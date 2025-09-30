"""
Supabase client and uploader for curriculum data.
Replaces Knack integration with direct Supabase uploads.
"""

import os
from typing import List, Dict, Tuple, Optional
from supabase import create_client, Client
from utils.logger import get_logger

logger = get_logger()


class SupabaseUploader:
    """
    Uploader for curriculum topic data directly to Supabase.
    Handles all new tables: specification_metadata, spec_components, etc.
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize Supabase client.
        
        Args:
            supabase_url: Supabase project URL (from env if not provided)
            supabase_key: Supabase service role key (from env if not provided)
        """
        self.url = supabase_url or os.getenv('SUPABASE_URL')
        self.key = supabase_key or os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and service key must be provided")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase uploader initialized")
    
    def upload_specification_complete(self, complete_data: Dict) -> Dict:
        """
        Upload complete specification data including metadata, components, constraints, and topics.
        
        Args:
            complete_data: Complete package from enhanced scraper containing:
                - metadata: subject info
                - components: course structure  
                - constraints: selection rules
                - options: topic options
                - vocabulary: key terms
                Plus exam_board, subject, qualification at root level
            
        Returns:
            Dict with upload results
        """
        results = {
            'metadata_id': None,
            'components': 0,
            'constraints': 0,
            'topics': 0,
            'vocabulary': 0,
            'errors': []
        }
        
        try:
            # Extract root-level context
            exam_board = complete_data.get('exam_board', 'AQA')
            subject = complete_data.get('subject', 'Unknown')
            qualification = complete_data.get('qualification', 'A-Level')
            
            # 1. Upload specification metadata
            metadata_id = self._upload_metadata(
                complete_data.get('metadata', {}),
                exam_board,
                subject,
                qualification
            )
            results['metadata_id'] = metadata_id
            
            # 2. Upload components
            component_ids = self._upload_components(
                metadata_id, complete_data.get('components', [])
            )
            results['components'] = len(component_ids)
            
            # 3. Upload constraints
            constraint_count = self._upload_constraints(
                metadata_id, complete_data.get('constraints', [])
            )
            results['constraints'] = constraint_count
            
            # 4. Upload topic options with enhanced metadata
            topic_count = self._upload_topic_options(
                complete_data.get('options', []),
                complete_data.get('detailed_topics', {})
            )
            results['topics'] = topic_count
            
            # 5. Upload vocabulary
            vocab_count = self._upload_vocabulary(
                metadata_id, complete_data.get('vocabulary', [])
            )
            results['vocabulary'] = vocab_count
            
            logger.info(f"Successfully uploaded complete specification: {results}")
            
        except Exception as e:
            logger.error(f"Error uploading specification: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def _upload_metadata(self, metadata: Dict, exam_board: str, subject: str, qualification: str) -> str:
        """Upload specification metadata, return ID."""
        try:
            # Map from extraction format to database format
            data_to_insert = {
                'exam_board': exam_board,
                'qualification_type': qualification.lower().replace('-', '_'),
                'subject_name': subject,
                'subject_code': metadata.get('subject_code'),
                'spec_version': metadata.get('spec_version'),
                'subject_description': metadata.get('description'),
                'total_guided_learning_hours': metadata.get('guided_learning_hours'),
                'assessment_overview': metadata.get('assessment_overview'),
                'specification_url': metadata.get('specification_url'),
                'specification_pdf_url': metadata.get('specification_pdf_url')
            }
            
            logger.info(f"Uploading metadata: {exam_board} {subject} {qualification}")
            
            result = self.client.table('specification_metadata').upsert(
                data_to_insert,
                on_conflict='exam_board,qualification_type,subject_name'
            ).execute()
            
            if result.data:
                logger.info(f"Uploaded metadata for {metadata.get('subject')}")
                return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Failed to upload metadata: {e}")
            raise
    
    def _upload_components(self, spec_id: str, components: List[Dict]) -> List[str]:
        """Upload spec components."""
        component_ids = []
        
        for i, component in enumerate(components):
            try:
                result = self.client.table('spec_components').insert({
                    'spec_metadata_id': spec_id,
                    'component_code': component.get('code'),
                    'component_name': component.get('name'),
                    'component_type': component.get('type'),
                    'selection_type': component.get('selection_type'),
                    'count_required': component.get('count_required'),
                    'total_available': component.get('total_available'),
                    'assessment_weight': component.get('weight'),
                    'assessment_format': component.get('assessment'),
                    'assessment_description': component.get('description'),
                    'sort_order': i
                }).execute()
                
                if result.data:
                    component_ids.append(result.data[0]['id'])
                    
            except Exception as e:
                logger.error(f"Failed to upload component {component.get('name')}: {e}")
        
        return component_ids
    
    def _upload_constraints(self, spec_id: str, constraints: List[Dict]) -> int:
        """Upload selection constraints."""
        count = 0
        
        for constraint in constraints:
            try:
                self.client.table('selection_constraints').insert({
                    'spec_metadata_id': spec_id,
                    'constraint_type': constraint.get('type'),
                    'constraint_rule': constraint.get('rule_details', {}),
                    'description': constraint.get('description'),
                    'applies_to_components': constraint.get('applies_to_components', [])
                }).execute()
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to upload constraint: {e}")
        
        return count
    
    def _upload_topic_options(self, options: List[Dict], detailed_topics: Dict) -> int:
        """Upload topic options with detailed subtopics."""
        count = 0
        
        if not options:
            logger.warning("No topic options to upload")
            return 0
        
        # Get exam_board_subject_id first (required foreign key)
        first_option = options[0]
        exam_board = first_option.get('exam_board', 'AQA')
        subject = first_option.get('subject', 'Unknown')
        qualification = first_option.get('qualification', 'A-Level')
        
        # Find the exam_board_subject record
        exam_board_subject_id = self._get_or_create_exam_board_subject(exam_board, subject, qualification)
        
        if not exam_board_subject_id:
            logger.error(f"Could not find/create exam_board_subject for {exam_board} {subject}")
            return 0
        
        for option in options:
            try:
                # Upload the main topic option using existing schema
                result = self.client.table('curriculum_topics').insert({
                    'exam_board_subject_id': exam_board_subject_id,  # Use foreign key
                    'topic_code': option.get('code'),
                    'component_code': option.get('component_code'),
                    'topic_name': option.get('title'),
                    'topic_type': option.get('type'),
                    'topic_level': 0,  # Top-level option
                    'chronological_period': option.get('period'),
                    'period_start_year': option.get('period_start'),
                    'period_end_year': option.get('period_end'),
                    'period_length_years': option.get('period_length'),
                    'geographical_region': option.get('region'),
                    'key_themes': option.get('key_themes', []),
                    'page_reference': option.get('page_reference'),
                    'description': option.get('title'),  # Use title as description
                    
                    # NEW: Version markers
                    'scraping_version': 'v2_enhanced',
                    'scraping_source': 'web_scraper',
                    'last_scraped': 'now()',
                    'data_quality_score': 4  # High quality - has metadata
                }).execute()
                
                count += 1
                
                # Upload detailed subtopics for this option
                option_code = option.get('code')
                if option_code in detailed_topics:
                    self._upload_subtopics(
                        option_code,
                        detailed_topics[option_code],
                        option
                    )
                    
            except Exception as e:
                logger.error(f"Failed to upload option {option.get('code')}: {e}")
        
        return count
    
    def _upload_subtopics(self, parent_code: str, subtopics: List[Dict], parent_option: Dict):
        """Upload detailed subtopics for a topic option."""
        for subtopic_data in subtopics:
            try:
                modules = subtopic_data.get('modules', [])
                for module in modules:
                    # Upload module level
                    self.client.table('curriculum_topics').upsert({
                        'exam_board': parent_option.get('exam_board'),
                        'qualification_type': parent_option.get('qualification'),
                        'subject_name': parent_option.get('subject'),
                        'parent_topic_id': parent_code,
                        'topic_name': module.get('module_title'),
                        'topic_level': 1,
                        'chronological_period': module.get('period'),
                        'key_themes': module.get('content_points', []),
                        'assessment_focus': module.get('assessment_focus')
                    }).execute()
                    
            except Exception as e:
                logger.error(f"Failed to upload subtopic: {e}")
    
    def _upload_vocabulary(self, spec_id: str, vocabulary: List) -> int:
        """Upload subject vocabulary."""
        count = 0
        
        if not vocabulary:
            return 0
        
        for term_data in vocabulary:
            try:
                # Handle both dict and string formats
                if isinstance(term_data, str):
                    # Simple string format
                    self.client.table('subject_vocabulary').insert({
                        'spec_metadata_id': spec_id,
                        'term': term_data,
                        'category': 'general',
                        'importance': 'medium'
                    }).execute()
                elif isinstance(term_data, dict):
                    # Dict format with details
                    self.client.table('subject_vocabulary').insert({
                        'spec_metadata_id': spec_id,
                        'term': term_data.get('term'),
                        'definition': term_data.get('definition'),
                        'category': term_data.get('category', 'general'),
                        'importance': term_data.get('importance', 'medium')
                    }).execute()
                else:
                    logger.warning(f"Unknown vocabulary format: {type(term_data)}")
                    continue
                    
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to upload vocabulary term: {e}")
        
        return count
    
    def upload_topics_batch(self, topics: List[Dict], batch_size: int = 100) -> Tuple[int, int]:
        """
        Upload topics in batches (legacy method for simple topics).
        Use upload_specification_complete() for enhanced data.
        
        Args:
            topics: List of topic dictionaries
            batch_size: Number of records per batch
            
        Returns:
            Tuple of (success_count, error_count)
        """
        success = 0
        errors = 0
        
        for i in range(0, len(topics), batch_size):
            batch = topics[i:i + batch_size]
            
            try:
                transformed = [self._transform_legacy_topic(t) for t in batch]
                
                result = self.client.table('curriculum_topics').upsert(
                    transformed,
                    on_conflict='exam_board,qualification_type,subject_name,topic_name,parent_topic_id'
                ).execute()
                
                success += len(batch)
                logger.info(f"Uploaded batch {i//batch_size + 1}: {len(batch)} topics")
                
            except Exception as e:
                errors += len(batch)
                logger.error(f"Failed to upload batch: {e}")
        
        return (success, errors)
    
    def _transform_legacy_topic(self, topic: Dict) -> Dict:
        """Transform old topic format to Supabase schema."""
        return {
            'exam_board': topic.get('Exam Board'),
            'qualification_type': self._normalize_qualification(topic.get('Exam Type')),
            'subject_name': topic.get('Subject'),
            'topic_name': topic.get('Topic'),
            'parent_topic_id': topic.get('Module'),
            'topic_level': 2 if topic.get('Sub Topic') else 1,
            'is_active': True
        }
    
    def _get_or_create_exam_board_subject(self, exam_board: str, subject: str, qualification: str = 'A-Level') -> Optional[str]:
        """
        Find or create exam_board_subject record and return its ID.
        This is needed because curriculum_topics uses exam_board_subject_id foreign key.
        """
        try:
            # First, get the exam_board_id
            board_result = self.client.table('exam_boards').select('id').eq('code', exam_board).execute()
            if not board_result.data:
                logger.error(f"Exam board {exam_board} not found in database")
                return None
            
            exam_board_id = board_result.data[0]['id']
            
            # Get the qualification_type_id
            qual_code = qualification.upper().replace('-', '_')  # A-Level → A_LEVEL
            qual_result = self.client.table('qualification_types').select('id').eq('code', qual_code).execute()
            if not qual_result.data:
                logger.error(f"Qualification type {qualification} not found")
                return None
            
            qualification_type_id = qual_result.data[0]['id']
            
            # Now find the exam_board_subject with BOTH IDs
            result = self.client.table('exam_board_subjects').select('id').eq(
                'subject_name', subject
            ).eq(
                'exam_board_id', exam_board_id
            ).eq(
                'qualification_type_id', qualification_type_id
            ).execute()
            
            if result.data and len(result.data) > 0:
                subject_id = result.data[0]['id']
                logger.info(f"Found exam_board_subject ID for {exam_board} {subject} {qualification}: {subject_id}")
                return subject_id
            
            logger.warning(f"No exam_board_subject found for {exam_board} {subject} {qualification}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding exam_board_subject: {e}")
            return None
    
    def _normalize_qualification(self, exam_type: str) -> str:
        """Normalize exam type to match database enum."""
        if not exam_type:
            return 'gcse'
        
        mapping = {
            'GCSE': 'gcse',
            'A-Level': 'a-level',
            'AS-Level': 'as-level',
            'A-level': 'a-level',
            'AS-level': 'as-level',
            'BTEC': 'btec',
            'IB': 'ib',
            'IGCSE': 'igcse'
        }
        return mapping.get(exam_type, exam_type.lower().replace(' ', '-'))
