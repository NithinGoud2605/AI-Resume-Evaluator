#!/usr/bin/env python3
"""
Script to check database schema and verify interview_questions column exists
"""

import os
from dotenv import load_dotenv
from supabase_manager import get_supabase_manager

load_dotenv()

def check_supabase_schema():
    """Check if interview_questions column exists in Supabase"""
    try:
        supabase_manager = get_supabase_manager()
        
        # Get a sample result to see the structure
        results = supabase_manager.get_all_results()
        
        if results:
            print("✅ Database connection successful")
            print(f"📊 Found {len(results)} results")
            
            # Check the first result structure
            first_result = results[0]
            print("\n📋 Sample result structure:")
            for key, value in first_result.items():
                print(f"  {key}: {type(value).__name__} = {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            
            # Check specifically for interview_questions
            if 'interview_questions' in first_result:
                print(f"\n✅ interview_questions column exists!")
                interview_data = first_result['interview_questions']
                if interview_data:
                    print(f"📝 Interview questions data: {interview_data}")
                else:
                    print("⚠️  interview_questions column exists but is empty/null")
            else:
                print("\n❌ interview_questions column NOT found!")
                print("Available columns:", list(first_result.keys()))
                
        else:
            print("⚠️  No results found in database")
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        import traceback
        traceback.print_exc()

def create_interview_questions_column():
    """Create the interview_questions column if it doesn't exist"""
    try:
        supabase_manager = get_supabase_manager()
        
        # SQL to add the column
        sql = """
        ALTER TABLE resume_evaluation_results 
        ADD COLUMN IF NOT EXISTS interview_questions JSONB;
        """
        
        # Execute the SQL
        response = supabase_manager.client.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ interview_questions column created successfully")
        
    except Exception as e:
        print(f"❌ Error creating column: {e}")
        print("You may need to manually add the column in Supabase dashboard")

if __name__ == "__main__":
    print("🔍 Checking Supabase schema...")
    check_supabase_schema()
    
    print("\n" + "="*50)
    print("Would you like to create the interview_questions column? (y/n)")
    response = input().lower().strip()
    
    if response == 'y':
        print("🔧 Creating interview_questions column...")
        create_interview_questions_column()
    else:
        print("⏭️  Skipping column creation") 