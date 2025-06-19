#!/usr/bin/env python3
"""
ATLAS Consciousness Insight Capture
Quick utility for capturing engineering insights, breakthrough moments, and decision patterns
Usage: python3 atlas_insight.py [type] [insight]
"""

import sys
import json
from datetime import datetime
from atlas_integration import atlas

def capture_insight(insight_type: str, content: str):
    """Capture different types of engineering insights"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    insight_templates = {
        'breakthrough': {
            'title': f'Engineering Breakthrough - {timestamp}',
            'log_category': 'breakthrough_insights',
            'work_activity': 'Engineering Breakthrough',
            'knowledge_insight': f'''
### Engineering Breakthrough
- **Discovery**: {content}
- **Context**: {insight_type.title()} moment
- **Timestamp**: {timestamp}
- **Impact**: Potential to improve development speed and quality
- **Next Action**: Validate and integrate into standard practices
'''
        },
        
        'pattern': {
            'title': f'Pattern Recognition - {timestamp}',
            'log_category': 'engineering_patterns',
            'work_activity': 'Pattern Recognition',
            'knowledge_insight': f'''
### Development Pattern Identified
- **Pattern**: {content}
- **Recognition Date**: {timestamp}
- **Application**: Can be applied to future similar situations
- **Documentation**: Adding to engineering knowledge base
'''
        },
        
        'decision': {
            'title': f'Technical Decision - {timestamp}',
            'log_category': 'technical_decisions',
            'work_activity': 'Technical Decision Documented',
            'knowledge_insight': f'''
### Technical Decision Framework Applied
- **Decision Context**: {content}
- **Framework**: ATLAS Decision Analysis
- **Timestamp**: {timestamp}
- **Reasoning**: Documented for future reference
- **Review**: Schedule follow-up to assess outcome
'''
        },
        
        'problem': {
            'title': f'Problem Solving - {timestamp}',
            'log_category': 'problem_solving',
            'work_activity': 'Problem Solving Session',
            'knowledge_insight': f'''
### Problem Solving Approach
- **Problem & Solution**: {content}
- **Solved**: {timestamp}
- **Approach**: Document methodology for similar future problems
- **Time Investment**: Track for process improvement
'''
        },
        
        'learning': {
            'title': f'Learning Insight - {timestamp}',
            'log_category': 'learning_insights',
            'work_activity': 'Learning Documented',
            'knowledge_insight': f'''
### Learning Insight
- **Insight**: {content}
- **Learned**: {timestamp}
- **Application**: Integrate into development practices
- **Knowledge Type**: Technical understanding enhancement
'''
        }
    }
    
    if insight_type not in insight_templates:
        # Default template for unknown types
        template = {
            'title': f'{insight_type.title()} - {timestamp}',
            'log_category': 'general_insights',
            'work_activity': f'{insight_type.title()} Captured',
            'knowledge_insight': f'''
### {insight_type.title()}
- **Content**: {content}
- **Captured**: {timestamp}
- **Type**: {insight_type}
'''
        }
    else:
        template = insight_templates[insight_type]
    
    # Log to working activity
    atlas.memory.log_work_activity(
        template['work_activity'],
        {
            'Type': insight_type.title(),
            'Content': content[:100] + '...' if len(content) > 100 else content,
            'Full Documentation': 'Added to knowledge log',
            'Capture Method': 'ATLAS Insight Tool'
        }
    )
    
    # Add to knowledge log
    atlas.memory.update_knowledge_log(
        template['log_category'],
        template['knowledge_insight']
    )
    
    print(f"✅ {template['work_activity']} captured successfully!")
    print(f"📝 Logged to: {template['log_category']}")
    print(f"🧠 Added to ATLAS consciousness system")

def interactive_mode():
    """Interactive mode for capturing insights"""
    print("🧠 ATLAS Consciousness Insight Capture")
    print("=====================================")
    print()
    print("Available insight types:")
    print("  breakthrough - Major technical discoveries")
    print("  pattern      - Recurring development patterns")
    print("  decision     - Technical decision documentation")
    print("  problem      - Problem-solving approaches")
    print("  learning     - New technical insights")
    print("  custom       - Custom insight type")
    print()
    
    insight_type = input("Enter insight type: ").strip().lower()
    if not insight_type:
        print("❌ Insight type required")
        return
    
    print()
    content = input("Enter your insight (can be multi-line, press Enter twice to finish):\n")
    
    # Allow multi-line input
    lines = [content]
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    full_content = "\n".join(lines).strip()
    
    if not full_content:
        print("❌ Content required")
        return
    
    capture_insight(insight_type, full_content)

def main():
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_mode()
    elif len(sys.argv) == 3:
        # Command line mode
        insight_type = sys.argv[1].lower()
        content = sys.argv[2]
        capture_insight(insight_type, content)
    else:
        print("Usage:")
        print("  python3 atlas_insight.py                    # Interactive mode")
        print("  python3 atlas_insight.py [type] [content]   # Command line mode")
        print()
        print("Example:")
        print('  python3 atlas_insight.py breakthrough "Found that caching email headers speeds up classification by 40%"')
        print('  python3 atlas_insight.py pattern "Debug sessions are most effective when starting with logging at boundaries"')

if __name__ == "__main__":
    main()
