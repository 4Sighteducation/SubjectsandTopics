"""
AQA Database Uploader
Uploads scraped data to AQA-specific tables
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()

from utils.logger import get_logger

logger = get_logger()


class AQAUploader:
    """Upload to AQA-specific database tables."""
    
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not url or not key:
            raise ValueError("SUPABASE credentials required")
        
        self.client = create_client(url, key)
        logger.info("AQA uploader initialized")
    
    def upload_subject_complete(self, subject_data: dict) -> dict:
        """
        Upload complete subject data (metadata + topics + components + constraints).
        
        Args:
            subject_data: {
                'subject_name': str,
                'subject_code': str,
                'qualification_type': str,
                'specification_url': str,
                'specification_pdf_url': str,
                'total_guided_learning_hours': int,
                'topics': list,  # With hierarchy
                'components': list,
                'constraints': list
            }
        
        Returns:
            {
                'subject_id': UUID,
                'topics_uploaded': int,
                'components_uploaded': int,
                'constraints_uploaded': int
            }
        """
        
        logger.info(f"Uploading {subject_data['subject_name']} to AQA database...")
        
        # 1. Upload subject metadata (upsert)
        subject_result = self.client.table('aqa_subjects').upsert({
            'subject_name': subject_data['subject_name'],
            'subject_code': subject_data['subject_code'],
            'qualification_type': subject_data['qualification_type'],
            'specification_url': subject_data.get('specification_url'),
            'specification_pdf_url': subject_data.get('specification_pdf_url'),
            'total_guided_learning_hours': subject_data.get('total_guided_learning_hours'),
            'assessment_overview': subject_data.get('assessment_overview'),
            'last_scraped': 'now()',
            'updated_at': 'now()'
        }, on_conflict='subject_code,qualification_type').execute()
        
        if not subject_result.data:
            raise ValueError("Failed to create/update subject")
        
        subject_id = subject_result.data[0]['id']
        logger.info(f"Subject ID: {subject_id}")
        
        # 2. Upload topics with hierarchy
        topics_count = self._upload_topics_hierarchical(
            subject_id, 
            subject_data.get('topics', [])
        )
        
        # 3. Upload components
        components_count = self._upload_components(
            subject_id,
            subject_data.get('components', [])
        )
        
        # 4. Upload constraints
        constraints_count = self._upload_constraints(
            subject_id,
            subject_data.get('constraints', [])
        )
        
        logger.info(f"✓ Upload complete: {topics_count} topics, {components_count} components, {constraints_count} constraints")
        
        return {
            'subject_id': subject_id,
            'topics_uploaded': topics_count,
            'components_uploaded': components_count,
            'constraints_uploaded': constraints_count
        }
    
    def _upload_topics_hierarchical(self, subject_id: str, topics: list) -> int:
        """Upload topics with proper parent-child relationships."""
        
        if not topics:
            return 0
        
        logger.info(f"Uploading {len(topics)} topics with hierarchy...")
        
        # Map topic_code → UUID for building relationships
        code_to_uuid = {}
        uploaded = 0
        
        # Sort by level to ensure parents created before children
        topics_sorted = sorted(topics, key=lambda x: x.get('level', 0))
        
        for topic in topics_sorted:
            try:
                topic_code = topic.get('code')
                parent_code = topic.get('parent_code')
                
                # Look up parent UUID
                parent_uuid = code_to_uuid.get(parent_code) if parent_code else None
                
                topic_data = {
                    'subject_id': subject_id,
                    'topic_code': topic_code,
                    'topic_name': topic.get('title'),
                    'topic_level': topic.get('level', 0),
                    'parent_topic_id': parent_uuid,
                    'description': topic.get('description'),
                    'component_code': topic.get('component_code'),
                    'chronological_period': topic.get('period'),
                    'period_start_year': topic.get('period_start'),
                    'period_end_year': topic.get('period_end'),
                    'geographical_region': topic.get('region'),
                    'key_themes': topic.get('content_points') or topic.get('key_themes')
                }
                
                # Upsert topic
                result = self.client.table('aqa_topics').upsert(
                    topic_data,
                    on_conflict='subject_id,topic_code'
                ).execute()
                
                if result.data:
                    topic_uuid = result.data[0]['id']
                    code_to_uuid[topic_code] = topic_uuid
                    uploaded += 1
                    
            except Exception as e:
                logger.error(f"Error uploading topic {topic.get('code')}: {e}")
        
        return uploaded
    
    def _upload_components(self, subject_id: str, components: list) -> int:
        """Upload component structure."""
        
        if not components:
            return 0
        
        uploaded = 0
        
        for comp in components:
            try:
                self.client.table('aqa_components').upsert({
                    'subject_id': subject_id,
                    'component_code': comp.get('code'),
                    'component_name': comp.get('name'),
                    'component_type': comp.get('type'),
                    'selection_type': comp.get('selection_type'),
                    'count_required': comp.get('count_required'),
                    'total_available': comp.get('total_available'),
                    'assessment_weight': comp.get('weight'),
                    'assessment_format': comp.get('format'),
                    'sort_order': comp.get('sort_order', 0)
                }, on_conflict='subject_id,component_code').execute()
                
                uploaded += 1
                
            except Exception as e:
                logger.error(f"Error uploading component: {e}")
        
        return uploaded
    
    def _upload_constraints(self, subject_id: str, constraints: list) -> int:
        """Upload selection constraints."""
        
        if not constraints:
            return 0
        
        uploaded = 0
        
        for constraint in constraints:
            try:
                # Handle both string and dict formats
                if isinstance(constraint, str):
                    constraint_data = {
                        'subject_id': subject_id,
                        'constraint_type': 'general',
                        'description': constraint,
                        'constraint_rule': {}
                    }
                elif isinstance(constraint, dict):
                    constraint_data = {
                        'subject_id': subject_id,
                        'constraint_type': constraint.get('type', 'general'),
                        'description': constraint.get('description', ''),
                        'constraint_rule': constraint.get('rule_details', {}),
                        'applies_to_components': constraint.get('applies_to_components', [])
                    }
                else:
                    continue
                
                self.client.table('aqa_constraints').insert(constraint_data).execute()
                uploaded += 1
                
            except Exception as e:
                logger.error(f"Error uploading constraint: {e}")
        
        return uploaded


if __name__ == '__main__':
    # Quick test
    uploader = AQAUploader()
    
    # Test data
    test_data = {
        'subject_name': 'Test Subject',
        'subject_code': 'TEST01',
        'qualification_type': 'A-Level',
        'topics': [
            {'code': '3.1', 'title': 'Main Topic', 'level': 0, 'parent_code': None},
            {'code': '3.1.1', 'title': 'Sub Topic', 'level': 1, 'parent_code': '3.1'}
        ],
        'components': [
            {'code': 'C1', 'name': 'Component 1', 'selection_type': 'required_all'}
        ],
        'constraints': []
    }
    
    result = uploader.upload_subject_complete(test_data)
    print(f"\nTest upload: {result}")
    
    # Clean up test
    uploader.client.table('aqa_subjects').delete().eq('subject_code', 'TEST01').execute()
    print("Test data cleaned up")

















