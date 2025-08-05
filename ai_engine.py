import sys
import fitz
import re
import json
import argparse
from docx import Document
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import datetime
from IPython.display import Markdown, display
import uuid
import requests
from typing import Dict, List, Any, Optional
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class OpenRouterKeyManager:
    """Manages multiple OpenRouter API keys with rotation and fallback"""
    
    def __init__(self):
        self.keys = []
        self.current_key_index = 0
        self.failed_keys = set()
        
        # Load all available keys
        for i in range(1, 6):
            key = os.getenv(f'OPENROUTER_API_KEY_{i}')
            if key:
                self.keys.append(key)
        
        if not self.keys:
            # Fallback to single key
            fallback_key = os.getenv('OPENROUTER_API_KEY')
            if fallback_key:
                self.keys.append(fallback_key)
                logger.warning("Using fallback single API key")
            else:
                raise ValueError("No OpenRouter API keys found! Please set OPENROUTER_API_KEY_1 through OPENROUTER_API_KEY_5 in your .env file")
        
        logger.info(f"Loaded {len(self.keys)} OpenRouter API keys")
    
    def get_current_key(self) -> str:
        """Get the current API key"""
        return self.keys[self.current_key_index]
    
    def get_random_key(self) -> str:
        """Get a random API key (excluding failed ones)"""
        available_keys = [key for i, key in enumerate(self.keys) if i not in self.failed_keys]
        if not available_keys:
            # Reset failed keys if all are exhausted
            self.failed_keys.clear()
            available_keys = self.keys
            logger.warning("All keys were marked as failed, resetting failed keys list")
        
        return random.choice(available_keys)
    
    def mark_key_failed(self, key: str):
        """Mark a key as failed"""
        try:
            index = self.keys.index(key)
            self.failed_keys.add(index)
            logger.warning(f"Marked key {index + 1} as failed")
        except ValueError:
            pass
    
    def rotate_key(self):
        """Move to the next key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        logger.info(f"Rotated to key {self.current_key_index + 1}")
    
    def get_available_key_count(self) -> int:
        """Get number of available (non-failed) keys"""
        return len(self.keys) - len(self.failed_keys)

# Initialize key manager
key_manager = OpenRouterKeyManager()

# OpenRouter configuration with reliable model
model_name = 'openai/gpt-3.5-turbo'  # Use GPT-3.5 Turbo (reliable and cost-effective)
base_url = "https://openrouter.ai/api/v1"

logger.info(f"Initializing OpenRouter with GPT-3.5 Turbo and {key_manager.get_available_key_count()} available keys")

def get_llm_with_fallback() -> ChatOpenAI:
    """Get LLM instance with automatic key rotation and fallback"""
    api_key = key_manager.get_random_key()
    
    # Set environment variables for compatibility
    os.environ['OPENAI_API_KEY'] = api_key
    os.environ['OPENAI_API_BASE'] = base_url
    
    return ChatOpenAI(
        model=model_name,
        temperature=0.1,
        api_key=api_key,
        base_url=base_url,
        max_tokens=1000,  # Further reduced for memory efficiency
        request_timeout=120,  # Add timeout
        model_kwargs={
            "response_format": {"type": "json_object"},
            "extra_headers": {
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Resume Evaluator"
            }
        }
    )

# Initialize the default LLM
llm = get_llm_with_fallback()

logger.info(f"Successfully initialized OpenRouter LLM: {model_name} with reduced token limit")

class ResumeEvaluationEngine:
    """Advanced Resume Evaluation Engine with industry-standard scoring"""
    
    def __init__(self):
        self.evaluation_criteria = {
            'experience_weight': 0.35,
            'skills_weight': 0.25,
            'education_weight': 0.15,
            'achievements_weight': 0.15,
            'cultural_fit_weight': 0.10
        }
        
        self.skill_categories = {
            'technical_skills': ['programming', 'software', 'technology', 'technical', 'coding', 'development'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'management', 'collaboration'],
            'domain_skills': ['business', 'finance', 'marketing', 'sales', 'operations', 'strategy']
        }

    def calculate_experience_score(self, candidate_exp: str, required_exp: str) -> tuple[int, str]:
        """Calculate experience score with detailed reasoning"""
        try:
            # Extract years from strings
            candidate_years = self._extract_years(candidate_exp)
            required_years = self._extract_years(required_exp)
            
            if candidate_years is None or required_years is None:
                return 50, "Unable to determine experience requirements clearly"
            
            # Handle range requirements (e.g., "3-5 years")
            if isinstance(required_years, tuple):
                min_req, max_req = required_years
                if candidate_years < min_req:
                    score = max(20, 60 - (min_req - candidate_years) * 10)
                    reason = f"Candidate has {candidate_years} years, but minimum {min_req} years required"
                elif min_req <= candidate_years <= max_req:
                    score = 90
                    reason = f"Perfect experience match: {candidate_years} years within required range"
                else:
                    # Overqualified check
                    if candidate_years > max_req + 5:
                        score = 75
                        reason = f"Overqualified: {candidate_years} years significantly exceeds requirement"
                    else:
                        score = 95
                        reason = f"Excellent experience: {candidate_years} years exceeds requirement appropriately"
            else:
                # Single number requirement
                if candidate_years < required_years:
                    score = max(25, 70 - (required_years - candidate_years) * 8)
                    reason = f"Below requirement: {candidate_years} vs {required_years} years needed"
                elif candidate_years == required_years:
                    score = 90
                    reason = f"Exact match: {candidate_years} years experience"
                else:
                    # Check for overqualification
                    if candidate_years > required_years + 8:
                        score = 80
                        reason = f"Significantly overqualified: {candidate_years} vs {required_years} years"
                    else:
                        score = 95
                        reason = f"Above requirement: {candidate_years} years exceeds {required_years} years needed"
                        
            return score, reason
            
        except Exception as e:
            logger.error(f"Error calculating experience score: {e}")
            return 50, "Error in experience evaluation"

    def _extract_years(self, text: str) -> Optional[int | tuple[int, int]]:
        """Extract years of experience from text"""
        if not text:
            return None
            
        text = text.lower().strip()
        
        # Pattern for range (e.g., "3-5 years", "2 to 4 years")
        range_pattern = r'(\d+)[\s\-to]+(\d+)\s*(?:years?|yrs?)'
        range_match = re.search(range_pattern, text)
        if range_match:
            return (int(range_match.group(1)), int(range_match.group(2)))
        
        # Pattern for single number (e.g., "5 years", "3+ years")
        single_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
        single_match = re.search(single_pattern, text)
        if single_match:
            return int(single_match.group(1))
        
        # Pattern for "fresh graduate" or "entry level"
        if any(term in text for term in ['fresh', 'graduate', 'entry', 'junior', 'new']):
            return 0
            
        return None

    def analyze_skill_match(self, candidate_skills: List[str], required_skills: List[str]) -> tuple[int, str]:
        """Analyze skill matching with weighted scoring"""
        if not candidate_skills or not required_skills:
            return 40, "Insufficient skill information provided"
        
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        # Exact matches
        exact_matches = []
        for req_skill in required_skills_lower:
            for cand_skill in candidate_skills_lower:
                if req_skill in cand_skill or cand_skill in req_skill:
                    exact_matches.append(req_skill)
                    break
        
        # Partial matches (semantic similarity)
        partial_matches = []
        for req_skill in required_skills_lower:
            if req_skill not in exact_matches:
                for cand_skill in candidate_skills_lower:
                    # Simple semantic matching
                    if self._calculate_similarity(req_skill, cand_skill) > 0.7:
                        partial_matches.append(req_skill)
                        break
        
        total_required = len(required_skills_lower)
        exact_score = len(exact_matches) / total_required * 80
        partial_score = len(partial_matches) / total_required * 40
        
        final_score = min(100, exact_score + partial_score)
        
        match_ratio = (len(exact_matches) + len(partial_matches)) / total_required
        
        if match_ratio >= 0.8:
            reason = f"Excellent skill match: {len(exact_matches)} exact + {len(partial_matches)} partial matches"
        elif match_ratio >= 0.6:
            reason = f"Good skill match: {len(exact_matches)} exact + {len(partial_matches)} partial matches"
        elif match_ratio >= 0.4:
            reason = f"Moderate skill match: {len(exact_matches)} exact + {len(partial_matches)} partial matches"
        else:
            reason = f"Limited skill match: {len(exact_matches)} exact + {len(partial_matches)} partial matches"
            
        return int(final_score), reason

    def _calculate_similarity(self, skill1: str, skill2: str) -> float:
        """Simple similarity calculation"""
        words1 = set(skill1.split())
        words2 = set(skill2.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

# Enhanced AI Agents with improved prompts
resume_analyzer = Agent(
    role="Senior Resume Analyst",
    goal="Extract comprehensive information from resumes with high accuracy and attention to detail.",
    backstory=(
        "You are a senior HR analyst with 15+ years of experience in talent acquisition. "
        "You excel at extracting and structuring information from resumes, identifying key qualifications, "
        "and understanding the nuances of different industries and roles. Your analysis is thorough, "
        "accurate, and provides valuable insights for hiring decisions."
    ),
    llm=get_llm_with_fallback(),
    allow_delegation=False,
    verbose=True
)

job_description_analyzer = Agent(
    role="Job Requirements Specialist",
    goal="Analyze job descriptions to extract precise requirements and evaluation criteria.",
    backstory=(
        "You are a job analysis expert who specializes in breaking down job descriptions into "
        "specific, measurable requirements. You understand the difference between must-have and nice-to-have "
        "qualifications, and can identify implicit requirements that may not be explicitly stated."
    ),
    llm=get_llm_with_fallback(),
    allow_delegation=False,
    verbose=True
)

advanced_evaluator = Agent(
    role="Senior Talent Evaluation Specialist",
    goal="Provide comprehensive, fair, and industry-standard resume evaluations with detailed scoring.",
    backstory=(
        "You are a senior talent evaluation specialist with expertise in multiple industries. "
        "You use data-driven approaches to assess candidates fairly and consistently. Your evaluations "
        "are trusted by Fortune 500 companies for their accuracy and insight. You consider not just "
        "technical qualifications but also career progression, achievements, and potential cultural fit."
    ),
    llm=get_llm_with_fallback(),
    allow_delegation=False,
    verbose=True
)

interview_strategist = Agent(
    role="Interview Strategy Expert",
    goal="Design targeted interview questions that effectively assess candidate suitability.",
    backstory=(
        "You are an interview design expert who creates questions that reveal true candidate capabilities. "
        "Your questions are behavioral, situational, and technical, designed to predict job performance. "
        "You understand how to assess both hard and soft skills through strategic questioning."
    ),
    llm=get_llm_with_fallback(),
    allow_delegation=False,
    verbose=True
)

quality_assurance_agent = Agent(
    role="Quality Assurance Specialist",
    goal="Ensure evaluation consistency, accuracy, and compliance with best practices.",
    backstory=(
        "You are a quality assurance specialist who ensures all evaluations meet high standards. "
        "You check for bias, consistency, and completeness in assessments. Your role is critical "
        "in maintaining the integrity and reliability of the evaluation process."
    ),
    llm=get_llm_with_fallback(),
    allow_delegation=False,
    verbose=True
)

# Enhanced Tasks
resume_analysis_task = Task(
    description="""
You are extracting **facts only** from a resume. Do not infer, expand, or invent. If a field is not present, return the closest faithful value or null per schema.

INPUT RESUME (raw text):
{resume}

OUTPUT FORMAT — return **only** valid JSON matching this exact schema (no extra fields, no markdown):

{
  "candidate_name": "string",           // Real name from resume header/contact block. If absent, "Unknown".
  "email": "string | null",             // Must match a valid email regex if present.
  "phone": "string | null",             // Include country code if shown; keep punctuation as in resume.
  "years_experience": int,              // Conservative count. If ambiguous, estimate low; never inflate.
  "skills": {
    "technical": [string],              // Only skills explicitly present in resume (e.g., Python, React).
    "soft": [string],                   // e.g., Leadership, Communication (only if explicitly stated).
    "domain": [string]                  // e.g., FinTech, e-commerce (only if explicitly stated).
  },
  "education": [
    { "degree": "string", "institution": "string", "grad_year": "string|null" }
  ],
  "work_history": [
    { "company": "string", "title": "string", "start": "string", "end": "string|null" }
  ],
  "certifications": [string]
}

HARD RULES:
- **Candidate name** must be the real one from the resume header/contact block. Never use placeholders like "John Doe", "Jane Smith", "[Candidate Name]".
- If multiple names appear (e.g., author vs. candidate), choose the **contact header** name.
- **No hallucinations.** If a datum isn't visible in the resume text, do not add it.
- Do not normalize text (keep original capitalization/spelling), except trimming whitespace.
- When dates are ranges (e.g., "Jan 2024 – Jun 2024"), copy exact strings.
- If an item is unclear, prefer null/empty arrays over guesses.

QUALITY CHECKS (perform internally before returning JSON):
- Email/phone formats are syntactically valid when present.
- Arrays exist even if empty (e.g., skills.soft: []).
- years_experience is an integer (approximate conservatively if necessary).

Return **JSON only**. No prose, no markdown, no comments.
""",
    expected_output="Strict, faithful JSON that matches the schema exactly. No invented data. Name is real or 'Unknown'.",
    agent=resume_analyzer
)

job_analysis_task = Task(
    description="""
You analyze a job description and structure requirements with rigor. Do not add anything not stated or clearly implied by the JD. If the JD is silent, leave fields empty or concise "N/A".

RAW JOB DESCRIPTION:
{job_description}

OUTPUT — **JSON only**, following exactly:

{
  "Role Information": {
    "Job Title": "string",
    "Level": "entry|mid|senior|executive|unspecified",
    "Department": "string|unspecified",
    "Reporting Structure": "string|unspecified",
    "Employment Type": "full-time|part-time|contract|internship|unspecified",
    "Locations": [ "string" ]
  },
  "Experience Requirements": {
    "Years of Experience": { "Minimum": "string|number|unspecified", "Preferred": "string|number|unspecified" },
    "Specific Industry Experience": [ "string" ],
    "Previous Role Requirements": [ "string" ]
  },
  "Skills and Competencies": {
    "Must-have Technical Skills": [ "string" ],
    "Nice-to-have Technical Skills": [ "string" ],
    "Required Soft Skills": [ "string" ],
    "Leadership/Management Requirements": [ "string" ]
  },
  "Education and Certifications": {
    "Degree Requirements": [ "string" ],
    "Preferred Certifications": [ "string" ],
    "Professional Licenses Needed": [ "string" ]
  },
  "Key Responsibilities": {
    "Primary Duties and Accountabilities": [ "string" ],
    "Success Metrics and KPIs": [ "string" ],
    "Team Size or Budget Responsibility": "string|unspecified"
  },
  "Company and Culture": {
    "Company Size": "string|unspecified",
    "Industry": "string|unspecified",
    "Work Environment and Culture": [ "string" ],
    "Growth Opportunities": [ "string" ]
  },
  "Requirement Priority": {
    "Critical": [ "string" ],
    "Important": [ "string" ],
    "Preferred": [ "string" ]
  }
}

PRIORITIZATION RULES:
- **Critical** = hard requirements to be eligible (e.g., sponsorship restrictions, degree required, baseline language).
- **Important** = strongly weighted for selection but not strictly disqualifying.
- **Preferred** = nice-to-have.

HARD RULES:
- Do **not** infer unstated years of experience; if a program targets new grads, set Minimum appropriately or "unspecified".
- Do **not** convert ranges; keep the JD's wording where helpful (e.g., "0–2 years").
- Preserve precise constraints (e.g., "US work authorization required", "no sponsorship").

Return **JSON only**.
""",
    expected_output="A faithful, prioritized JSON breakdown of the JD with Critical/Important/Preferred clarity.",
    agent=job_description_analyzer
)

comprehensive_evaluation_task = Task(
    description=f"""
You compute a hiring fit using only the structured outputs from the resume and job analysis. Be conservative and fair. Do not penalize protected attributes or add unstated requirements.

INPUTS:
- resume_analysis_task.output
- job_analysis_task.output

OUTPUT — **JSON only** with this exact shape:

{{
  "candidate_name": "ACTUAL_NAME_FROM_RESUME",
  "overall_score": 0-100,
  "qualification_tag": "QUALIFIED | NOT QUALIFIED | OVERQUALIFIED",
  "category_scores": {{
      "experience": int,
      "skills": int,
      "education": int,
      "achievements": int,
      "culture": int
  }},
  "strengths": [ "string" ],
  "areas_of_concern": [ "string" ],
  "recommendations": "string",
  "interview_questions": {{
      "technical_questions": [ "string" ],
      "behavioral_questions": [ "string" ],
      "situational_questions": [ "string" ],
      "cultural_fit_questions": [ "string" ],
      "gap_assessment_questions": [ "string" ],
      "interview_duration": "string",
      "panel_composition": "string",
      "evaluation_criteria": "string"
  }}
}}

SCORING & RULES (apply consistently):
- **Use only** facts from the structured resume/JD outputs. No outside knowledge or guessing.
- **Experience score**: align years/scope with JD. Do not under/over-credit internships vs. FT unless JD distinguishes.
- **Skills score**: match against JD's Critical/Important/Preferred; exact > related > missing.
- **Education score**: credit degree/major alignment per JD; do not penalize if JD lists degree as "preferred".
- **Achievements score**: outcomes/impact (metrics, scale, complexity).
- **Culture score**: collaboration, ownership, learning mindset **only if evidenced**; never infer personality/socio-demographics.
- **qualification_tag**: 
  - QUALIFIED if Critical requirements satisfied and overall_score ≥ 70.
  - NOT QUALIFIED if any Critical unmet or overall_score < 60.
  - OVERQUALIFIED if evidence substantially exceeds level/scope in JD and risk of role mismatch is high.
- If the resume name is "Unknown", set candidate_name to "Unknown" (do not invent).

BIAS & COMPLIANCE GUARDS:
- Do not reference age, gender, ethnicity, disability, parental status, religion, or unrelated personal details.
- Ignore school prestige unless the JD explicitly requires it.

INTERVIEW CONTENT:
- Questions must stem from gaps/risks and the JD's Critical/Important skills.
- No trivia; favor problem-solving, system/approach, debugging, tradeoffs, and STAR prompts.
- Provide concise, neutral language.

Return **JSON only**. No markdown or prose.
""",
    expected_output="Validated, bias-aware evaluation JSON with consistent category scores and actionable interview questions.",
    context=[resume_analysis_task, job_analysis_task],
    agent=advanced_evaluator,
)

interview_design_task = Task(
    description="""
Design a targeted interview plan derived from the evaluation results. Do not restate the resume; build questions that validate skills, experience scope, and risk areas. No trivia.

INPUT:
- comprehensive_evaluation_task.output

OUTPUT — **JSON only**:

{
  "strategy": "string",                      // 2–4 sentence strategy overview
  "technical_questions": [ "string" ],       // 6–8 items
  "behavioral_questions": [ "string" ],      // 4–6 items (STAR-ready)
  "situational_questions": [ "string" ],     // 3–5 items
  "cultural_fit_questions": [ "string" ],    // 3–4 items (work style, collaboration, ownership)
  "gap_assessment_questions": [ "string" ],  // 3–5 items directly probing 'areas_of_concern'
  "interview_duration": "string",            // e.g., "75 minutes total: 40 tech, 20 behavioral, 15 wrap-up"
  "panel_composition": "string",             // e.g., "Hiring manager, senior engineer, peer engineer"
  "evaluation_criteria": "string"            // crisp rubric: signals for Strong/Yes/Leaning/No
}

HARD RULES:
- All questions must be derived from the JD priorities and evaluation gaps.
- No generic "tell me about yourself".
- Prefer scenario/system/tradeoff questions with clear success signals.
- No prose outside JSON.
""",
    expected_output="A JSON-only interview plan with focused, role-relevant questions and an explicit rubric.",
    agent=interview_strategist,
    context=[comprehensive_evaluation_task]
)

quality_review_task = Task(
    description="""
Perform a final QA across all prior outputs. Ensure the candidate's actual name is used consistently (no placeholders). Validate schema, scores, tags, and bias compliance. If something is missing or non-compliant, fix it **within** the final JSON only — do not write commentary.

INPUTS:
- resume_analysis_task.output
- job_analysis_task.output
- comprehensive_evaluation_task.output
- interview_design_task.output

FINAL OUTPUT — **JSON only** in this exact structure:

{
  "candidate_name": "ACTUAL_NAME",
  "overall_score": 0-100,
  "qualification_tag": "QUALIFIED | NOT QUALIFIED | OVERQUALIFIED",
  "category_scores": {
    "experience": int, "skills": int, "education": int, "achievements": int, "culture": int
  },
  "strengths": [ "string" ],
  "areas_of_concern": [ "string" ],
  "recommendations": "string",
  "interview_questions": {
    "technical_questions": [ "string" ],
    "behavioral_questions": [ "string" ],
    "situational_questions": [ "string" ],
    "cultural_fit_questions": [ "string" ],
    "gap_assessment_questions": [ "string" ],
    "interview_duration": "string",
    "panel_composition": "string",
    "evaluation_criteria": "string"
  }
}

MANDATORY CHECKS (fix quietly inside the JSON if needed):
- **Schema exactness**: no extra fields; required fields present; correct types.
- **Name**: use the real candidate name from resume extraction (or "Unknown"). No placeholders.
- **Tag logic**: consistent with scores and Critical JD requirements.
- **Bias-safe**: remove any language about protected attributes or non-job-related information.
- **Actionability**: recommendations are concrete and aligned to gaps/JD priorities.
- **Interview content**: questions are role-specific and probe risks/requirements.

Return **JSON only**. No prose, no markdown.
""",
    expected_output="A fully QA'd, schema-accurate, bias-safe evaluation JSON ready for storage and display.",
    agent=quality_assurance_agent,
    context=[resume_analysis_task, job_analysis_task, comprehensive_evaluation_task, interview_design_task]
)

def extract_text(fname: str) -> str:
    """Enhanced text extraction with better error handling"""
    try:
        file_extension = fname.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            doc = fitz.open(fname)
            text = ""
            for page in doc:
                text += str(page.get_text())
            doc.close()
            return " ".join(text.split('\n'))
            
        elif file_extension == 'txt':
            with open(fname, 'r', encoding='utf-8') as file:
                return file.read()
                
        elif file_extension == 'docx':
            doc = Document(fname)
            text = []
            for para in doc.paragraphs:
                text.append(para.text)
            return ' '.join(text)
            
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
            
    except Exception as e:
        logger.error(f"Error extracting text from {fname}: {e}")
        raise

# Old parsing functions removed - using clean JSON output from tasks

def validate_agent_data_flow(resume_data: dict, job_data: dict, evaluation_data: dict) -> dict:
    """
    Validate data consistency across agent outputs
    """
    validation_results = {
        'resume_validation': {},
        'job_validation': {},
        'evaluation_validation': {},
        'cross_validation': {},
        'overall_status': 'PASS'
    }
    
    # Resume data validation
    if resume_data:
        validation_results['resume_validation'] = {
            'has_name': bool(resume_data.get('candidate_name') and resume_data['candidate_name'] != 'Unknown'),
            'has_experience': 'years_experience' in resume_data,
            'has_skills': bool(resume_data.get('skills', {}).get('technical') or resume_data.get('skills', {}).get('soft')),
            'has_education': bool(resume_data.get('education')),
            'has_work_history': bool(resume_data.get('work_history'))
        }
    
    # Job data validation
    if job_data:
        validation_results['job_validation'] = {
            'has_title': bool(job_data.get('Role Information', {}).get('Job Title')),
            'has_requirements': bool(job_data.get('Skills and Competencies', {}).get('Must-have Technical Skills')),
            'has_experience_req': bool(job_data.get('Experience Requirements', {}).get('Years of Experience')),
            'has_responsibilities': bool(job_data.get('Key Responsibilities', {}).get('Primary Duties and Accountabilities'))
        }
    
    # Evaluation data validation
    if evaluation_data:
        validation_results['evaluation_validation'] = {
            'has_score': 'overall_score' in evaluation_data and isinstance(evaluation_data['overall_score'], (int, float)),
            'has_tag': bool(evaluation_data.get('qualification_tag')),
            'has_category_scores': bool(evaluation_data.get('category_scores')),
            'has_strengths': bool(evaluation_data.get('strengths')),
            'has_recommendations': bool(evaluation_data.get('recommendations')),
            'has_interview_questions': bool(evaluation_data.get('interview_questions'))
        }
    
    # Cross-validation
    if resume_data and evaluation_data:
        name_consistency = resume_data.get('candidate_name') == evaluation_data.get('candidate_name')
        validation_results['cross_validation'] = {
            'name_consistency': name_consistency,
            'score_range': 0 <= evaluation_data.get('overall_score', 0) <= 100,
            'tag_validity': evaluation_data.get('qualification_tag') in ['QUALIFIED', 'NOT QUALIFIED', 'OVERQUALIFIED']
        }
    
    # Overall status
    all_validations = []
    for section in validation_results.values():
        if isinstance(section, dict):
            all_validations.extend(section.values())
    
    if not all(all_validations):
        validation_results['overall_status'] = 'FAIL'
        logger.warning("Data flow validation failed")
    else:
        logger.info("Data flow validation passed")
    
    return validation_results

# Create the enhanced crew
enhanced_crew = Crew(
    agents=[
        resume_analyzer,
        job_description_analyzer,
        advanced_evaluator,
        interview_strategist,
        quality_assurance_agent
    ],
    tasks=[
        resume_analysis_task,
        job_analysis_task,
        comprehensive_evaluation_task,
        interview_design_task,
        quality_review_task
    ],
    verbose=True,
    process=Process.sequential
)

# Backwards compatibility exports
crew = enhanced_crew
summarization_task = resume_analysis_task
evaluation_task = comprehensive_evaluation_task
interview_task = interview_design_task
editor_task = quality_review_task
output_parser_task = quality_review_task

if __name__ == "__main__":
    # Test the system
    print("Enhanced Resume Evaluation Engine initialized successfully!")
    print(f"Using model: {model_name}")
    print(f"API endpoint: {base_url or 'OpenAI'}")