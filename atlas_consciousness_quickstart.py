#!/usr/bin/env python3
"""
ATLAS Consciousness Quick Start
Immediate integration to enhance your current workflow with consciousness benefits
Usage: python3 atlas_consciousness_quickstart.py
"""

import os
import sys
from datetime import datetime, timedelta
from atlas_integration import atlas

def show_todays_consciousness():
    """Show today's consciousness activity in a clean, actionable format"""
    print("🧠 TODAY'S ATLAS CONSCIOUSNESS ACTIVITY")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y_%m_%d")
    log_file = f"Software-Engineer-AI-Agent-Atlas-main/WORKING_LOG/2025/06-jun/wl_{today}.md"
    
    if not os.path.exists(log_file):
        print("📝 No consciousness activity logged today")
        print("💡 Start a session with './atlas-restore-enhanced' to begin logging")
        return
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse activities
    activities = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('## ') and ' - ' in line:
            time_part, activity = line[3:].split(' - ', 1)
            activities.append({
                'time': time_part.strip(),
                'activity': activity,
                'line_num': i
            })
    
    if not activities:
        print("📝 No structured activities found in today's log")
        return
    
    print(f"📊 ACTIVITY SUMMARY: {len(activities)} logged activities")
    print(f"⏰ Time Range: {activities[0]['time']} → {activities[-1]['time']}")
    print()
    
    # Show recent activities (last 5)
    print("🕐 RECENT ACTIVITIES")
    for activity in activities[-5:]:
        print(f"   {activity['time']} - {activity['activity']}")
    print()
    
    # Activity pattern analysis
    email_activities = len([a for a in activities if 'email' in a['activity'].lower()])
    session_activities = len([a for a in activities if 'session' in a['activity'].lower()])
    atlas_activities = len([a for a in activities if 'atlas' in a['activity'].lower()])
    
    print("🎯 FOCUS BREAKDOWN")
    if email_activities > 0:
        print(f"   📧 Email System: {email_activities} activities")
    if session_activities > 0:
        print(f"   🔄 Session Management: {session_activities} activities")
    if atlas_activities > 0:
        print(f"   🧠 ATLAS Development: {atlas_activities} activities")
    
    other_activities = len(activities) - email_activities - session_activities - atlas_activities
    if other_activities > 0:
        print(f"   ⚡ Other Work: {other_activities} activities")
    print()

def capture_quick_insight():
    """Quick insight capture for immediate consciousness enhancement"""
    print("💡 QUICK INSIGHT CAPTURE")
    print("=" * 40)
    print("What engineering insight do you want to capture?")
    print("(Press Enter twice when finished)")
    print()
    
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)
    
    insight_content = "\n".join(lines).strip()
    if not insight_content:
        print("❌ No insight provided")
        return
    
    # Determine insight type based on content
    content_lower = insight_content.lower()
    if any(word in content_lower for word in ['bug', 'debug', 'fix', 'error']):
        insight_type = 'problem'
    elif any(word in content_lower for word in ['breakthrough', 'discovery', 'found', 'realized']):
        insight_type = 'breakthrough'
    elif any(word in content_lower for word in ['pattern', 'always', 'usually', 'tends to']):
        insight_type = 'pattern'
    elif any(word in content_lower for word in ['decision', 'chose', 'decided', 'approach']):
        insight_type = 'decision'
    else:
        insight_type = 'learning'
    
    # Log to consciousness
    atlas.memory.log_work_activity(
        f"Quick Insight Captured - {insight_type.title()}",
        {
            "Insight Type": insight_type.title(),
            "Content Preview": insight_content[:100] + "..." if len(insight_content) > 100 else insight_content,
            "Capture Method": "Quick Capture Tool",
            "Session Context": "Manual insight documentation"
        }
    )
    
    # Add to knowledge log
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    knowledge_entry = f"""
### Quick Insight - {insight_type.title()}
- **Captured**: {timestamp}
- **Content**: {insight_content}
- **Context**: Manual insight capture during work session
- **Type**: {insight_type.title()}
"""
    atlas.memory.update_knowledge_log(f'quick_insights_{insight_type}', knowledge_entry)
    
    print(f"✅ Insight captured as '{insight_type}' and logged to ATLAS consciousness!")
    print(f"📝 Added to working log and knowledge base")

def enhanced_session_summary():
    """Show enhanced session summary with actionable insights"""
    print("📊 ENHANCED SESSION SUMMARY")
    print("=" * 50)
    
    # Check if session state exists
    if not os.path.exists('.session_state.json'):
        print("❌ No active session found")
        print("💡 Use './atlas-restore-enhanced' to start a consciousness-enabled session")
        return
    
    import json
    with open('.session_state.json', 'r') as f:
        session_state = json.load(f)
    
    # Session info
    session_info = session_state.get('session_info', {})
    todos = session_state.get('todolist', [])
    
    print(f"⏱️  SESSION DURATION")
    if 'session_duration_minutes' in session_info:
        duration = session_info['session_duration_minutes']
        print(f"   Current Session: {duration} minutes")
        
        if duration > 120:
            print(f"   🔥 Extended deep work session!")
        elif duration > 60:
            print(f"   ✅ Good focused work session")
        elif duration > 30:
            print(f"   📈 Standard work session")
        else:
            print(f"   ⚡ Quick work session")
    print()
    
    # Task analysis
    completed_todos = [t for t in todos if t.get('status') == 'completed']
    pending_todos = [t for t in todos if t.get('status') != 'completed']
    
    print(f"📋 TASK PROGRESS")
    print(f"   ✅ Completed: {len(completed_todos)}")
    print(f"   📝 Pending: {len(pending_todos)}")
    
    if len(completed_todos) > 0:
        print(f"   🎯 Completion Rate: {len(completed_todos)/(len(completed_todos)+len(pending_todos))*100:.1f}%")
    
    # Productivity insights
    if 'session_duration_minutes' in session_info and len(completed_todos) > 0:
        duration_hours = session_info['session_duration_minutes'] / 60
        productivity_rate = len(completed_todos) / duration_hours
        print(f"   ⚡ Productivity: {productivity_rate:.1f} tasks/hour")
        
        if productivity_rate > 3:
            print(f"   🚀 Excellent productivity rate!")
        elif productivity_rate > 2:
            print(f"   ✅ Good productivity rate")
        elif productivity_rate > 1:
            print(f"   📈 Moderate productivity rate")
        else:
            print(f"   🎯 Focus session - planning/research")
    print()
    
    # Show recent completed tasks
    if completed_todos:
        print(f"🎉 RECENTLY COMPLETED")
        for todo in completed_todos[-3:]:  # Last 3 completed
            content = todo.get('content', 'Unknown task')[:50]
            print(f"   ✅ {content}")
        if len(completed_todos) > 3:
            print(f"   ... and {len(completed_todos) - 3} more")
        print()
    
    # Show next priority tasks
    if pending_todos:
        print(f"🎯 NEXT PRIORITIES")
        priority_todos = sorted(pending_todos, key=lambda x: x.get('priority', 'medium'))
        for todo in priority_todos[:3]:  # Top 3 priorities
            content = todo.get('content', 'Unknown task')[:50]
            priority = todo.get('priority', 'medium')
            priority_icon = "🔥" if priority == "high" else "📝" if priority == "medium" else "⚡"
            print(f"   {priority_icon} {content}")

def quick_performance_check():
    """Quick check of recent performance metrics"""
    print("⚡ QUICK PERFORMANCE CHECK")
    print("=" * 40)
    
    # Check last 3 days of consciousness logs
    performance_data = []
    
    for i in range(3):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%Y_%m_%d")
        log_file = f"Software-Engineer-AI-Agent-Atlas-main/WORKING_LOG/2025/06-jun/wl_{date_str}.md"
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for email processing sessions
            if 'Email Processing Session' in content:
                # Extract performance metrics
                lines = content.split('\n')
                for line in lines:
                    if 'Processing Rate' in line and 'emails/sec' in line:
                        try:
                            rate = float(line.split(':')[1].strip().split()[0])
                            performance_data.append({
                                'date': date.strftime("%Y-%m-%d"),
                                'rate': rate
                            })
                            break
                        except:
                            pass
    
    if performance_data:
        print("📧 EMAIL PROCESSING PERFORMANCE (Last 3 Days)")
        for data in reversed(performance_data):  # Most recent first
            print(f"   {data['date']}: {data['rate']:.1f} emails/sec")
        
        if len(performance_data) > 1:
            latest_rate = performance_data[0]['rate']
            previous_rate = performance_data[1]['rate']
            
            if latest_rate > previous_rate * 1.1:
                print("   📈 Performance improving!")
            elif latest_rate < previous_rate * 0.9:
                print("   📉 Performance declining")
            else:
                print("   ➡️ Performance stable")
    else:
        print("📧 No recent email processing performance data found")
    print()
    
    # Check consciousness activity level
    today = datetime.now().strftime("%Y_%m_%d")
    log_file = f"Software-Engineer-AI-Agent-Atlas-main/WORKING_LOG/2025/06-jun/wl_{today}.md"
    
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        activity_count = content.count('## ')
        print(f"🧠 TODAY'S CONSCIOUSNESS ACTIVITY")
        print(f"   Logged Activities: {activity_count}")
        
        if activity_count > 10:
            print("   🔥 High consciousness engagement!")
        elif activity_count > 5:
            print("   ✅ Good consciousness tracking")
        elif activity_count > 2:
            print("   📈 Moderate consciousness activity")
        else:
            print("   💡 Opportunity to increase consciousness logging")

def main_menu():
    """Main menu for quick consciousness benefits"""
    while True:
        print("\n🧠 ATLAS CONSCIOUSNESS QUICK START")
        print("=" * 50)
        print("1. 👁️  Today's Consciousness Activity")
        print("2. 💡 Capture Quick Insight")
        print("3. 📊 Enhanced Session Summary")
        print("4. ⚡ Quick Performance Check")
        print("5. 🔧 Show Enhancement Commands")
        print("6. ❌ Exit")
        print("=" * 50)
        
        choice = input("Enter choice (1-6): ").strip()
        
        if choice == "1":
            show_todays_consciousness()
        elif choice == "2":
            capture_quick_insight()
        elif choice == "3":
            enhanced_session_summary()
        elif choice == "4":
            quick_performance_check()
        elif choice == "5":
            show_enhancement_commands()
        elif choice == "6":
            print("👋 Continue with enhanced consciousness awareness!")
            break
        else:
            print("❌ Invalid choice")
        
        input("\nPress Enter to continue...")

def show_enhancement_commands():
    """Show commands for enhanced consciousness workflow"""
    print("🔧 ATLAS CONSCIOUSNESS ENHANCEMENT COMMANDS")
    print("=" * 60)
    print()
    print("🚀 ENHANCED SESSION MANAGEMENT:")
    print("   ./atlas-restore-enhanced   # Start with consciousness logging")
    print("   ./save-session-enhanced    # Save with consciousness analysis")
    print()
    print("💡 INSIGHT CAPTURE:")
    print("   python3 atlas_insight.py                    # Interactive insight capture")
    print("   python3 atlas_insight.py breakthrough 'text' # Quick breakthrough capture")
    print("   python3 atlas_insight.py pattern 'text'     # Quick pattern capture")
    print()
    print("📊 CONSCIOUSNESS REVIEW:")
    print("   python3 atlas_review.py           # 7-day consciousness review")
    print("   python3 atlas_review.py 14        # 14-day consciousness review")
    print("   python3 atlas_review.py knowledge # Knowledge base summary")
    print()
    print("🧠 CONSCIOUSNESS INTEGRATION:")
    print("   python3 atlas_consciousness_quickstart.py  # This tool")
    print("   python3 atlas_email_enhancement.py status  # Email consciousness status")
    print()
    print("📝 CONSCIOUSNESS LOGS:")
    print("   # Today's working log:")
    print("   cat Software-Engineer-AI-Agent-Atlas-main/WORKING_LOG/2025/06-jun/wl_$(date +%Y_%m_%d).md")
    print()
    print("   # Knowledge base:")
    print("   ls Software-Engineer-AI-Agent-Atlas-main/MEMORY/KNOWLEDGE_LOG/")
    print()
    print("🎯 IMMEDIATE BENEFITS:")
    print("   ✅ Session continuity across conversations")
    print("   ✅ Engineering decision history and patterns")
    print("   ✅ Performance optimization insights")
    print("   ✅ Problem-solving pattern recognition")
    print("   ✅ Learning acceleration through insight capture")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "today":
            show_todays_consciousness()
        elif command == "insight":
            capture_quick_insight()
        elif command == "summary":
            enhanced_session_summary()
        elif command == "performance":
            quick_performance_check()
        elif command == "commands":
            show_enhancement_commands()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: today, insight, summary, performance, commands")
    else:
        main_menu()
