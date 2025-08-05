#!/usr/bin/env python3
"""
Script to clean up test data from the database
"""

from supabase_manager import get_supabase_manager

def cleanup_test_data():
    """Remove test data from the database"""
    try:
        supabase_manager = get_supabase_manager()
        
        # Delete test candidate
        response = supabase_manager.client.table('resume_evaluation_results').delete().eq('candidate_name', 'Test Candidate').execute()
        
        print(f"✅ Cleaned up test data: {len(response.data)} records deleted")
        
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")

if __name__ == "__main__":
    cleanup_test_data() 