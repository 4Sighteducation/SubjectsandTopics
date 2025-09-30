# FLASH - Curriculum Content Pipeline Strategy V2
**Date:** September 30, 2025  
**Based On:** Existing Topic List Scraper System  
**Objective:** Unified, robust pipeline that updates Supabase directly  
**Update Frequency:** Every 6 months (automated)

---

## Executive Summary

This document outlines an improved curriculum content pipeline **building on your existing Topic List Scraper** system. Instead of starting from scratch, we'll:

1. **Refactor** the existing working architecture
2. **Unify** the scrapers into a single orchestrated pipeline
3. **Replace** Knack with direct Supabase integration
4. **Improve** error handling and reliability
5. **Automate** the entire process with scheduling

**Timeline:**
- **Phase 1 (Week 1-2):** Refactor existing code, add Supabase integration
- **Phase 2 (Week 3-4):** Unified orchestration, better error handling
- **Phase 3 (Week 5-6):** Automation, monitoring, and deployment

---

## Analysis of Existing System

### ✅ What Works Well (Keep & Improve)

#### 1. **Strong Foundation Architecture**
- ✅ `BaseScraper` class with inheritance pattern
- ✅ Separate scrapers per exam board (AQA, Edexcel, OCR, WJEC, SQA, CCEA)
- ✅ Organized data structure (`data/raw/`, `data/processed/`)
- ✅ Helper utilities (`utils/helpers.py`, `utils/logger.py`)
- ✅ Good logging system

**Keep:** The base architecture is solid

#### 2. **AI-Assisted Extraction**
- ✅ `ai_helpers/topic_extractor.py` using Claude/Gemini
- ✅ Handles both PDF and HTML extraction
- ✅ Structured JSON output format
- ✅ Fallback mechanism (Gemini → Anthropic)
- ✅ Good prompt engineering

**Keep:** This is excellent and working well

#### 3. **Comprehensive Coverage**
- ✅ Direct specification URLs for major subjects
- ✅ Fallback topic structures for problematic subjects
- ✅ 357 log files show extensive testing/usage
- ✅ Large data collection already exists

**Build On:** Leverage existing data and knowledge

### ❌ What Needs Improvement (Fix)

#### 1. **Fragmented Execution** ⚠️ HIGH PRIORITY
**Problem:**
- Separate scraper files for each board
- Must run manually per board
- No unified orchestration
- Many test files (`test_*.py`) suggest debugging challenges

**Solution:**
- Single `pipeline.py` orchestrator
- Runs all boards in sequence or parallel
- Progress tracking
- Resume capability on failure

#### 2. **Inconsistent Error Handling** ⚠️ HIGH PRIORITY
**Problem:**
- 357 log files = lots of errors/retries
- No centralized error recovery
- Failures require manual intervention

**Solution:**
- Unified error handling strategy
- Automatic retries with exponential backoff
- Graceful degradation
- Error notification system

#### 3. **Knack Integration** ⚠️ HIGH PRIORITY
**Problem:**
- Uses Knack API (`knack/topics_uploader.py`)
- Need direct Supabase integration
- Current duplicate checking is slow

**Solution:**
- Replace with `supabase_uploader.py`
- Batch upserts for performance
- Smart deduplication before upload

#### 4. **No Automation** ⚠️ MEDIUM PRIORITY
**Problem:**
- Fully manual process
- No scheduling
- No change detection

**Solution:**
- GitHub Actions workflow
- Runs every 6 months automatically
- Detects curriculum changes
- Alerts on completion/failure

#### 5. **Data Quality Issues** ⚠️ MEDIUM PRIORITY
**Problem:**
- Some duplicates in data
- Patchy coverage for some boards
- Manual verification needed

**Solution:**
- Pre-upload validation
- Standardized normalization
- Quality scoring system
- Manual review interface for edge cases

---

## Improved Architecture

### System Components (Enhanced)

```
┌────────────────────────────────────────────────────────┐
│                 Unified Pipeline Orchestrator           │
│              (pipeline.py - NEW MAIN ENTRY)            │
└────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Scrapers   │    │ Processors   │    │   Storage    │
│ (EXISTING)   │    │ (ENHANCED)   │    │   (NEW)      │
│              │    │              │    │              │
│ - AQA        │───▶│ - Normalize  │───▶│ - Supabase   │
│ - Edexcel    │    │ - Dedupe     │    │ - Direct     │
│ - OCR        │    │ - Validate   │    │ - Batch      │
│ - WJEC       │    │ - Quality    │    │ - Upsert     │
│ - SQA        │    │ - Scoring    │    │              │
│ - CCEA       │    │              │    │              │
│              │    │              │    │              │
│ AI Helpers   │    │              │    │              │
│ - Claude     │    │              │    │              │
│ - Gemini     │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                ┌──────────────────────┐
                │    Orchestration     │
                │      (NEW)           │
                │                      │
                │ - Progress tracking  │
                │ - Error recovery     │
                │ - Resume capability  │
                │ - Notifications      │
                │ - Change detection   │
                └──────────────────────┘
```

### Key Improvements

1. **Single Entry Point:** `pipeline.py` instead of `main.py`
2. **Unified Execution:** All boards run through one process
3. **Better State Management:** Save progress, resume on failure
4. **Direct Supabase:** No intermediate database
5. **Smart Batching:** Efficient bulk operations

---

## Implementation Plan

### Phase 1: Refactor & Integrate (Weeks 1-2)

#### Week 1: Supabase Integration

**Goal:** Replace Knack with Supabase

```python
# NEW FILE: database/supabase_uploader.py

from supabase import create_client, Client
from typing import List, Dict, Tuple
from utils.logger import get_logger

logger = get_logger()

class SupabaseUploader:
    """
    Uploader for curriculum topic data directly to Supabase.
    Replaces knack/topics_uploader.py
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize Supabase client.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key (for admin operations)
        """
        self.client: Client = create_client(supabase_url, supabase_key)
        self.table_name = "curriculum_topics"
        logger.info("Supabase uploader initialized")
    
    def upload_batch(self, topics: List[Dict], batch_size: int = 100) -> Tuple[int, int]:
        """
        Upload topics in batches using upsert for deduplication.
        
        Args:
            topics: List of topic dictionaries
            batch_size: Number of records per batch
            
        Returns:
            Tuple of (success_count, error_count)
        """
        success = 0
        errors = 0
        
        # Process in batches
        for i in range(0, len(topics), batch_size):
            batch = topics[i:i + batch_size]
            
            try:
                # Transform to match Supabase schema
                transformed = [self._transform_topic(t) for t in batch]
                
                # Upsert (insert or update on conflict)
                # This handles duplicates automatically
                result = self.client.table(self.table_name).upsert(
                    transformed,
                    on_conflict="exam_board,qualification_type,subject_name,topic_level,topic_name"
                ).execute()
                
                success += len(batch)
                logger.info(f"Uploaded batch {i//batch_size + 1}: {len(batch)} topics")
                
            except Exception as e:
                errors += len(batch)
                logger.error(f"Failed to upload batch {i//batch_size + 1}: {e}")
        
        return (success, errors)
    
    def _transform_topic(self, topic: Dict) -> Dict:
        """
        Transform scraped topic data to Supabase schema.
        
        Args:
            topic: Raw topic data from scraper
            
        Returns:
            Transformed data matching curriculum_topics table
        """
        # Map from scraper format to Supabase schema
        return {
            "exam_board": topic.get("Exam Board"),
            "qualification_type": self._normalize_qualification(topic.get("Exam Type")),
            "subject_name": topic.get("Subject"),
            "topic_level": self._determine_level(topic),
            "topic_name": topic.get("Topic"),
            "parent_topic_name": topic.get("Module"),
            "sub_topics": topic.get("Sub Topic") if isinstance(topic.get("Sub Topic"), list) else [topic.get("Sub Topic")] if topic.get("Sub Topic") else [],
            "source_url": topic.get("source_url"),
            "scraped_date": "now()",
            "is_active": True
        }
    
    def _normalize_qualification(self, exam_type: str) -> str:
        """Normalize exam type to match database enum."""
        mapping = {
            "GCSE": "gcse",
            "A-Level": "a-level",
            "AS-Level": "as-level",
            "BTEC": "btec",
            "IB": "ib"
        }
        return mapping.get(exam_type, exam_type.lower())
    
    def _determine_level(self, topic: Dict) -> int:
        """
        Determine topic hierarchy level.
        0=module, 1=topic, 2=subtopic
        """
        if topic.get("Sub Topic"):
            return 2
        elif topic.get("Module"):
            return 1
        else:
            return 0
    
    def verify_upload(self, exam_board: str, subject: str) -> Dict:
        """
        Verify that topics were uploaded successfully.
        
        Args:
            exam_board: Exam board to check
            subject: Subject to check
            
        Returns:
            Dict with counts by level
        """
        try:
            result = self.client.table(self.table_name).select(
                "topic_level",
                count="exact"
            ).eq(
                "exam_board", exam_board
            ).eq(
                "subject_name", subject
            ).execute()
            
            return {
                "total": result.count,
                "data": result.data
            }
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {}
```

**Tasks for Week 1:**
- [ ] Create `database/supabase_uploader.py` (above)
- [ ] Update `.env.example` with Supabase credentials
- [ ] Test Supabase connection and schema mapping
- [ ] Create migration to add versioning fields to Supabase
- [ ] Write integration tests

#### Week 2: Unified Orchestrator

**Goal:** Single pipeline that runs all boards

```python
# NEW FILE: pipeline.py

"""
Unified Curriculum Content Pipeline
Orchestrates all exam board scrapers with error recovery and progress tracking
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from database.supabase_uploader import SupabaseUploader
from processors.topic_processor import TopicProcessor
from utils.logger import get_logger
from scrapers import (
    AQAScraper, EdexcelScraper, OCRScraper,
    WJECScraper, SQAScraper, CCEAScraper
)

logger = get_logger()

@dataclass
class PipelineState:
    """Track pipeline execution state for resumability."""
    run_id: str
    started_at: str
    completed_boards: List[str]
    failed_boards: Dict[str, str]  # board: error_message
    total_topics_uploaded: int
    current_board: Optional[str] = None
    
    def save(self, filepath: str):
        """Save state to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> Optional['PipelineState']:
        """Load state from JSON file."""
        if not Path(filepath).exists():
            return None
        with open(filepath, 'r') as f:
            return cls(**json.load(f))


class CurriculumPipeline:
    """
    Unified pipeline orchestrator for all exam board scrapers.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the pipeline.
        
        Args:
            config: Configuration dictionary with credentials and settings
        """
        self.config = config
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.state_file = f"data/pipeline_state_{self.run_id}.json"
        
        # Initialize components
        self.uploader = SupabaseUploader(
            supabase_url=config['supabase_url'],
            supabase_key=config['supabase_key']
        )
        self.processor = TopicProcessor(
            output_dir="data/processed/topics"
        )
        
        # Initialize scrapers
        self.scrapers = {
            'AQA': AQAScraper(headless=config.get('headless', True)),
            'Edexcel': EdexcelScraper(headless=config.get('headless', True)),
            'OCR': OCRScraper(headless=config.get('headless', True)),
            'WJEC': WJECScraper(headless=config.get('headless', True)),
            'SQA': SQAScraper(headless=config.get('headless', True)),
            'CCEA': CCEAScraper(headless=config.get('headless', True))
        }
        
        # Load previous state if resuming
        self.state = PipelineState.load(self.state_file) or PipelineState(
            run_id=self.run_id,
            started_at=datetime.now().isoformat(),
            completed_boards=[],
            failed_boards={},
            total_topics_uploaded=0
        )
        
        logger.info(f"Pipeline initialized: Run ID {self.run_id}")
    
    def run(self, boards: List[str] = None, exam_types: List[str] = None):
        """
        Run the complete pipeline for specified boards.
        
        Args:
            boards: List of board names to process (None = all)
            exam_types: List of exam types to scrape (None = all)
        """
        boards_to_process = boards or list(self.scrapers.keys())
        
        # Filter out already completed boards if resuming
        remaining_boards = [
            b for b in boards_to_process 
            if b not in self.state.completed_boards
        ]
        
        logger.info(f"Processing {len(remaining_boards)} boards: {remaining_boards}")
        
        for board_name in remaining_boards:
            self.state.current_board = board_name
            self.state.save(self.state_file)
            
            try:
                logger.info(f"=== Starting {board_name} ===")
                self._process_board(board_name, exam_types)
                
                self.state.completed_boards.append(board_name)
                self.state.current_board = None
                self.state.save(self.state_file)
                
                logger.info(f"=== Completed {board_name} ===")
                
            except Exception as e:
                logger.error(f"Failed to process {board_name}: {e}", exc_info=True)
                self.state.failed_boards[board_name] = str(e)
                self.state.save(self.state_file)
                
                # Continue with next board instead of failing entire pipeline
                continue
        
        # Final summary
        self._print_summary()
    
    def _process_board(self, board_name: str, exam_types: List[str] = None):
        """
        Process a single exam board.
        
        Args:
            board_name: Name of the exam board
            exam_types: List of exam types to process
        """
        scraper = self.scrapers[board_name]
        exam_types = exam_types or ['gcse', 'a-level']
        
        for exam_type in exam_types:
            logger.info(f"Scraping {exam_type} topics from {board_name}")
            
            try:
                # Scrape topics
                raw_topics = scraper.scrape_topics(
                    subject=None,  # None = all subjects
                    exam_type=exam_type
                )
                
                if not raw_topics:
                    logger.warning(f"No topics found for {board_name} {exam_type}")
                    continue
                
                logger.info(f"Scraped {len(raw_topics)} raw topics")
                
                # Process topics
                processed_topics = self.processor.process(
                    raw_topics, 
                    board_name
                )
                
                logger.info(f"Processed to {len(processed_topics)} topics")
                
                # Validate topics
                valid_topics = self._validate_topics(processed_topics)
                
                logger.info(f"Validated {len(valid_topics)} topics")
                
                # Upload to Supabase
                success, errors = self.uploader.upload_batch(valid_topics)
                
                self.state.total_topics_uploaded += success
                
                logger.info(
                    f"Uploaded {success} topics, {errors} errors "
                    f"for {board_name} {exam_type}"
                )
                
            except Exception as e:
                logger.error(
                    f"Error processing {board_name} {exam_type}: {e}",
                    exc_info=True
                )
                raise
            
            finally:
                # Always close scraper after use
                scraper.close()
    
    def _validate_topics(self, topics: List[Dict]) -> List[Dict]:
        """
        Validate and filter topics before upload.
        
        Args:
            topics: List of processed topics
            
        Returns:
            List of valid topics
        """
        valid = []
        
        for topic in topics:
            # Check required fields
            if not all(topic.get(f) for f in ['Exam Board', 'Subject', 'Topic']):
                logger.warning(f"Skipping invalid topic: {topic}")
                continue
            
            # Check topic length (avoid garbage)
            if len(topic.get('Topic', '')) > 200:
                logger.warning(f"Topic too long: {topic.get('Topic')[:50]}...")
                continue
            
            # Quality checks passed
            valid.append(topic)
        
        return valid
    
    def _print_summary(self):
        """Print final pipeline summary."""
        logger.info("=" * 60)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Run ID: {self.state.run_id}")
        logger.info(f"Started: {self.state.started_at}")
        logger.info(f"Completed boards: {len(self.state.completed_boards)}")
        logger.info(f"Failed boards: {len(self.state.failed_boards)}")
        logger.info(f"Total topics uploaded: {self.state.total_topics_uploaded}")
        
        if self.state.failed_boards:
            logger.warning("Failed boards:")
            for board, error in self.state.failed_boards.items():
                logger.warning(f"  - {board}: {error}")
        
        logger.info("=" * 60)


def main():
    """Main entry point for the pipeline."""
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'supabase_url': os.getenv('SUPABASE_URL'),
        'supabase_key': os.getenv('SUPABASE_SERVICE_KEY'),
        'headless': os.getenv('HEADLESS', 'true').lower() == 'true'
    }
    
    # Validate config
    if not all([config['supabase_url'], config['supabase_key']]):
        logger.error("Missing required environment variables")
        return 1
    
    # Create and run pipeline
    pipeline = CurriculumPipeline(config)
    pipeline.run()
    
    return 0


if __name__ == '__main__':
    exit(main())
```

**Tasks for Week 2:**
- [ ] Create `pipeline.py` (above)
- [ ] Add state management for resumability
- [ ] Test with single board (AQA)
- [ ] Test error recovery (simulate failures)
- [ ] Test full pipeline with all boards
- [ ] Document new architecture

---

### Phase 2: Enhanced Reliability (Weeks 3-4)

#### Week 3: Better Error Handling

**Enhanced Retry Logic:**

```python
# ENHANCE: scrapers/base_scraper.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests
from selenium.common.exceptions import TimeoutException

class BaseScraper(ABC):
    # ... existing code ...
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((
            requests.exceptions.RequestException,
            TimeoutException
        ))
    )
    def _get_page_with_retry(self, url, **kwargs):
        """
        Enhanced page fetching with exponential backoff.
        Replaces _get_page for better reliability.
        """
        return self._get_page(url, **kwargs)
```

**Centralized Error Tracking:**

```python
# NEW FILE: utils/error_tracker.py

from collections import defaultdict
from typing import Dict, List
import json

class ErrorTracker:
    """Track and categorize errors across the pipeline."""
    
    def __init__(self):
        self.errors = defaultdict(list)
    
    def record_error(self, board: str, subject: str, 
                    error_type: str, message: str):
        """Record an error occurrence."""
        self.errors[board].append({
            'subject': subject,
            'type': error_type,
            'message': message,
            'count': 1
        })
    
    def get_summary(self) -> Dict:
        """Get error summary by board."""
        summary = {}
        for board, errors in self.errors.items():
            summary[board] = {
                'total': len(errors),
                'by_type': self._group_by_type(errors)
            }
        return summary
    
    def save_report(self, filepath: str):
        """Save error report to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)
```

#### Week 4: Deduplication & Quality

**Pre-Upload Deduplication:**

```python
# ENHANCE: processors/topic_processor.py

from difflib import SequenceMatcher
from typing import List, Dict

class TopicProcessor:
    # ... existing code ...
    
    def deduplicate(self, topics: List[Dict]) -> List[Dict]:
        """
        Remove duplicate topics using fuzzy matching.
        More sophisticated than the current version.
        """
        unique = []
        seen_signatures = set()
        
        for topic in topics:
            # Create a signature for the topic
            signature = self._create_signature(topic)
            
            # Check for exact duplicates
            if signature in seen_signatures:
                logger.debug(f"Skipping exact duplicate: {topic.get('Topic')}")
                continue
            
            # Check for fuzzy duplicates
            is_duplicate = False
            for existing in unique:
                similarity = self._calculate_similarity(topic, existing)
                if similarity > 0.90:  # 90% similar
                    is_duplicate = True
                    logger.debug(f"Skipping fuzzy duplicate: {topic.get('Topic')}")
                    break
            
            if not is_duplicate:
                unique.append(topic)
                seen_signatures.add(signature)
        
        logger.info(f"Deduplication: {len(topics)} → {len(unique)} topics")
        return unique
    
    def _create_signature(self, topic: Dict) -> str:
        """Create unique signature for a topic."""
        return f"{topic.get('Exam Board')}|{topic.get('Subject')}|{topic.get('Topic')}|{topic.get('Sub Topic', '')}"
    
    def _calculate_similarity(self, topic1: Dict, topic2: Dict) -> float:
        """Calculate similarity between two topics."""
        # Must be same board and subject
        if (topic1.get('Exam Board') != topic2.get('Exam Board') or
            topic1.get('Subject') != topic2.get('Subject')):
            return 0.0
        
        # Compare topic names
        name1 = topic1.get('Topic', '').lower()
        name2 = topic2.get('Topic', '').lower()
        
        return SequenceMatcher(None, name1, name2).ratio()
```

---

### Phase 3: Automation & Deployment (Weeks 5-6)

#### Week 5: GitHub Actions Automation

```yaml
# .github/workflows/curriculum-scraper.yml

name: Curriculum Content Pipeline

on:
  schedule:
    # Run on 1st of March and September at 2am UTC
    - cron: '0 2 1 3,9 *'
  workflow_dispatch:  # Allow manual trigger
    inputs:
      boards:
        description: 'Boards to scrape (comma-separated, or "all")'
        required: false
        default: 'all'
      exam_types:
        description: 'Exam types (comma-separated, or "all")'
        required: false
        default: 'all'

jobs:
  scrape-curriculum:
    runs-on: ubuntu-latest
    timeout-minutes: 360  # 6 hours max
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Install Chrome
        uses: browser-actions/setup-chrome@latest
      
      - name: Run pipeline
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          python pipeline.py
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: pipeline-logs
          path: data/logs/
      
      - name: Upload state file
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: pipeline-state
          path: data/pipeline_state_*.json
      
      - name: Send notification on failure
        if: failure()
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: Curriculum Pipeline Failed
          to: ${{ secrets.NOTIFICATION_EMAIL }}
          from: GitHub Actions
          body: |
            The curriculum scraping pipeline failed.
            Run ID: ${{ github.run_id }}
            Check logs for details.
      
      - name: Send success notification
        if: success()
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: Curriculum Pipeline Completed Successfully
          to: ${{ secrets.NOTIFICATION_EMAIL }}
          from: GitHub Actions
          body: |
            The curriculum scraping pipeline completed successfully.
            Run ID: ${{ github.run_id }}
            Check the uploaded artifacts for details.
```

#### Week 6: Monitoring & Documentation

**Add Monitoring Dashboard:**

```python
# NEW FILE: monitoring/dashboard.py

"""
Simple monitoring dashboard for pipeline runs.
Run with: streamlit run monitoring/dashboard.py
"""

import streamlit as st
import json
from pathlib import Path
import pandas as pd

st.title("Curriculum Pipeline Monitor")

# Load recent pipeline states
state_files = sorted(Path("data").glob("pipeline_state_*.json"), reverse=True)[:10]

if not state_files:
    st.warning("No pipeline runs found")
else:
    # Show latest run
    latest = json.loads(state_files[0].read_text())
    
    st.header("Latest Run")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Topics", latest['total_topics_uploaded'])
    col2.metric("Completed Boards", len(latest['completed_boards']))
    col3.metric("Failed Boards", len(latest['failed_boards']))
    
    # Show history
    st.header("Run History")
    history = []
    for f in state_files:
        data = json.loads(f.read_text())
        history.append({
            'Run ID': data['run_id'],
            'Started': data['started_at'],
            'Topics': data['total_topics_uploaded'],
            'Success': len(data['completed_boards']),
            'Failed': len(data['failed_boards'])
        })
    
    df = pd.DataFrame(history)
    st.dataframe(df)
```

---

## International Exam Boards Expansion

### Target International Qualifications (Phase 3)

#### 1. **Cambridge International (Priority 1)**
- **Website:** https://www.cambridgeinternational.org/
- **Qualifications:** 
  - Cambridge IGCSE (International GCSE)
  - Cambridge International AS & A Level
  - Cambridge Pre-U
- **Format:** PDF syllabuses, structured website data
- **Coverage:** 70+ subjects
- **Key Markets:** Asia, Middle East, Africa, Europe
- **Data Quality:** Excellent - very structured specifications

**Implementation Notes:**
- Well-organized syllabus PDFs with clear topic hierarchies
- Consistent URL patterns across subjects
- Good candidate for AI extraction
- Some subjects require login (use public syllabuses only)

#### 2. **International Baccalaureate - IB (Priority 2)**
- **Website:** https://www.ibo.org/
- **Qualifications:**
  - IB Diploma Programme (DP)
  - IB Middle Years Programme (MYP)
  - IB Career-related Programme (CP)
- **Format:** PDF subject guides (some require IB login)
- **Coverage:** 50+ subjects
- **Key Markets:** International schools worldwide
- **Data Quality:** Excellent but access restricted

**Implementation Notes:**
- Subject guides are comprehensive but require IB credentials
- Focus on publicly available subject briefs initially
- Consider partnership with IB schools for full access
- Very structured content ideal for AI extraction

#### 3. **Pearson Edexcel International (Priority 3)**
- **Website:** https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses-and-edexcel-certificates.html
- **Qualifications:**
  - Edexcel International GCSE
  - Edexcel International A Level
- **Format:** PDF specifications
- **Coverage:** 40+ subjects
- **Key Markets:** Similar to Cambridge International
- **Data Quality:** Good - similar to UK Edexcel

**Implementation Notes:**
- Very similar structure to UK Edexcel scraper
- Can leverage existing Edexcel scraper code
- Well-organized specification PDFs
- Good AI extraction candidate

#### 4. **Other International Qualifications (Future)**

##### **Advanced Placement (AP) - USA**
- **Provider:** College Board
- **Website:** https://apstudents.collegeboard.org/
- **Coverage:** 38 subjects
- **Format:** HTML course descriptions, PDF frameworks
- **Market:** US high schools, international schools

##### **Singapore-Cambridge GCE**
- **Provider:** SEAB (Singapore Examinations and Assessment Board)
- **Website:** https://www.seab.gov.sg/
- **Coverage:** ~30 subjects
- **Format:** PDF syllabuses
- **Market:** Singapore schools

##### **Hong Kong HKDSE**
- **Provider:** HKEAA
- **Website:** https://www.hkeaa.edu.hk/
- **Coverage:** Core + elective subjects
- **Format:** PDF syllabuses
- **Market:** Hong Kong schools

### International Scraper Implementation Strategy

#### Building on Existing Foundation

Your existing scrapers provide excellent templates. For international boards:

```python
# NEW FILE: scrapers/international/cambridge_scraper.py

from scrapers.base_scraper import BaseScraper
from ai_helpers.topic_extractor import extract_topics_from_pdf, extract_topics_from_html
from utils.logger import get_logger
import re

logger = get_logger()

class CambridgeScraper(BaseScraper):
    """
    Scraper for Cambridge International Examinations.
    Similar pattern to your existing UK scrapers but adapted for Cambridge.
    """
    
    # Cambridge IGCSE subject URLs
    CAMBRIDGE_IGCSE_SUBJECTS = {
        "Accounting": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-accounting-0452/",
        "Biology": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-biology-0610/",
        "Chemistry": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-chemistry-0620/",
        "Computer Science": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-computer-science-0478/",
        "Economics": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-economics-0455/",
        "Mathematics": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-igcse-mathematics-0580/",
        # ... add all 70+ subjects
    }
    
    # Cambridge International A Level subject URLs
    CAMBRIDGE_A_LEVEL_SUBJECTS = {
        "Biology": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-biology-9700/",
        "Chemistry": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-chemistry-9701/",
        "Mathematics": "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-mathematics-9709/",
        # ... add all subjects
    }
    
    def __init__(self, headless=True, delay=2.0):
        """Initialize Cambridge scraper."""
        super().__init__(
            name="Cambridge International",
            base_url="https://www.cambridgeinternational.org",
            headless=headless,
            delay=delay
        )
    
    def scrape_topics(self, subject=None, exam_type=None):
        """
        Scrape topics from Cambridge International.
        Uses the same pattern as your existing scrapers!
        """
        logger.info(f"Scraping Cambridge topics for {subject} ({exam_type})")
        
        # Get subject URLs based on exam type
        if exam_type and exam_type.lower() == 'igcse':
            subject_urls = self.CAMBRIDGE_IGCSE_SUBJECTS
        elif exam_type and exam_type.lower() in ['a-level', 'as-level']:
            subject_urls = self.CAMBRIDGE_A_LEVEL_SUBJECTS
        else:
            # Combine both
            subject_urls = {**self.CAMBRIDGE_IGCSE_SUBJECTS, **self.CAMBRIDGE_A_LEVEL_SUBJECTS}
        
        # Filter by subject if specified
        if subject:
            subject_urls = {k: v for k, v in subject_urls.items() 
                          if subject.lower() in k.lower()}
        
        all_topics = []
        
        for subj_name, subj_url in subject_urls.items():
            try:
                # Get the syllabus PDF URL
                html = self._get_page(subj_url, use_selenium=True)
                if not html:
                    continue
                
                # Find PDF link
                soup = BeautifulSoup(html, 'lxml')
                pdf_link = soup.find('a', href=re.compile(r'syllabus.*\.pdf', re.I))
                
                if pdf_link:
                    pdf_url = urljoin(self.base_url, pdf_link['href'])
                    
                    # Download PDF
                    pdf_path = self._download_document(
                        pdf_url,
                        f"{subj_name}_syllabus.pdf",
                        "specifications/cambridge"
                    )
                    
                    if pdf_path:
                        # Use AI extraction (same as your existing code!)
                        topics = extract_topics_from_pdf(
                            pdf_path, subj_name, exam_type, "Cambridge International"
                        )
                        all_topics.extend(topics)
                
            except Exception as e:
                logger.error(f"Error scraping {subj_name}: {e}")
                continue
        
        return all_topics
    
    def scrape_papers(self, subject=None, exam_type=None, year_from=2021):
        """Scrape past papers from Cambridge."""
        # Similar implementation to your existing paper scrapers
        pass
```

#### Leveraging Your Existing AI System

Your `ai_helpers/topic_extractor.py` is **excellent** and already supports:
- ✅ Claude API (Anthropic)
- ✅ Gemini API (Google)
- ✅ PDF extraction
- ✅ HTML extraction
- ✅ Structured JSON output

**This works perfectly for international boards too!** No changes needed - just point it at Cambridge/IB PDFs.

### International Expansion Roadmap

#### Phase 3A: Cambridge International (Weeks 7-8)

**Priority:** High - largest international market

**Week 7:**
- [ ] Create `scrapers/international/cambridge_scraper.py`
- [ ] Map all IGCSE subject URLs (~70 subjects)
- [ ] Map all Cambridge A-Level URLs (~40 subjects)
- [ ] Test with 5 subjects (Math, Biology, Chemistry, Physics, English)

**Week 8:**
- [ ] Run full scrape for Cambridge IGCSE
- [ ] Run full scrape for Cambridge A-Level
- [ ] Process and validate data
- [ ] Upload to Supabase
- [ ] Verify coverage (target: 90%+ of subjects)

**Expected Output:** ~15,000-20,000 additional topics

#### Phase 3B: International Baccalaureate (Weeks 9-10)

**Priority:** High - premium market

**Challenges:**
- Some content requires IB login
- Focus on publicly available subject briefs
- Consider partnership with IB schools

**Week 9:**
- [ ] Create `scrapers/international/ib_scraper.py`
- [ ] Map public subject brief URLs
- [ ] Test PDF extraction with IB guides
- [ ] Build fallback topic structures for restricted content

**Week 10:**
- [ ] Run scrape for all accessible subjects
- [ ] Manual supplementation for restricted subjects
- [ ] Upload to Supabase
- [ ] Document access limitations

**Expected Output:** ~5,000-8,000 topics (limited by access)

#### Phase 3C: Edexcel International (Week 11)

**Priority:** Medium - similar to UK Edexcel

**Week 11:**
- [ ] Adapt existing `edexcel_scraper.py` for international
- [ ] Map Edexcel International subject URLs
- [ ] Run scrape (should be quick - similar structure)
- [ ] Upload to Supabase

**Expected Output:** ~8,000-10,000 topics

### Coverage Targets

| Qualification Type | Subjects | Est. Topics | Priority | Weeks |
|-------------------|----------|-------------|----------|-------|
| UK GCSE (6 boards) | 40-50 each | ~30,000 | ✅ Done | - |
| UK A-Level (6 boards) | 30-40 each | ~25,000 | ✅ Done | - |
| Cambridge IGCSE | 70+ | 15,000-20,000 | High | 7-8 |
| Cambridge A-Level | 40+ | 10,000-15,000 | High | 7-8 |
| IB Diploma | 50+ | 5,000-8,000 | High | 9-10 |
| Edexcel International | 40+ | 8,000-10,000 | Medium | 11 |
| AP (USA) | 38 | 5,000-7,000 | Low | Future |
| **TOTAL** | **~350-400** | **~98,000-125,000** | | |

---

## Migration Guide

### Step-by-Step Transition from Current System

#### Step 1: Backup Current System
```bash
# Create backup of existing system
cd "Topic List Scraper"
git init  # If not already a git repo
git add .
git commit -m "Backup before v2 migration"
git tag v1-backup
```

#### Step 2: Set Up New Structure
```bash
# Create new directories
mkdir -p database
mkdir -p monitoring
mkdir -p .github/workflows

# Copy existing files that we're keeping
cp scrapers/* ../new-pipeline/scrapers/
cp ai_helpers/* ../new-pipeline/ai_helpers/
cp utils/* ../new-pipeline/utils/
cp processors/* ../new-pipeline/processors/
```

#### Step 3: Add New Components
```bash
# Create new files
touch pipeline.py
touch database/supabase_uploader.py
touch monitoring/dashboard.py
touch .github/workflows/curriculum-scraper.yml
```

#### Step 4: Update Environment Variables
```bash
# .env file - ADD these new variables
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# REMOVE these (no longer needed)
# KNACK_APP_ID=...
# KNACK_API_KEY=...
```

#### Step 5: Test Migration
```bash
# Test with single board first
python pipeline.py --boards AQA --exam-types gcse --test-mode

# If successful, run full pipeline
python pipeline.py
```

---

## Updated File Structure

```
flash-curriculum-pipeline-v2/
├── scrapers/                    # KEEP & EXPAND
│   ├── __init__.py
│   ├── base_scraper.py         # ENHANCE with retry logic
│   │
│   ├── uk/                     # UK Exam Boards (EXISTING)
│   │   ├── aqa_scraper.py          # KEEP
│   │   ├── edexcel_scraper.py      # KEEP
│   │   ├── ocr_scraper.py          # KEEP
│   │   ├── wjec_scraper.py         # KEEP
│   │   ├── ccea_scraper.py         # KEEP
│   │   └── sqa_scraper.py          # KEEP
│   │
│   └── international/          # International (NEW)
│       ├── cambridge_scraper.py    # Cambridge International
│       ├── ib_scraper.py          # International Baccalaureate
│       ├── edexcel_intl_scraper.py # Edexcel International
│       └── caie_scraper.py        # Cambridge Assessment International
│
├── ai_helpers/                  # KEEP from existing
│   ├── __init__.py
│   └── topic_extractor.py      # KEEP (works great!)
│
├── processors/                  # ENHANCE from existing
│   ├── __init__.py
│   └── topic_processor.py      # ENHANCE with better deduplication
│
├── database/                    # NEW (replaces knack/)
│   ├── __init__.py
│   ├── supabase_uploader.py    # NEW
│   └── schema_migrations/      # NEW
│       └── add_versioning.sql
│
├── utils/                       # KEEP & ENHANCE
│   ├── __init__.py
│   ├── logger.py               # KEEP
│   ├── helpers.py              # KEEP
│   ├── subjects.py             # KEEP
│   └── error_tracker.py        # NEW
│
├── monitoring/                  # NEW
│   ├── __init__.py
│   └── dashboard.py            # NEW
│
├── data/                        # KEEP structure
│   ├── raw/                    # Existing scraped data
│   ├── processed/              # Processed topics
│   ├── logs/                   # Log files
│   └── pipeline_state_*.json   # NEW - state files
│
├── .github/
│   └── workflows/
│       └── curriculum-scraper.yml  # NEW
│
├── pipeline.py                  # NEW - main entry point
├── requirements.txt             # UPDATE
├── .env.example                 # UPDATE
├── README.md                    # UPDATE
└── MIGRATION-GUIDE.md          # NEW

# REMOVE (no longer needed):
├── knack/                       # DELETE - replaced by database/
├── main.py                      # DELETE - replaced by pipeline.py
└── test_*.py                    # ARCHIVE - keep for reference
```

---

## Key Improvements Summary

### 1. **Unified Execution** ✨
- Single `pipeline.py` instead of running each board separately
- Automatic orchestration of all scrapers
- Progress tracking with state files

### 2. **Better Reliability** ✨
- Enhanced retry logic with exponential backoff
- Graceful error handling (one failure doesn't break everything)
- Resume capability if pipeline fails mid-run
- Centralized error tracking

### 3. **Direct Supabase Integration** ✨
- Batch upserts for performance
- Automatic deduplication via unique constraints
- Proper schema mapping
- No intermediate database

### 4. **Improved Data Quality** ✨
- Pre-upload validation
- Fuzzy deduplication
- Quality scoring
- Better normalization

### 5. **Full Automation** ✨
- GitHub Actions runs every 6 months
- Email notifications on completion/failure
- Manual trigger available
- Automated deployment

### 6. **Maintainability** ✨
- Clear separation of concerns
- Well-documented code
- Monitoring dashboard
- Migration guide

---

## Timeline & Effort Estimate

### Conservative Timeline (6 weeks)

| Week | Focus | Hours | Deliverable |
|------|-------|-------|-------------|
| 1 | Supabase integration | 20-25 | Working uploader |
| 2 | Unified orchestrator | 20-25 | Single pipeline |
| 3 | Error handling | 15-20 | Reliable execution |
| 4 | Deduplication & quality | 15-20 | Clean data |
| 5 | GitHub Actions | 10-15 | Automated runs |
| 6 | Monitoring & docs | 10-15 | Production ready |
| **Total** | | **90-120 hours** | **Production pipeline** |

### Aggressive Timeline (3-4 weeks)

Focus on essentials:
- Week 1-2: Supabase + Pipeline
- Week 3: Error handling + Quality
- Week 4: Automation + Deploy

**Total: 50-60 hours**

---

## Testing Strategy

### Unit Tests
```python
# tests/test_supabase_uploader.py
def test_transform_topic():
    """Test topic transformation to Supabase schema."""
    uploader = SupabaseUploader(url, key)
    topic = {
        "Exam Board": "AQA",
        "Exam Type": "GCSE",
        "Subject": "Mathematics",
        "Module": "Number",
        "Topic": "Fractions"
    }
    transformed = uploader._transform_topic(topic)
    assert transformed['exam_board'] == "AQA"
    assert transformed['topic_level'] == 1
```

### Integration Tests
```python
# tests/test_pipeline.py
def test_pipeline_single_board():
    """Test pipeline with single board."""
    config = {...}
    pipeline = CurriculumPipeline(config)
    pipeline.run(boards=['AQA'], exam_types=['gcse'])
    assert len(pipeline.state.completed_boards) == 1
```

### End-to-End Test
```bash
# Run with test flag (doesn't upload to production)
python pipeline.py --test-mode --boards AQA --exam-types gcse
```

---

## Success Metrics

### Phase 1 Success Criteria
- ✅ Supabase uploader working
- ✅ At least 1 board successfully migrated
- ✅ Data quality matches or exceeds current system
- ✅ Upload performance < 10 seconds per 100 topics

### Phase 2 Success Criteria
- ✅ All 6 UK boards working through unified pipeline
- ✅ < 5% failure rate for individual scrapes
- ✅ Automatic recovery from transient failures
- ✅ Deduplication reduces duplicates by 95%+

### Phase 3 Success Criteria
- ✅ GitHub Actions running successfully
- ✅ Notifications working
- ✅ Monitoring dashboard functional
- ✅ Complete documentation

---

## Cost Analysis

### Development Costs

| Phase | If DIY | If Outsourced |
|-------|--------|---------------|
| Phase 1 | 40-50 hours | £2,000-3,000 |
| Phase 2 | 30-40 hours | £1,500-2,000 |
| Phase 3 | 20-30 hours | £1,000-1,500 |
| **Total** | **90-120 hours** | **£4,500-6,500** |

### Ongoing Costs

| Item | Cost |
|------|------|
| GitHub Actions (free tier) | £0/year |
| Supabase (existing) | £0 (included) |
| Email notifications | £0 (Gmail) |
| Maintenance (quarterly check) | 4 hours/year |

**Total ongoing:** ~£800/year if outsourced (£50/hour × 4 hours × 4 quarters)

---

## Complete Implementation Roadmap

### Phase 1: Refactor UK Boards (Weeks 1-2)

**Goal:** Migrate existing system to Supabase with unified pipeline

#### Week 1: Supabase Integration
**Day 1-2: Environment Setup**
- [ ] Create new branch: `pipeline-v2`
- [ ] Set up Supabase service key in environment
- [ ] Add `supabase-py` to requirements.txt
- [ ] Test Supabase connection
- [ ] Review and update database schema

**Day 3-5: Build Supabase Uploader**
- [ ] Create `database/supabase_uploader.py`
- [ ] Map scraper format to Supabase schema
- [ ] Implement batch upsert logic
- [ ] Add deduplication via unique constraints
- [ ] Write unit tests

**Day 6-7: First Integration Test**
- [ ] Test uploader with existing AQA data
- [ ] Verify data appears correctly in Supabase
- [ ] Test deduplication works
- [ ] Document any schema issues

#### Week 2: Unified Orchestrator
**Day 8-10: Create Pipeline**
- [ ] Create `pipeline.py` orchestrator
- [ ] Add state management for resumability
- [ ] Integrate all 6 UK board scrapers
- [ ] Add progress tracking

**Day 11-12: Enhanced Error Handling**
- [ ] Add retry logic with exponential backoff
- [ ] Add error categorization
- [ ] Test failure scenarios
- [ ] Ensure graceful degradation

**Day 13-14: First Complete UK Run**
- [ ] Run full pipeline for all UK boards
- [ ] Monitor for errors
- [ ] Compare data quality with current system
- [ ] Fix critical issues

**Deliverable:** Working pipeline for all UK exam boards → Supabase

---

### Phase 2: Quality & Automation (Weeks 3-4)

**Goal:** Production-ready pipeline with automation

#### Week 3: Data Quality
**Day 1-3: Advanced Processing**
- [ ] Enhance deduplication algorithm (fuzzy matching)
- [ ] Add data quality scoring
- [ ] Implement validation rules
- [ ] Create quality report generator

**Day 4-5: Change Detection**
- [ ] Add data versioning to schema
- [ ] Implement change detection
- [ ] Create diff reports for curriculum updates
- [ ] Test with historical data

**Day 6-7: Manual Review Interface**
- [ ] Build simple web UI for reviewing flagged topics
- [ ] Add approve/reject workflow
- [ ] Connect to staging database
- [ ] Test review process

#### Week 4: Automation & Deployment
**Day 1-3: GitHub Actions**
- [ ] Create GitHub Actions workflow
- [ ] Add scheduling (every 6 months)
- [ ] Add manual trigger option
- [ ] Test workflow in GitHub

**Day 4-5: Monitoring**
- [ ] Create monitoring dashboard
- [ ] Add email notifications
- [ ] Set up logging aggregation
- [ ] Create runbooks for common issues

**Day 6-7: Documentation & Handover**
- [ ] Document complete pipeline
- [ ] Create operator's guide
- [ ] Write troubleshooting guide
- [ ] Create maintenance schedule

**Deliverable:** Fully automated, production-ready UK pipeline

---

### Phase 3: International Expansion (Weeks 5-8)

**Goal:** Add Cambridge, IB, and Edexcel International

#### Week 5: Cambridge International IGCSE
**Day 1-2: Setup**
- [ ] Create `scrapers/international/cambridge_scraper.py`
- [ ] Map all IGCSE subject URLs (70+ subjects)
- [ ] Identify PDF download patterns
- [ ] Test manual extraction for 3 subjects

**Day 3-5: Implementation**
- [ ] Implement scrape_topics method
- [ ] Leverage existing AI extraction
- [ ] Test with 10 subjects
- [ ] Fix any issues

**Day 6-7: Full IGCSE Scrape**
- [ ] Run complete IGCSE scrape
- [ ] Process and validate
- [ ] Upload to Supabase
- [ ] Verify coverage

**Deliverable:** ~15,000 Cambridge IGCSE topics in database

#### Week 6: Cambridge A-Level
**Day 1-3: A-Level Implementation**
- [ ] Map Cambridge A-Level URLs (40+ subjects)
- [ ] Adapt scraper for A-Level format
- [ ] Test with 10 subjects

**Day 4-7: Full A-Level Scrape**
- [ ] Run complete A-Level scrape
- [ ] Process and validate
- [ ] Upload to Supabase
- [ ] Integration testing with app

**Deliverable:** ~10,000 Cambridge A-Level topics

#### Week 7: International Baccalaureate
**Day 1-2: IB Research**
- [ ] Map publicly accessible IB resources
- [ ] Identify login-required content
- [ ] Document access restrictions
- [ ] Create subject URL map

**Day 3-5: IB Scraper**
- [ ] Create `scrapers/international/ib_scraper.py`
- [ ] Focus on public subject briefs
- [ ] Build fallback structures for restricted content
- [ ] Test with accessible subjects

**Day 6-7: IB Data Collection**
- [ ] Scrape all accessible IB content
- [ ] Supplement with manual data entry for key subjects
- [ ] Upload to Supabase
- [ ] Document coverage gaps

**Deliverable:** ~5,000-8,000 IB topics (with known limitations)

#### Week 8: Edexcel International + Testing
**Day 1-3: Edexcel International**
- [ ] Adapt existing Edexcel scraper
- [ ] Map International IGCSE URLs
- [ ] Run scrape
- [ ] Upload to Supabase

**Day 4-7: Comprehensive Testing**
- [ ] Test app with new international data
- [ ] Verify AI card generation works with international curricula
- [ ] Fix any integration issues
- [ ] Update app UI to show international options

**Deliverable:** ~8,000 Edexcel International topics + tested app integration

---

### Phase 4: Future Expansions (Weeks 9+)

#### Additional International Qualifications (As Needed)

**Advanced Placement (AP) - USA Market**
- Week 9-10: Build AP scraper
- Expected: 5,000-7,000 topics
- Market: US + international schools

**Singapore-Cambridge GCE**
- Week 11: Build Singapore scraper
- Expected: 3,000-5,000 topics
- Market: Singapore schools

**Other Countries (Future)**
- Australia (VCAA, HSC)
- Ireland (Leaving Certificate)
- South Africa (NSC)
- India (CBSE, ICSE)

### International Coverage Summary

After Phase 3 completion, FLASH will have:

| Region | Qualifications | Topics | Status |
|--------|---------------|--------|--------|
| UK | GCSE, A-Level (6 boards) | ~55,000 | ✅ Complete |
| International | Cambridge IGCSE/A-Level | ~25,000 | Week 5-6 |
| International | IB Diploma | ~6,000 | Week 7 |
| International | Edexcel International | ~8,000 | Week 8 |
| USA | AP (future) | ~6,000 | Future |
| **TOTAL** | **~12 qualification types** | **~100,000** | **8 weeks** |

This positions FLASH as a **truly international** study app, not just UK-focused!

---

## Immediate Next Steps (Parallel to App Beta)

### Week 1 (Oct 1-7): Research & Setup
**Day 1 (Today):**
- [ ] Review both strategy documents
- [ ] Decide on timeline (3-4 weeks vs 6 weeks)
- [ ] Create new git branch in Topic List Scraper
- [ ] Set up Supabase service key

**Day 2-3:**
- [ ] Research Cambridge International website structure
- [ ] Research IB public resources
- [ ] Document URL patterns
- [ ] Test manual PDF downloads

**Day 4-5:**
- [ ] Create `database/supabase_uploader.py`
- [ ] Test connection to Supabase
- [ ] Test with existing AQA data

**Day 6-7:**
- [ ] Create basic `pipeline.py`
- [ ] Test with single board (AQA)
- [ ] Document findings

### Week 2 (Oct 8-14): Build & Test
**Day 8-10:**
- [ ] Integrate all UK scrapers
- [ ] Test each board individually
- [ ] Fix integration issues

**Day 11-14:**
- [ ] Run complete UK pipeline
- [ ] Compare with existing data
- [ ] Make go/no-go decision for Phase 2

**Deliverable:** Working UK pipeline ready for automation

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scraper failures | Medium | Enhanced retry logic, resume capability |
| API rate limits | Medium | Rate limiting, exponential backoff |
| Data quality issues | High | Validation layer, manual review process |
| Supabase schema mismatch | High | Thorough testing, migration scripts |

### Business Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Website changes | High | Version scrapers, fallback to AI extraction |
| API costs (Claude/Gemini) | Medium | Cache results, use cheaper models |
| Time overrun | Medium | Phased approach, MVP first |

---

## Conclusion

This comprehensive pipeline strategy:

1. **Builds on your existing work** - Leverages 357 log files worth of learning, proven scrapers
2. **Fixes the pain points** - Unified execution, better errors, Supabase direct
3. **Keeps what works** - AI extraction (excellent!), base architecture, organized structure
4. **Expands internationally** - Cambridge, IB, Edexcel International, future AP
5. **Adds automation** - GitHub Actions, monitoring, notifications
6. **Is scalable** - Clear path from 55,000 topics to 100,000+ topics
7. **Is maintainable** - Clear code, good docs, easy to extend

### Complete Timeline Overview

| Phase | Focus | Duration | Output |
|-------|-------|----------|--------|
| 1 | Refactor UK boards | 2 weeks | Unified pipeline + Supabase |
| 2 | Quality & automation | 2 weeks | Production-ready UK system |
| 3 | International expansion | 4 weeks | Cambridge, IB, Edexcel Intl |
| 4 | Future expansions | Ongoing | AP, other countries |
| **Total to International Coverage** | | **8 weeks** | **~100,000 topics** |

### Parallel with App Development

**Weeks 1-2 (During App Beta Launch):**
- Work on Pipeline Phase 1 (Supabase integration)
- This won't block your app launch
- You can test with existing data

**Weeks 3-4 (After App Beta Deployed):**
- Complete Pipeline Phase 2 (automation)
- UK content refreshed and validated

**Weeks 5-8 (While gathering beta feedback):**
- Add international boards
- Expand your market reach
- Differentiate from UK-only competitors

### Competitive Advantage

With 100,000+ topics covering:
- ✅ All UK exam boards (6)
- ✅ Cambridge International (IGCSE + A-Level)
- ✅ International Baccalaureate
- ✅ Edexcel International

FLASH becomes the **most comprehensive** exam-focused flashcard app globally, not just UK!

---

## Estimated Costs

### Development (DIY)
- **Phase 1-2:** 80-100 hours (£4,000-5,000 outsourced)
- **Phase 3:** 60-80 hours (£3,000-4,000 outsourced)
- **Total:** 140-180 hours (£7,000-9,000 outsourced)

### Development (Recommended Hybrid)
- **You do:** Phase 1 setup + oversight (30 hours)
- **Outsource:** Scraper development (£3,000-4,000)
- **You do:** Integration + testing (20 hours)
- **Total:** 50 hours + £3,000-4,000

### Ongoing (Annual)
- GitHub Actions: £0 (free tier)
- Maintenance: 16 hours/year (quarterly checks)
- API costs: £100-200/year (Claude/Gemini for new content)

---

## Success Metrics

### Phase 1 (UK Refactor)
- ✅ All 6 UK boards running through unified pipeline
- ✅ < 10% failure rate on individual subject scrapes
- ✅ Duplicate rate < 5%
- ✅ Upload speed > 100 topics/minute
- ✅ Resume works after failure

### Phase 2 (Automation)
- ✅ GitHub Actions runs successfully
- ✅ Email notifications working
- ✅ Monitoring dashboard shows real data
- ✅ Documentation complete

### Phase 3 (International)
- ✅ Cambridge International: 20,000+ topics
- ✅ IB: 5,000+ topics (with known access limits)
- ✅ Edexcel International: 8,000+ topics
- ✅ App successfully shows international options
- ✅ AI card generation works with international curricula

### Overall Success
- ✅ Total topics: 90,000-100,000+
- ✅ Coverage: UK + 3 major international boards
- ✅ Update frequency: Automated every 6 months
- ✅ Quality: >95% valid topics
- ✅ Performance: Full run completes in < 4 hours

---

**Next Actions:**
1. Review this comprehensive strategy
2. Decide on timeline commitment:
   - **Fast track:** 4 weeks to UK complete
   - **Full track:** 8 weeks to international coverage
3. Start Phase 1, Day 1 (create git branch, set up Supabase)
4. Schedule check-ins:
   - After Week 1: Supabase uploader working
   - After Week 2: UK pipeline complete
   - After Week 4: Ready for automation
   - After Week 8: International coverage complete

**You're building something comprehensive here** - not just a UK study app, but a global education platform! 🌍

*Ready to start Phase 1?*
