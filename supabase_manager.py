"""
Supabase database manager for the Resume Evaluator application
"""
import os
import logging
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime
from supabase import create_client, Client
from config import Config

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL), 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseManager:
    """Handles Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = Config.SUPABASE_URL
        self.supabase_key = Config.SUPABASE_KEY or Config.SUPABASE_ANON_KEY
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test the Supabase connection"""
        try:
            # Try a simple query to test connection
            result = self.client.table('resume_evaluation_results').select('id').limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
    
    def insert_evaluation_result(self, result_data: Dict[str, Any]) -> Optional[str]:
        """Insert a single evaluation result"""
        try:
            # Convert any JSON fields to proper format
            if 'extracted_skills' in result_data and isinstance(result_data['extracted_skills'], str):
                result_data['extracted_skills'] = json.loads(result_data['extracted_skills'])
            if 'previous_roles' in result_data and isinstance(result_data['previous_roles'], str):
                result_data['previous_roles'] = json.loads(result_data['previous_roles'])
            if 'certifications' in result_data and isinstance(result_data['certifications'], str):
                result_data['certifications'] = json.loads(result_data['certifications'])
            # Handle interview_questions field
            if 'interview_questions' in result_data and isinstance(result_data['interview_questions'], str):
                result_data['interview_questions'] = json.loads(result_data['interview_questions'])
            
            # Ensure required fields are present
            required_fields = ['candidate_name', 'overall_score', 'qualification_tag']
            for field in required_fields:
                if field not in result_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Insert the record
            response = self.client.table('resume_evaluation_results').insert(result_data).execute()
            
            if response.data:
                inserted_id = response.data[0]['id']
                logger.info(f"Successfully inserted evaluation result for {result_data['candidate_name']}")
                return inserted_id
            else:
                logger.error("No data returned from insert operation")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting evaluation result: {e}")
            raise
    
    def insert_multiple_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple evaluation results"""
        inserted_ids = []
        
        try:
            for result in results:
                inserted_id = self.insert_evaluation_result(result)
                if inserted_id:
                    inserted_ids.append(inserted_id)
            
            logger.info(f"Successfully inserted {len(inserted_ids)} evaluation results")
            return inserted_ids
            
        except Exception as e:
            logger.error(f"Error inserting multiple results: {e}")
            raise
    
    def get_all_results(self) -> List[Dict[str, Any]]:
        """Get all evaluation results"""
        try:
            response = self.client.table('resume_evaluation_results').select('*').order('evaluated_at', desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching all results: {e}")
            return []
    
    def get_results_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get results for a specific session"""
        try:
            response = self.client.table('resume_evaluation_results').select('*').eq('session_id', session_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching results for session {session_id}: {e}")
            return []
    
    def get_candidate_results(self, candidate_name: str) -> List[Dict[str, Any]]:
        """Get all results for a specific candidate"""
        try:
            response = self.client.table('resume_evaluation_results').select('*').eq('candidate_name', candidate_name).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching results for candidate {candidate_name}: {e}")
            return []
    
    def clear_all_results(self) -> bool:
        """Clear all evaluation results (use with caution)"""
        try:
            response = self.client.table('resume_evaluation_results').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logger.info("Successfully cleared all evaluation results")
            return True
        except Exception as e:
            logger.error(f"Error clearing results: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evaluation statistics"""
        try:
            # Get total count
            total_response = self.client.table('resume_evaluation_results').select('id', count='exact').execute()
            total_count = total_response.count if total_response.count is not None else 0
            
            # Get qualified count
            qualified_response = self.client.table('resume_evaluation_results').select('id', count='exact').eq('qualification_tag', 'QUALIFIED').execute()
            qualified_count = qualified_response.count if qualified_response.count is not None else 0
            
            # Get not qualified count
            not_qualified_response = self.client.table('resume_evaluation_results').select('id', count='exact').eq('qualification_tag', 'NOT QUALIFIED').execute()
            not_qualified_count = not_qualified_response.count if not_qualified_response.count is not None else 0
            
            # Get overqualified count
            overqualified_response = self.client.table('resume_evaluation_results').select('id', count='exact').eq('qualification_tag', 'OVERQUALIFIED').execute()
            overqualified_count = overqualified_response.count if overqualified_response.count is not None else 0
            
            # Get average score
            avg_response = self.client.table('resume_evaluation_results').select('overall_score').execute()
            scores = [result['overall_score'] for result in avg_response.data if result['overall_score'] is not None]
            average_score = sum(scores) / len(scores) if scores else 0
            
            # Get highest and lowest scores
            highest_score = max(scores) if scores else 0
            lowest_score = min(scores) if scores else 0
            
            return {
                'total_candidates': total_count,
                'qualified_count': qualified_count,
                'not_qualified_count': not_qualified_count,
                'overqualified_count': overqualified_count,
                'average_score': round(average_score, 2),
                'highest_score': highest_score,
                'lowest_score': lowest_score
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'total_candidates': 0,
                'qualified_count': 0,
                'not_qualified_count': 0,
                'overqualified_count': 0,
                'average_score': 0,
                'highest_score': 0,
                'lowest_score': 0
            }
    
    def create_evaluation_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Create a new evaluation session"""
        try:
            response = self.client.table('evaluation_sessions').insert(session_data).execute()
            if response.data:
                session_id = response.data[0]['id']
                logger.info(f"Created evaluation session: {session_id}")
                return session_id
            return None
        except Exception as e:
            logger.error(f"Error creating evaluation session: {e}")
            return None
    
    def update_session_status(self, session_id: str, status: str, **kwargs) -> bool:
        """Update session status"""
        try:
            update_data = {'status': status, **kwargs}
            if status == 'completed':
                update_data['completed_at'] = datetime.utcnow().isoformat()
            
            response = self.client.table('evaluation_sessions').update(update_data).eq('id', session_id).execute()
            logger.info(f"Updated session {session_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating session status: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details"""
        try:
            response = self.client.table('evaluation_sessions').select('*').eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all evaluation sessions"""
        try:
            response = self.client.table('evaluation_sessions').select('*').order('started_at', desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching all sessions: {e}")
            return []

# Global instance
supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """Get or create Supabase manager instance"""
    global supabase_manager
    if supabase_manager is None:
        supabase_manager = SupabaseManager()
    return supabase_manager

def test_supabase_connection() -> bool:
    """Test Supabase connection"""
    try:
        manager = get_supabase_manager()
        return manager.test_connection()
    except Exception as e:
        logger.error(f"Supabase connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the connection
    if test_supabase_connection():
        print("✅ Supabase connection successful")
    else:
        print("❌ Supabase connection failed") 