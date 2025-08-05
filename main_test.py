from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from dotenv import load_dotenv
import json
import re
from ai_engine import extract_text, enhanced_crew
import os
import pandas as pd
import uuid
import tempfile
import logging
import datetime
import traceback
from typing import Dict, List, Any, Optional
import time
from config import Config
from supabase_manager import get_supabase_manager

def first_json_block(text: str) -> dict:
    """Return the first top-level JSON object found in text."""
    # Try to find the complete JSON object by counting braces
    start = text.find('{')
    if start == -1:
        raise ValueError("No JSON object found in LLM output")
    
    brace_count = 0
    end = start
    
    for i in range(start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break
    
    if brace_count != 0:
        raise ValueError("Incomplete JSON object found in LLM output")
    
    json_str = text[start:end]
    return json.loads(json_str)

# Flask app configuration
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory for uploaded files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB
app.secret_key = 'a_super_secret_key_12345'  # Use a secure random string
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Database Configuration
# Use Supabase by default, fallback to MySQL if specified
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'supabase')

if DATABASE_TYPE == 'mysql':
    from flask_mysqldb import MySQL
    import mysql.connector

    # MySQL Configuration
    app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
    app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
    app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
    app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    mysql = MySQL(app)
else:
    # Supabase configuration
    mysql = None

def insert_results_into_db(results):
    """Insert results into database (supports both MySQL and Supabase)"""
    try:
        if DATABASE_TYPE == 'mysql':
            # MySQL insertion
            cur = mysql.connection.cursor()
            
            # Handle both list of lists and flat list
            if isinstance(results[0], list):
                # List of lists format
                for resume_list in results:
                    for resume in resume_list:
                        cur.execute("""
                            INSERT INTO hr_resume_results (
                                candidate_name,
                                overall_score,
                                tag,
                                explanation,
                                feedback
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, (
                            resume.get('candidate_name'),
                            resume.get('overall_score'),
                            resume.get('qualification_tag'),
                            resume.get('explanation'),
                            resume.get('feedback')
                        ))
            else:
                # Flat list format
                for resume in results:
                    cur.execute("""
                        INSERT INTO hr_resume_results (
                            candidate_name,
                            overall_score,
                            tag,
                            explanation,
                            feedback
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (
                        resume.get('candidate_name'),
                        resume.get('overall_score'),
                        resume.get('qualification_tag'),
                        resume.get('explanation'),
                        resume.get('feedback')
                    ))
            mysql.connection.commit()
            cur.close()
            print("✅ All results inserted successfully into MySQL database.")
        else:
            # Supabase insertion
            supabase_manager = get_supabase_manager()
            
            # Convert results to Supabase format
            supabase_results = []
            
            # Handle both list of lists and flat list
            if isinstance(results[0], list):
                # List of lists format
                for resume_list in results:
                    for resume in resume_list:
                        supabase_result = {
                            'candidate_name': resume.get('candidate_name'),
                            'overall_score': resume.get('overall_score'),
                            'qualification_tag': resume.get('qualification_tag'),  # Use new key name
                            'explanation': resume.get('recommendations'),   # Use recommendations field
                            'feedback': "Strengths: " + ", ".join(resume.get('strengths', [])),
                            # 'interview_questions': resume.get('interview_questions', {}),  # Temporarily commented out
                            'evaluated_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
                        }
                        # Store filename in explanation for now (we'll enhance this later)
                        if resume.get('resume_filename'):
                            supabase_result['explanation'] = f"[RESUME_FILE:{resume.get('resume_filename')}] {resume.get('recommendations', '')}"
                        supabase_results.append(supabase_result)
            else:
                # Flat list format
                for resume in results:
                    supabase_result = {
                        'candidate_name': resume.get('candidate_name'),
                        'overall_score': resume.get('overall_score'),
                        'qualification_tag': resume.get('qualification_tag'),  # Use new key name
                        'explanation': resume.get('recommendations'),   # Use recommendations field
                        'feedback': "Strengths: " + ", ".join(resume.get('strengths', [])),
                        # 'interview_questions': resume.get('interview_questions', {}),  # Temporarily commented out
                        'evaluated_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                    # Store filename in explanation for now (we'll enhance this later)
                    if resume.get('resume_filename'):
                        supabase_result['explanation'] = f"[RESUME_FILE:{resume.get('resume_filename')}] {resume.get('recommendations', '')}"
                    supabase_results.append(supabase_result)
            
            # Insert into Supabase
            inserted_ids = supabase_manager.insert_multiple_results(supabase_results)
            print(f"✅ All results inserted successfully into Supabase database. {len(inserted_ids)} records inserted.")
            
    except Exception as e:
        print("❌ Error inserting results:")
        traceback.print_exc()


def save_file(file, upload_folder):
    """
    Save an uploaded file to the specified folder and return the file path.
    """
    try:
        if not file or file.filename == '':
            raise ValueError("File is missing.")
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        logging.info(f"File saved at: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        raise

def read_temp_file(file_path):
    """
    Read the content of a temporary file and return its contents.
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error reading temporary file: {e}")
        raise

@app.route('/', methods=['GET', 'POST'])
def home():
    """Enhanced home route with better error handling and processing"""
    error = None
    try:
        if request.method == 'POST':
            return process_evaluation_request()
            
    except ValueError as ve:
        error = str(ve)
        logging.warning(f"Validation error: {error}")
    except Exception as e:
        error = "An unexpected error occurred. Please try again."
        logging.error(f"Unexpected error: {e}", exc_info=True)

    # Render the new modern homepage
    return render_template('index.html', 
                         error=error, 
                         current_job_desc=session.get('job_description_file'),
                         current_file_name=session.get('file_name'))

def process_evaluation_request():
    """Process the evaluation request with enhanced error handling"""
    start_time = time.time()
    
    # ===== FLASK CONFIRMATION =====
    print("\n" + "="*80)
    print("🚀 FLASK APPLICATION CONFIRMED")
    print("="*80)
    print("✅ Using Flask web framework")
    print("✅ Flask app instance: main_test.py")
    print("✅ Request method: " + request.method)
    print("✅ Session active: " + str('user_id' in session))
    print("="*80)
    print()
    
    # Validate inputs
    retain_job_desc = 'retain_job_desc' in request.form

    # Process job description
    if not retain_job_desc or not os.path.exists(session.get('job_description_file', '')):
        job_desc_file = request.files.get('job_desc')
        if not job_desc_file or job_desc_file.filename == '':
            raise ValueError("Job description file is required.")

        job_desc_path = save_file(job_desc_file, app.config['UPLOAD_FOLDER'])
        session['job_description_file'] = job_desc_path
        session['file_name'] = job_desc_file.filename
        logging.info(f"New job description uploaded: {job_desc_file.filename}")
    else:
        logging.info("Reusing existing job description.")

    # Process resume files
    resume_files = request.files.getlist('resumes')
    if not resume_files or all(file.filename == '' for file in resume_files):
        raise ValueError("At least one resume file is required.")

    # Validate file formats
    supported_formats = ('.pdf', '.docx', '.txt')
    valid_files = [f for f in resume_files if f.filename.lower().endswith(supported_formats)]
    
    if not valid_files:
        raise ValueError("No supported file formats found. Please upload PDF, DOCX, or TXT files.")

    logging.info(f"Processing {len(valid_files)} resume files")

    # Clear previous results
    clear_previous_results()

    # Extract job description text
    job_description_path = session.get('job_description_file')
    job_description = extract_text(job_description_path)

    # ===== CONSOLE LOGGING FOR DEBUGGING =====
    print("\n" + "="*80)
    print("🔍 EXTRACTED JOB DESCRIPTION DATA:")
    print("="*80)
    print(f"📄 Job Description File: {job_description_path}")
    print(f"📊 Job Description Length: {len(job_description)} characters")
    print(f"📝 Job Description Preview (first 500 chars):")
    print("-" * 50)
    print(job_description[:500] + "..." if len(job_description) > 500 else job_description)
    print("-" * 50)
    print("="*80)
    print()

    # Process each resume
    all_results = []
    processing_errors = []

    for i, resume_file in enumerate(valid_files):
        try:
            logging.info(f"Processing resume {i+1}/{len(valid_files)}: {resume_file.filename}")
            
            # Save and extract resume text
            resume_path = save_file(resume_file, app.config['UPLOAD_FOLDER'])
            resume_text = extract_text(resume_path)
            candidate_name = os.path.splitext(resume_file.filename)[0]

            # ===== CONSOLE LOGGING FOR RESUME DATA =====
            print("\n" + "="*80)
            print(f"📋 RESUME {i+1}/{len(valid_files)}: {resume_file.filename}")
            print("="*80)
            print(f"👤 Candidate Name (from filename): {candidate_name}")
            print(f"📄 Resume File Path: {resume_path}")
            print(f"📊 Resume Text Length: {len(resume_text)} characters")
            print(f"📝 Resume Text Preview (first 500 chars):")
            print("-" * 50)
            print(resume_text[:500] + "..." if len(resume_text) > 500 else resume_text)
            print("-" * 50)
            
            # Check if candidate name appears in resume text
            if candidate_name.lower() in resume_text.lower():
                print(f"✅ Candidate name '{candidate_name}' found in resume text")
            else:
                print(f"⚠️  Candidate name '{candidate_name}' NOT found in resume text")
                print(f"🔍 Looking for name patterns in resume...")
                # Look for common name patterns
                import re
                name_patterns = [
                    r'^([A-Z][a-z]+ [A-Z][a-z]+)',  # First Last
                    r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)',  # First Middle Last
                    r'([A-Z][A-Z]+ [A-Z][a-z]+)',  # FIRST Last
                ]
                for pattern in name_patterns:
                    matches = re.findall(pattern, resume_text[:1000])  # Check first 1000 chars
                    if matches:
                        print(f"🔍 Found potential names: {matches}")
                        break
                else:
                    print("❌ No clear name patterns found in resume")
            
            print("="*80)
            print()

            # Run AI evaluation using OpenRouter only
            logging.info(f"Running OpenRouter evaluation for: {candidate_name}")
            
            result = enhanced_crew.kickoff(inputs={
                "resume": resume_text,
                "job_description": job_description,
            })

            # Get the final output from CrewAI and parse first JSON block
            if hasattr(result, 'raw'):
                raw_json = result.raw
            elif hasattr(result, 'output'):
                raw_json = result.output
            elif hasattr(result, 'result'):
                raw_json = result.result
            else:
                # Fallback: try to get the last task's output
                raw_json = str(result)
            
            evaluation_dict = first_json_block(raw_json)
            
            # Validate data flow consistency
            from ai_engine import validate_agent_data_flow
            validation_result = validate_agent_data_flow(
                resume_data={'candidate_name': candidate_name, 'resume_text': resume_text[:1000]},  # Sample data
                job_data={'job_description': job_description[:1000]},  # Sample data
                evaluation_data=evaluation_dict
            )
            
            if validation_result['overall_status'] == 'FAIL':
                logging.warning(f"Data flow validation failed for {candidate_name}: {validation_result}")
            
            # Check for placeholder names and retry if detected
            placeholder_names = {
                "john doe", "jane smith", "[candidate name]", "unknown", 
                "john smith", "jane doe", "candidate", "applicant", "test user",
                "sample candidate", "example candidate", "demo user"
            }
            
            if evaluation_dict["candidate_name"].lower() in placeholder_names:
                logging.warning(f"Placeholder name detected: {evaluation_dict['candidate_name']}. Retrying evaluation...")
                # Retry the evaluation with enhanced prompts
                retry_result = enhanced_crew.kickoff(inputs={
                    "resume": resume_text,
                    "job_description": job_description,
                })
                
                # Parse retry result
                if hasattr(retry_result, 'raw'):
                    retry_raw_json = retry_result.raw
                elif hasattr(retry_result, 'output'):
                    retry_raw_json = retry_result.output
                elif hasattr(retry_result, 'result'):
                    retry_raw_json = retry_result.result
                else:
                    retry_raw_json = str(retry_result)
                
                retry_evaluation_dict = first_json_block(retry_raw_json)
                
                # Check if retry also has placeholder
                if retry_evaluation_dict["candidate_name"].lower() in placeholder_names:
                    logging.error(f"Placeholder name still detected after retry: {retry_evaluation_dict['candidate_name']}")
                    # Use filename as fallback
                    fallback_name = os.path.splitext(resume_file.filename)[0].replace('_', ' ').replace('-', ' ')
                    retry_evaluation_dict["candidate_name"] = fallback_name
                    logging.info(f"Using filename as candidate name: {fallback_name}")
                
                evaluation_dict = retry_evaluation_dict
            
            # ===== LOGGING FINAL OUTPUT =====
            print("\n" + "="*80)
            print("🔍 FINAL AI OUTPUT:")
            print("="*80)
            print(f"📄 Raw Output Length: {len(str(raw_json))}")
            print(f"📄 First 500 chars: {str(raw_json)[:500]}...")
            print("="*80)
            print()
            
            parsed_result = evaluation_dict  # rename for clarity
            parsed_result["resume_filename"] = resume_file.filename
            
            # ===== CONSOLE LOGGING FOR AI EVALUATION RESULTS =====
            print("\n" + "="*80)
            print(f"🤖 AI EVALUATION RESULTS FOR: {candidate_name}")
            print("="*80)
            print(f"👤 Candidate Name: {parsed_result.get('candidate_name', 'N/A')}")
            print(f"📊 Overall Score: {parsed_result.get('overall_score', 'N/A')}")
            print(f"🏷️  Qualification Tag: {parsed_result.get('qualification_tag', 'N/A')}")
            print(f"📄 Resume Filename: {parsed_result.get('resume_filename', 'N/A')}")
            print(f"💪 Strengths: {', '.join(parsed_result.get('strengths', []))}")
            print(f"⚠️  Areas of Concern: {', '.join(parsed_result.get('areas_of_concern', []))}")
            print(f"📝 Recommendations Preview (first 300 chars):")
            print("-" * 50)
            recommendations = parsed_result.get('recommendations', 'No recommendations available')
            print(recommendations[:300] + "..." if len(recommendations) > 300 else recommendations)
            print("-" * 50)
            print("="*80)
            print()
                
            logging.info(f"OpenRouter evaluation successful: {parsed_result['candidate_name']} (Score: {parsed_result['overall_score']})")
            
            # Monitor data flow
            flow_data = monitor_data_flow(resume_file, job_description_path, parsed_result, time.time() - start_time)
            
            all_results.append(parsed_result)

        except Exception as e:
            error_msg = f"OpenRouter evaluation failed for {resume_file.filename}: {str(e)}"
            logging.error(error_msg)
            
            # Check if it's a credit/authentication error and try with different key
            if "credits" in str(e).lower() or "authentication" in str(e).lower() or "402" in str(e):
                logging.info(f"Attempting to retry with different API key for {resume_file.filename}")
                try:
                    # Import the key manager from ai_engine
                    from ai_engine import key_manager
                    
                    # Mark current key as failed and get a new one
                    current_key = key_manager.get_current_key()
                    key_manager.mark_key_failed(current_key)
                    
                    # Retry with new key
                    logging.info(f"Retrying with key {key_manager.get_available_key_count()} available keys")
                    result = enhanced_crew.kickoff()
                    
                    # Parse the result again
                    if hasattr(result, 'raw'):
                        raw_json = result.raw
                    elif hasattr(result, 'output'):
                        raw_json = result.output
                    elif hasattr(result, 'result'):
                        raw_json = result.result
                    else:
                        raw_json = str(result)
                    
                    evaluation_dict = first_json_block(raw_json)
                    
                    # Safety check for placeholder names
                    placeholder_names = {
                        "john doe", "jane smith", "[candidate name]", "unknown", 
                        "john smith", "jane doe", "candidate", "applicant", "test user",
                        "sample candidate", "example candidate", "demo user"
                    }
                    
                    if evaluation_dict["candidate_name"].lower() in placeholder_names:
                        logging.warning(f"Placeholder name detected in retry: {evaluation_dict['candidate_name']}")
                        # Use filename as fallback
                        fallback_name = os.path.splitext(resume_file.filename)[0].replace('_', ' ').replace('-', ' ')
                        evaluation_dict["candidate_name"] = fallback_name
                        logging.info(f"Using filename as candidate name: {fallback_name}")
                    
                    parsed_result = {
                        'candidate_name': evaluation_dict['candidate_name'],
                        'overall_score': evaluation_dict['overall_score'],
                        'qualification_tag': evaluation_dict['qualification_tag'],
                        'category_scores': evaluation_dict.get('category_scores', {}),
                        'strengths': evaluation_dict.get('strengths', []),
                        'areas_of_concern': evaluation_dict.get('areas_of_concern', []),
                        'recommendations': evaluation_dict.get('recommendations', ''),
                        'interview_questions': evaluation_dict.get('interview_questions', {}),
                        'resume_filename': resume_file.filename
                    }
                    
                    logging.info(f"Retry successful: {parsed_result['candidate_name']} (Score: {parsed_result['overall_score']})")
                    all_results.append(parsed_result)
                    continue  # Skip the error handling below
                    
                except Exception as retry_error:
                    logging.error(f"Retry also failed for {resume_file.filename}: {str(retry_error)}")
                    processing_errors.append(f"Failed after retry: {resume_file.filename} - {str(retry_error)}")
                    flash(f"Evaluation failed for {resume_file.filename} even after retry. Please try again later.", "error")
            else:
                processing_errors.append(error_msg)
                flash(f"Evaluation failed for {resume_file.filename}. Please try again.", "error")

    # Insert results into database
    if all_results:
        insert_results_into_db(all_results)
    
    # ===== FINAL SUMMARY =====
    print("\n" + "="*80)
    print("📊 EVALUATION SUMMARY")
    print("="*80)
    print(f"✅ Successfully processed: {len(all_results)} resumes")
    print(f"❌ Failed evaluations: {len(processing_errors)}")
    print(f"⏱️  Total processing time: {time.time() - start_time:.2f} seconds")
    
    if all_results:
        print(f"📈 Average score: {sum(r.get('overall_score', 0) for r in all_results) / len(all_results):.1f}")
        print(f"🏷️  Qualification breakdown:")
        tags = {}
        for result in all_results:
            tag = result.get('qualification_tag', 'Unknown')
            tags[tag] = tags.get(tag, 0) + 1
        for tag, count in tags.items():
            print(f"   - {tag}: {count}")
    
    if processing_errors:
        print(f"\n❌ Processing Errors:")
        for error in processing_errors:
            print(f"   - {error}")
    
    print("="*80)
    print()
        
    processing_time = time.time() - start_time
    logging.info(f"Evaluation completed in {processing_time:.2f} seconds")
    
    if processing_errors:
        session['processing_errors'] = processing_errors

    return redirect(url_for('results'))

def clear_previous_results():
    """Clear previous evaluation results"""
    try:
        if DATABASE_TYPE == 'mysql':
            cur = mysql.connection.cursor()
            cur.execute("TRUNCATE TABLE hr_resume_results")
            mysql.connection.commit()
            cur.close()
            logging.info("Cleared previous results from MySQL database")
        else:
            supabase_manager = get_supabase_manager()
            supabase_manager.clear_all_results()
            logging.info("Cleared previous results from Supabase database")
    except Exception as e:
        logging.error(f"Error clearing previous results: {e}")
        raise

@app.route('/results')
def results():
    """Enhanced results page with error handling and processing info"""
    try:
        if DATABASE_TYPE == 'mysql':
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT candidate_name, overall_score, tag, explanation, feedback 
                FROM hr_resume_results 
                ORDER BY overall_score DESC
            """)
            results_data = cur.fetchall()
            cur.close()
        else:
            # Supabase query
            supabase_manager = get_supabase_manager()
            supabase_results = supabase_manager.get_all_results()
            
            # Convert to expected format
            results_data = []
            for result in supabase_results:
                results_data.append({
                    'candidate_name': result.get('candidate_name'),
                    'overall_score': result.get('overall_score'),
                    'tag': result.get('qualification_tag'),  # Map back to 'tag'
                    'explanation': result.get('explanation'),
                    'feedback': result.get('feedback'),
                    'interview_questions': result.get('interview_questions', {})  # Include interview questions
                })

        # Get processing errors from session if any
        processing_errors = session.pop('processing_errors', [])
        
        # Add some statistics
        stats = calculate_results_statistics(results_data)
        
        logging.info(f"Displaying {len(results_data)} evaluation results")

        return render_template('results.html', 
                             results=results_data,
                             stats=stats,
                             processing_errors=processing_errors)
                             
    except Exception as e:
        logging.error(f"Error fetching results: {e}")
        return render_template('results.html', 
                             results=[], 
                             stats={},
                             error="Failed to load results.")

def calculate_results_statistics(results_data):
    """Calculate statistics for the results dashboard"""
    if not results_data:
        return {}
    
    total_candidates = len(results_data)
    qualified = len([r for r in results_data if r['tag'] == 'QUALIFIED'])
    not_qualified = len([r for r in results_data if r['tag'] == 'NOT QUALIFIED'])
    overqualified = len([r for r in results_data if r['tag'] == 'OVERQUALIFIED'])
    
    scores = [r['overall_score'] for r in results_data if isinstance(r['overall_score'], (int, float))]
    
    return {
        'total_candidates': total_candidates,
        'qualified': qualified,
        'not_qualified': not_qualified,
        'overqualified': overqualified,
        'average_score': sum(scores) / len(scores) if scores else 0,
        'highest_score': max(scores) if scores else 0,
        'lowest_score': min(scores) if scores else 0
    }

@app.route('/view_resume/<filename>')
def view_resume(filename):
    """Serve uploaded resume files for viewing"""
    try:
        # Security check - ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return "Invalid filename", 400
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return "File not found", 404
        
        # Determine file type and serve appropriately
        if filename.lower().endswith('.pdf'):
            return send_file(file_path, mimetype='application/pdf')
        elif filename.lower().endswith(('.doc', '.docx')):
            return send_file(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        else:
            return send_file(file_path)
            
    except Exception as e:
        logging.error(f"Error serving resume file: {e}")
        return "Error serving file", 500

@app.route('/api/export/<format>')
def export_results(format):
    """API endpoint for exporting results in different formats"""
    try:
        if DATABASE_TYPE == 'mysql':
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT candidate_name, overall_score, tag, explanation, feedback 
                FROM hr_resume_results 
                ORDER BY overall_score DESC
            """)
            results_data = cur.fetchall()
            cur.close()
        else:
            # Supabase query
            supabase_manager = get_supabase_manager()
            supabase_results = supabase_manager.get_all_results()
            
            # Convert to expected format
            results_data = []
            for result in supabase_results:
                results_data.append({
                    'candidate_name': result.get('candidate_name'),
                    'overall_score': result.get('overall_score'),
                    'tag': result.get('qualification_tag'),  # Map back to 'tag'
                    'explanation': result.get('explanation'),
                    'feedback': result.get('feedback'),
                    'interview_questions': result.get('interview_questions', {})  # Include interview questions
                })

        if format.lower() == 'json':
            return jsonify(results_data)
        elif format.lower() == 'csv':
            # Convert to CSV format
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['candidate_name', 'overall_score', 'tag', 'explanation', 'feedback'])
            writer.writeheader()
            writer.writerows(results_data)
            
            response = app.response_class(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=resume_evaluation_results.csv'}
            )
            return response
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logging.error(f"Error exporting results: {e}")
        return jsonify({'error': 'Export failed'}), 500

def monitor_data_flow(resume_file, job_description_path, evaluation_result, processing_time):
    """
    Monitor and log the complete data flow for debugging and optimization
    """
    flow_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'resume_file': resume_file.filename if resume_file else 'N/A',
        'job_description_path': job_description_path,
        'processing_time_seconds': processing_time,
        'evaluation_summary': {
            'candidate_name': evaluation_result.get('candidate_name'),
            'overall_score': evaluation_result.get('overall_score'),
            'qualification_tag': evaluation_result.get('qualification_tag'),
            'has_interview_questions': bool(evaluation_result.get('interview_questions')),
            'has_category_scores': bool(evaluation_result.get('category_scores'))
        },
        'data_quality': {
            'name_extracted': bool(evaluation_result.get('candidate_name') and evaluation_result['candidate_name'] != 'Unknown'),
            'score_valid': isinstance(evaluation_result.get('overall_score'), (int, float)) and 0 <= evaluation_result.get('overall_score', 0) <= 100,
            'tag_valid': evaluation_result.get('qualification_tag') in ['QUALIFIED', 'NOT QUALIFIED', 'OVERQUALIFIED'],
            'recommendations_present': bool(evaluation_result.get('recommendations')),
            'strengths_present': bool(evaluation_result.get('strengths'))
        }
    }
    
    # Log flow data
    logging.info(f"Data flow monitoring: {json.dumps(flow_data, indent=2)}")
    
    # Store in session for debugging
    if 'data_flow_log' not in session:
        session['data_flow_log'] = []
    session['data_flow_log'].append(flow_data)
    
    return flow_data

if __name__ == "__main__":
    # Start the Flask application
    app.run(host='0.0.0.0', debug=True, port=8000)