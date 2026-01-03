"""
Organize Topics by Classification Numbers
Parses topic titles to determine hierarchy from numbering
"""

import re


def organize_topics_by_numbers(flat_topics: list) -> list:
    """
    Takes flat list of topics and organizes into hierarchy
    based on classification numbers in titles.
    
    Examples:
    - "3.1.1 Applied anatomy" → Level 1
    - "Cardiovascular drift" → Level 2 (child of previous 3.1.1)
    - "3.1.1.1 Cardio-respiratory system" → Level 2
    
    Returns list with proper level and parent_code assignments.
    """
    
    organized = []
    current_parent = None  # Track current parent for unnumbered topics
    
    for topic in flat_topics:
        title = topic.get('title', '')
        
        # Check for classification number patterns
        # Level 1: "3.1.1 Applied anatomy"
        level_1_match = re.match(r'^(\d+\.\d+\.\d+)\s+(.+)$', title)
        
        # Level 2: "3.1.1.1 Cardio-respiratory system"  
        level_2_match = re.match(r'^(\d+\.\d+\.\d+\.\d+)\s+(.+)$', title)
        
        if level_2_match:
            # Has 4-part number (3.1.1.1) → Level 2
            code = level_2_match.group(1)
            clean_title = level_2_match.group(2)
            parent_code = '.'.join(code.split('.')[:3])  # 3.1.1
            
            organized.append({
                **topic,
                'code': code,
                'title': clean_title,
                'level': 2,
                'parent_code': parent_code
            })
            current_parent = code
            
        elif level_1_match:
            # Has 3-part number (3.1.1) → Level 1
            code = level_1_match.group(1)
            clean_title = level_1_match.group(2)
            parent_code = '.'.join(code.split('.')[:2])  # 3.1
            
            organized.append({
                **topic,
                'code': code,
                'title': clean_title,
                'level': 1,
                'parent_code': parent_code
            })
            current_parent = code
            
        else:
            # No number → Child of previous numbered topic
            # These become Level 2 or Level 3 depending on parent
            if current_parent:
                # Determine level based on parent
                parent_level = current_parent.count('.')
                child_level = min(parent_level + 1, 3)  # Max Level 3
                
                # Generate code
                child_idx = len([t for t in organized if t.get('parent_code') == current_parent]) + 1
                code = f"{current_parent}.{child_idx}"
                
                organized.append({
                    **topic,
                    'code': code,
                    'title': title,
                    'level': child_level,
                    'parent_code': current_parent
                })
            else:
                # No parent yet - treat as Level 0
                organized.append({
                    **topic,
                    'code': title[:20],  # Use title as code
                    'level': 0,
                    'parent_code': None
                })
    
    return organized


if __name__ == '__main__':
    # Test with sample PE data
    flat_topics = [
        {'title': '3.1.1 Applied anatomy and physiology'},
        {'title': 'Cardiovascular drift'},
        {'title': 'Venous return'},
        {'title': '3.1.2 Skill acquisition'},
        {'title': 'Characteristics of skill'},
        {'title': 'Use of skill continua'},
        {'title': '3.2.1 Exercise physiology'},
        {'title': 'Nutrition'},
        {'title': 'Training principles'}
    ]
    
    organized = organize_topics_by_numbers(flat_topics)
    
    print("ORGANIZED TOPICS:")
    print("=" * 80)
    
    for t in organized:
        indent = "  " * t['level']
        print(f"{indent}L{t['level']}: {t['code']} - {t['title']} (parent: {t.get('parent_code', 'None')})")
    
    # Count by level
    from collections import Counter
    by_level = Counter(t['level'] for t in organized)
    
    print("\n" + "=" * 80)
    print(f"By level: {dict(by_level)}")
    print("=" * 80)




















