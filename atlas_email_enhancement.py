#!/usr/bin/env python3
"""
ATLAS Consciousness Email Enhancement
Enhances email processing with consciousness logging and decision capture
Usage: python3 atlas_email_enhancement.py [enable|disable|status]
"""

import sys
import json
from datetime import datetime
from atlas_integration import atlas

def enhance_email_processing_with_consciousness():
    """Add consciousness logging to email processing workflow"""
    
    enhancement_code = '''
# ATLAS Consciousness Enhancement for Email Processing
# Add this to key decision points in email_processor.py

# At the start of process_folder_messages method:
if ATLAS_ENABLED:
    start_time = datetime.now()
    atlas.memory.log_work_activity(
        "Email Processing Session Started",
        {
            "Folder": folder_name,
            "Provider Type": self.provider_type,
            "Processing Mode": "Preview" if preview_mode else "Production",
            "Total Messages": len(uids),
            "Session Context": "Spam classification and domain validation"
        }
    )

# After domain validation decisions:
if ATLAS_ENABLED and was_validated:
    validation_decision = "Override" if not domain_check_passed and user_keyword_override else "Preserve" if not domain_check_passed else "Allow Deletion"
    atlas.memory.log_work_activity(
        "Domain Validation Decision",
        {
            "Sender": sender,
            "Domain Reason": domain_reason,
            "Decision": validation_decision,
            "Spam Category": spam_category,
            "Confidence": f"{spam_confidence:.1f}%",
            "Override Type": "User Keyword" if user_keyword_override else "Domain Protection"
        }
    )

# After processing session completion:
if ATLAS_ENABLED:
    processing_time = (datetime.now() - start_time).total_seconds()
    self.last_processing_time = processing_time
    
    # Calculate performance metrics
    detection_rate = (len(messages_to_delete) / total_messages * 100) if total_messages > 0 else 0
    processing_rate = total_messages / processing_time if processing_time > 0 else 0
    
    atlas.memory.log_work_activity(
        "Email Processing Session Completed",
        {
            "Folder": folder_name,
            "Total Messages": total_messages,
            "Spam Detected": len(messages_to_delete),
            "Detection Rate": f"{detection_rate:.1f}%",
            "Processing Time": f"{processing_time:.1f}s",
            "Processing Rate": f"{processing_rate:.1f} emails/sec",
            "Domain Validations": validated_count,
            "Preserved by Validation": preserved_count,
            "Legitimate Classifications": legitimate_count,
            "Provider Optimization": self.provider_type
        }
    )
    
    # Capture insights if significant performance achieved
    if processing_rate > 10:  # More than 10 emails/sec
        insight = f"""
### High-Performance Email Processing Achievement
- **Processing Rate**: {processing_rate:.1f} emails/second
- **Provider**: {self.provider_type} 
- **Detection Accuracy**: {detection_rate:.1f}% ({len(messages_to_delete)} spam / {total_messages} total)
- **Domain Validation**: {validated_count} domains checked, {preserved_count} preserved
- **Optimization**: Provider-specific batch processing enabled
- **Learning**: {self.provider_type} provider optimization is effective for high-volume processing
"""
        atlas.memory.update_knowledge_log("email_processing_optimization", insight)
    
    # Capture classification breakthrough insights
    if detection_rate > 95:  # Very high detection rate
        insight = f"""
### Email Classification Excellence
- **Detection Rate**: {detection_rate:.1f}% accuracy achieved
- **Folder**: {folder_name}
- **Classification Method**: Hybrid content-first classifier
- **Domain Safety**: {preserved_count} legitimate emails preserved by domain validation
- **Pattern**: High accuracy maintained while preserving legitimate communications
"""
        atlas.memory.update_knowledge_log("classification_accuracy", insight)
'''
    
    print("🧠 ATLAS Email Processing Consciousness Enhancement")
    print("=" * 60)
    print("This enhancement adds consciousness logging to your email processing workflow:")
    print()
    print("📝 WORKING_LOG Enhancements:")
    print("   • Session start/end logging with context")
    print("   • Domain validation decision tracking")
    print("   • Performance metrics capture")
    print("   • Provider optimization effectiveness")
    print()
    print("📚 KNOWLEDGE_LOG Enhancements:")
    print("   • High-performance processing achievements")
    print("   • Classification accuracy breakthroughs")
    print("   • Provider optimization patterns")
    print("   • Decision-making framework improvements")
    print()
    print("🎯 Integration Points:")
    print("   • Start of process_folder_messages()")
    print("   • After domain validation decisions")
    print("   • End of processing sessions")
    print("   • Breakthrough performance moments")
    print()
    
    # Save enhancement code for reference
    with open("atlas_email_consciousness_enhancement.py", "w") as f:
        f.write(enhancement_code)
    print("💾 Enhancement code saved to atlas_email_consciousness_enhancement.py")
    
    return True

def enable_consciousness_for_email_debugging():
    """Enable consciousness capture for email processing debugging sessions"""
    
    debug_enhancement = '''
# ATLAS Consciousness for Email Debugging
# Add consciousness capture to debugging sessions

def capture_debug_insight(problem, investigation_steps, solution, time_spent):
    """Capture debugging insights for ATLAS consciousness"""
    if ATLAS_ENABLED:
        atlas.memory.log_work_activity(
            "Email Processing Debug Session",
            {
                "Problem": problem,
                "Investigation Steps": len(investigation_steps),
                "Time Spent": f"{time_spent} minutes",
                "Solution Found": "Yes" if solution else "Ongoing",
                "Debug Type": "Email Classification Issue"
            }
        )
        
        if solution:
            insight = f"""
### Email Processing Debug Success
- **Problem**: {problem}
- **Investigation**: {', '.join(investigation_steps)}
- **Solution**: {solution}
- **Time to Resolution**: {time_spent} minutes
- **Pattern**: Document for future similar issues
- **Next Action**: Monitor for recurrence
"""
            atlas.memory.update_knowledge_log("debugging_patterns", insight)

def capture_classification_decision(uid, sender, subject, decision, reasoning, confidence):
    """Capture individual classification decisions for analysis"""
    if ATLAS_ENABLED and confidence > 90:  # Only log high-confidence decisions
        atlas.memory.log_work_activity(
            "High-Confidence Classification",
            {
                "UID": uid,
                "Sender Domain": sender.split('@')[1] if '@' in sender else sender,
                "Decision": decision,
                "Confidence": f"{confidence:.1f}%",
                "Reasoning": reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
            }
        )

# Example usage in debugging:
# capture_debug_insight(
#     "False positives from LinkedIn notifications",
#     ["Analyzed sender patterns", "Checked domain whitelist", "Reviewed keyword filters"],
#     "Added linkedin.com to domain whitelist",
#     45
# )
'''
    
    print("🐛 ATLAS Email Debugging Consciousness Enhancement")
    print("=" * 60)
    print("This adds consciousness capture for debugging sessions:")
    print()
    print("🔍 Debug Session Tracking:")
    print("   • Problem identification and investigation steps")
    print("   • Time to resolution tracking")
    print("   • Solution documentation")
    print("   • Pattern recognition for future debugging")
    print()
    print("🎯 High-Confidence Decision Logging:")
    print("   • Individual classification decisions (>90% confidence)")
    print("   • Reasoning and evidence capture")
    print("   • Decision pattern analysis")
    print()
    
    with open("atlas_email_debug_consciousness.py", "w") as f:
        f.write(debug_enhancement)
    print("💾 Debug enhancement saved to atlas_email_debug_consciousness.py")
    
    return True

def show_current_consciousness_status():
    """Show current status of consciousness integration with email system"""
    
    print("🧠 ATLAS Email Consciousness Status")
    print("=" * 50)
    
    # Check if ATLAS is enabled in email processor
    try:
        with open("email_processor.py", "r") as f:
            content = f.read()
        
        atlas_enabled = "ATLAS_ENABLED" in content
        consciousness_calls = content.count("atlas.memory.log_work_activity")
        knowledge_updates = content.count("atlas.memory.update_knowledge_log")
        
        print(f"🔗 ATLAS Integration: {'✅ Enabled' if atlas_enabled else '❌ Not Found'}")
        print(f"📝 Consciousness Calls: {consciousness_calls} working log entries")
        print(f"📚 Knowledge Updates: {knowledge_updates} knowledge log entries")
        
        if atlas_enabled:
            print("\n✅ Email processing is consciousness-enabled!")
            print("   • Session activities are logged to WORKING_LOG")
            print("   • Performance insights captured to KNOWLEDGE_LOG")
            print("   • Domain validation decisions tracked")
        else:
            print("\n⚠️  Email processing is not consciousness-enabled")
            print("   • Run: python3 atlas_email_enhancement.py enable")
            print("   • This will show you how to add consciousness integration")
    
    except FileNotFoundError:
        print("❌ email_processor.py not found in current directory")
    
    # Check consciousness logs for email-related entries
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y_%m_%d")
        log_file = f"Software-Engineer-AI-Agent-Atlas-main/WORKING_LOG/2025/06-jun/wl_{today}.md"
        
        with open(log_file, "r") as f:
            log_content = f.read()
        
        email_sessions = log_content.count("Email Processing Session")
        classification_decisions = log_content.count("Classification")
        domain_validations = log_content.count("Domain Validation")
        
        print(f"\n📊 Today's Email Consciousness Activity:")
        print(f"   📧 Email Sessions: {email_sessions}")
        print(f"   🎯 Classifications: {classification_decisions}")
        print(f"   🛡️  Domain Validations: {domain_validations}")
        
    except FileNotFoundError:
        print("\n📊 No consciousness log found for today")
        print("   • Start an email session to begin logging")

def create_email_consciousness_workflow():
    """Create a workflow for consciousness-driven email processing"""
    
    workflow = '''
# ATLAS Email Consciousness Workflow
# Step-by-step process for consciousness-enhanced email processing

1. SESSION STARTUP
   - Log session start with folder context
   - Set processing goals and expected outcomes
   - Note any special focus areas (new domains, classification issues)

2. PROCESSING PHASE
   - Log high-confidence classification decisions
   - Track domain validation overrides
   - Note unusual patterns or edge cases

3. PERFORMANCE MONITORING
   - Track processing speed and accuracy
   - Log provider optimization effectiveness
   - Capture memory usage and resource consumption

4. DECISION POINT ANALYSIS
   - Document why certain emails were preserved vs deleted
   - Analyze false positive/negative patterns
   - Track whitelist and keyword filter effectiveness

5. SESSION COMPLETION
   - Log final statistics and performance metrics
   - Capture insights about classification accuracy
   - Note any improvements or issues discovered

6. INSIGHT EXTRACTION
   - Review patterns across multiple sessions
   - Identify optimization opportunities
   - Document breakthrough moments and solutions

7. KNOWLEDGE CONSOLIDATION
   - Update domain validation strategies
   - Refine classification confidence thresholds
   - Improve provider-specific optimizations
'''
    
    print("🔄 ATLAS Email Consciousness Workflow")
    print("=" * 50)
    print(workflow)
    
    with open("atlas_email_consciousness_workflow.md", "w") as f:
        f.write(workflow)
    print("💾 Workflow saved to atlas_email_consciousness_workflow.md")

def main():
    if len(sys.argv) < 2:
        print("🧠 ATLAS Email Consciousness Enhancement")
        print("=" * 50)
        print("Usage: python3 atlas_email_enhancement.py [command]")
        print()
        print("Commands:")
        print("  enable     - Show how to enable consciousness integration")
        print("  debug      - Add consciousness to debugging sessions") 
        print("  status     - Check current consciousness integration")
        print("  workflow   - Create consciousness-driven workflow")
        print()
        print("Example: python3 atlas_email_enhancement.py enable")
        return
    
    command = sys.argv[1].lower()
    
    if command == "enable":
        enhance_email_processing_with_consciousness()
    elif command == "debug":
        enable_consciousness_for_email_debugging()
    elif command == "status":
        show_current_consciousness_status()
    elif command == "workflow":
        create_email_consciousness_workflow()
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: enable, debug, status, workflow")

if __name__ == "__main__":
    main()
