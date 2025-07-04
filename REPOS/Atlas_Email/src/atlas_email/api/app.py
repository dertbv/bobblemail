#!/usr/bin/env python3
"""
Fresh KISS Web Interface for Mail Filter - Rebuilt from Scratch
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List
from pathlib import Path

# Add project root to path so config module can be found
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Check dependencies
try:
    from fastapi import FastAPI, Request, Form
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.templating import Jinja2Templates
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    print("❌ Missing dependencies: pip install fastapi uvicorn")
    sys.exit(1)

# Import your existing modules
from atlas_email.models.database import db
from atlas_email.models.db_logger import logger
from config.credentials import db_credentials
from atlas_email.utils.batch_timer import AutoBatchTimer
from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
# get_filters will be imported locally when needed

# ML Training Integration
import threading

# Initialize classifier for re-classification
hybrid_classifier = None

def get_classifier():
    """Get initialized classifier for re-classification"""
    global hybrid_classifier
    if hybrid_classifier is None:
        try:
            print("🔄 Initializing classifier for re-classification...")
            hybrid_classifier = EnsembleHybridClassifier()
            print("✅ Classifier initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize classifier: {e}")
            import traceback
            traceback.print_exc()
            hybrid_classifier = None
    return hybrid_classifier

def _trigger_ml_training_async(feedback_type='incorrect'):
    """Trigger ML training in background thread when feedback is received"""
    def run_training():
        try:
            print(f"🤖 Starting ML training trigger for feedback type: {feedback_type}")
            
            # Import and run binary feedback processor
            from atlas_email.ml.feedback_processor import BinaryFeedbackProcessor
            processor = BinaryFeedbackProcessor()
            
            # Get count of unprocessed feedback
            unprocessed_count = len(processor.get_unprocessed_feedback())
            print(f"📊 Found {unprocessed_count} unprocessed feedback records")
            
            # Only trigger training if we have enough feedback or if this is incorrect feedback
            if feedback_type == 'incorrect' or unprocessed_count >= 5:
                print(f"🚀 Triggering ML retraining (threshold met)")
                results = processor.process_all_unprocessed_feedback()
                print(f"✅ ML training completed: {results}")
            else:
                print(f"⏭️ Skipping ML training (not enough feedback: {unprocessed_count}/5)")
                
        except Exception as e:
            print(f"❌ ML training failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run in background thread to avoid blocking the web request
    training_thread = threading.Thread(target=run_training, daemon=True)
    training_thread.start()
    print(f"🔄 ML training triggered in background thread")

def reclassify_email(email_data):
    """Re-classify an email using current system and return new classification"""
    classifier = get_classifier()
    if not classifier:
        return {"error": "Classifier not available", "current_category": "Unknown", "confidence": 0.0}
    
    try:
        # Extract data for classification
        sender = email_data.get('sender_email', '')
        subject = email_data.get('subject', '')
        headers = ""  # We don't have headers in the stored data
        
        print(f"🔄 Re-classifying: {sender} | {subject}")
        
        # Run classification with correct parameters
        result = classifier.classify_email(sender, subject, headers)
        
        print(f"✅ Classification result: {result}")
        
        return {
            "current_category": result.get('category', 'Unknown'),
            "confidence": round(result.get('confidence', 0.0), 2),
            "reason": result.get('reasoning', 'Current system classification'),
            "system_agrees": result.get('category') == email_data.get('category'),
            "features": result.get('features', {}),
            "method": result.get('method', 'hybrid')
        }
        
    except Exception as e:
        print(f"❌ Re-classification error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "current_category": "Error", "confidence": 0.0}

def get_next_classification_alternative(sender: str, subject: str, original_category: str, email_id: int) -> str:
    """
    ALTERNATIVE RANKING SYSTEM: Get the next logical classification alternative.
    
    This function is called when user clicks thumbs down to cycle through
    ranked alternative classifications until user accepts one.
    
    Args:
        sender: Email sender address
        subject: Email subject line
        original_category: Current classification that user rejected
        email_id: Database ID for tracking attempts
        
    Returns:
        Next best alternative classification
    """
    try:
        from atlas_email.filters.keyword_processor import keyword_processor
        
        # Check if we've already tried alternatives for this email
        existing_attempts = db.execute_query("""
            SELECT user_classification FROM user_feedback 
            WHERE email_uid = ? AND feedback_type = 'incorrect'
            ORDER BY timestamp DESC
        """, (f"internal_{email_id}",))
        
        # Get all possible ranked classifications
        all_text = f"{subject} {sender}".lower()
        ranked_alternatives = keyword_processor.get_ranked_classifications(
            all_text, sender, confidence_threshold=0.2, limit=8
        )
        
        print(f"🎯 Ranked alternatives for email {email_id}: {[cat for cat, conf, spec in ranked_alternatives]}")
        
        # Build list of categories to exclude (original + previously tried)
        excluded_categories = {original_category}
        for attempt in existing_attempts:
            if attempt[0]:  # user_classification is not null
                excluded_categories.add(attempt[0])
        
        # Find next best alternative that hasn't been tried
        for category, confidence, specificity in ranked_alternatives:
            if category not in excluded_categories:
                print(f"✅ Selected next alternative: {category} (confidence: {confidence:.2f}, specificity: {specificity:.2f})")
                return category
        
        # If we've exhausted all logical alternatives, fall back to "Not Spam"
        if "Not Spam" not in excluded_categories:
            print("🔄 Falling back to 'Not Spam' - all alternatives exhausted")
            return "Not Spam"
        
        # Ultimate fallback - return "Marketing Spam" (should never reach here)
        print("⚠️ All alternatives exhausted, using final fallback")
        return "Marketing Spam"
        
    except Exception as e:
        print(f"❌ Error getting next classification alternative: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback on error
        simple_fallbacks = ["Marketing Spam", "Promotional Email", "Not Spam"]
        for fallback in simple_fallbacks:
            if fallback != original_category:
                return fallback
        return "Not Spam"

app = FastAPI(title="Mail Filter Web Interface - Fresh", version="2.0.0")

# Initialize Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global variables for timer management
web_timer = None

def initialize_web_timer():
    """Initialize the auto batch timer for web interface"""
    global web_timer
    
    def batch_callback():
        # Import here to avoid circular imports
        from atlas_email.core.processing_controller import batch_processing_for_timer
        return batch_processing_for_timer()
    
    web_timer = AutoBatchTimer(batch_callback)
    return web_timer

# Initialize timer on startup
web_timer = initialize_web_timer()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard - completely rebuilt"""
    
    print("🚨 FRESH DASHBOARD FUNCTION CALLED!")  # Debug
    
    try:
        # Force fresh connection
        db.close_connection()
        
        # Get database stats
        stats = db.get_database_stats()
        print(f"📊 Stats: {stats}")
        
        # Map bulletproof count to expected key for template compatibility
        stats['processed_emails_count'] = stats.get('processed_emails_bulletproof_count', 0)
        
        # Get accounts
        accounts = db_credentials.load_credentials()
        account_count = len(accounts) if accounts else 0
        print(f"👤 Accounts: {account_count}")
        
        # Get LATEST emails with explicit timestamp sorting
        print("🔍 Fetching latest emails...")
        latest_emails = db.execute_query("""
            SELECT 
                datetime(timestamp) as formatted_time,
                timestamp,
                action, 
                sender_email, 
                subject, 
                category,
                reason,
                id
            FROM processed_emails_bulletproof 
            ORDER BY datetime(timestamp) DESC, id DESC
            LIMIT 15
        """)
        
        print(f"📧 Found {len(latest_emails)} recent emails")
        
        # Format emails for template
        formatted_emails = []
        for email in latest_emails:
            try:
                # Parse timestamp - already in local time, no timezone conversion needed
                dt = datetime.fromisoformat(email['timestamp'].replace('T', ' ').replace('Z', ''))
                time_display = dt.strftime("%H:%M:%S")
                date_display = dt.strftime("%m/%d")
                full_timestamp = f"{date_display} {time_display}"
            except:
                full_timestamp = "Unknown"
            
            formatted_emails.append({
                'timestamp': full_timestamp,
                'action': email['action'],
                'sender_email': email['sender_email'] or '',
                'subject': email['subject'] or '',
                'category': email['category'] or 'Unknown',
                'reason': email['reason'] or ''
            })
        
        # Prepare context for template
        context = {
            'request': request,
            'stats': {
                'total_accounts': account_count,
                'total_emails': f"{stats.get('processed_emails_count', 0):,}",
                'spam_count': stats.get('spam_count', 0),
                'sessions_count': stats.get('sessions_count', 0),
                'db_size_mb': f"{stats.get('db_size_mb', 0):.1f}"
            },
            'emails': formatted_emails,
            'last_updated': datetime.now().strftime('%H:%M:%S')
        }
        
        return templates.TemplateResponse("pages/dashboard.html", context)
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"<h1>Error: {e}</h1>")


@app.get("/timer", response_class=HTMLResponse)
async def timer_control(request: Request):
    """Timer control page"""
    print("⏰ TIMER CONTROL PAGE CALLED!")
    
    timer_active = web_timer.is_timer_active() if web_timer else False
    timer_minutes = web_timer.timer_minutes if web_timer else 0
    repeat_mode = web_timer.repeat_timer if web_timer else False
    execution_count = web_timer.execution_count if web_timer else 0
    
    # Get timer status details
    timer_status = "Inactive"
    timer_details = ""
    if web_timer and web_timer.is_timer_active():
        timer_status = "Active"
        if web_timer.start_time:
            elapsed = datetime.now() - web_timer.start_time
            remaining = timedelta(minutes=web_timer.timer_minutes) - elapsed
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() / 60)
                timer_details = f"{mins} minutes remaining"
    
    context = {
        'request': request,
        'timer_active': timer_active,
        'timer_minutes': timer_minutes,
        'repeat_mode': repeat_mode,
        'execution_count': execution_count,
        'timer_details': timer_details
    }
    
    return templates.TemplateResponse("pages/timer.html", context)

# API Endpoints for Timer Control
@app.post("/api/timer/set")
async def set_timer(request: Request):
    """Set timer configuration"""
    try:
        data = await request.json()
        minutes = data.get('minutes', 30)
        repeat_mode = data.get('repeat_mode', False)
        
        if web_timer:
            web_timer.timer_minutes = minutes
            web_timer.repeat_timer = repeat_mode
            
            return {"success": True, "message": f"Timer set to {minutes} minutes ({'repeating' if repeat_mode else 'one-time'})"}
        else:
            return {"success": False, "message": "Timer not initialized"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/timer/start")
async def start_timer():
    """Start the timer"""
    try:
        if web_timer and not web_timer.is_timer_active():
            if web_timer.timer_minutes > 0:
                web_timer._start_timer()
                return {"success": True, "message": "Timer started successfully"}
            else:
                return {"success": False, "message": "Please set timer duration first"}
        else:
            return {"success": False, "message": "Timer already active or not initialized"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/timer/stop")
async def stop_timer():
    """Stop the timer"""
    try:
        if web_timer and web_timer.is_timer_active():
            web_timer.stop_requested = True
            web_timer.timer_active = False
            return {"success": True, "message": "Timer stopped successfully"}
        else:
            return {"success": False, "message": "Timer not active"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/country-classifications/{country_code}")
async def get_country_classifications(country_code: str):
    """Get spam classification breakdown for a specific country"""
    print(f"🌍 COUNTRY CLASSIFICATIONS API called for {country_code}")
    
    try:
        classifications_raw = db.execute_query("""
            SELECT 
                category,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
            FROM processed_emails_bulletproof 
            WHERE sender_country_code = ?
            AND category IS NOT NULL
            AND action = 'DELETED'
            AND category NOT IN ('Marketing', 'Promotional', 'Whitelisted', 'Marketing Spam', 'Promotional Email', 'Transactional', 'TRANSACTIONAL', 'BUSINESS_TRANSACTION')
            GROUP BY category
            ORDER BY count DESC 
            LIMIT 7
        """, (country_code,))
        
        classifications = [dict(row) for row in classifications_raw]
        
        return {
            "success": True,
            "country_code": country_code,
            "classifications": classifications
        }
        
    except Exception as e:
        print(f"❌ Country classifications error: {e}")
        return {"success": False, "message": f"Error getting classifications: {str(e)}"}

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """Analytics and reporting dashboard using Jinja2 template"""
    print("📊 ANALYTICS DASHBOARD CALLED!")
    
    try:
        # Get comprehensive analytics data
        analytics_data = get_analytics_data()
        
        # Calculate effectiveness rate
        eff = analytics_data['effectiveness']
        total = eff.get('total_count', 0)
        deleted = eff.get('deleted_count', 0)
        effectiveness_rate = (deleted / total * 100) if total > 0 else 0
        
        # Provider icons for account breakdown
        provider_icons = {
            'gmail': '📧',
            'icloud': '☁️',
            'outlook': '📨',
            'yahoo': '📮',
            'other': '📧'
        }
        
        return templates.TemplateResponse("pages/analytics.html", {
            "request": request,
            "effectiveness": analytics_data['effectiveness'],
            "effectiveness_rate": effectiveness_rate,
            "categories": analytics_data['categories'],
            "daily_activity": analytics_data['daily_activity'],
            "spam_domains": analytics_data['spam_domains'],
            "session_stats": analytics_data['session_stats'],
            "account_breakdown_total": analytics_data['account_breakdown_total'],
            "account_breakdown_spam": analytics_data['account_breakdown_spam'],
            "geographic_data": analytics_data['geographic_data'],
            "provider_icons": provider_icons
        })
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("pages/analytics.html", {
            "request": request,
            "error": str(e)
        })

def get_analytics_data():
    """Gather analytics data from database"""
    
    # Get processing effectiveness (last 30 days)
    effectiveness_raw = db.execute_query("""
        SELECT 
            COUNT(CASE WHEN action = 'DELETED' THEN 1 END) as deleted_count,
            COUNT(CASE WHEN action = 'PRESERVED' THEN 1 END) as preserved_count,
            COUNT(*) as total_count
        FROM processed_emails_bulletproof 
        WHERE datetime(timestamp) > datetime('now', '-30 days')
    """)
    effectiveness = dict(effectiveness_raw[0]) if effectiveness_raw else {}
    
    # Get spam categories breakdown
    categories_raw = db.execute_query("""
        SELECT 
            category,
            COUNT(*) as count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
        FROM processed_emails_bulletproof 
        WHERE action = 'DELETED' 
        AND datetime(timestamp) > datetime('now', '-30 days')
        AND category IS NOT NULL
        GROUP BY category 
        ORDER BY count DESC 
        LIMIT 10
    """)
    categories = [dict(row) for row in categories_raw]
    
    # Get daily activity (last 14 days)
    daily_activity_raw = db.execute_query("""
        SELECT 
            DATE(timestamp) as date,
            COUNT(CASE WHEN action = 'DELETED' THEN 1 END) as deleted,
            COUNT(CASE WHEN action = 'PRESERVED' THEN 1 END) as preserved
        FROM processed_emails_bulletproof 
        WHERE datetime(timestamp) > datetime('now', '-14 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    """)
    daily_activity = [dict(row) for row in daily_activity_raw]
    
    # Get top spam domains
    spam_domains_raw = db.execute_query("""
        SELECT 
            sender_domain,
            COUNT(*) as count
        FROM processed_emails_bulletproof 
        WHERE action = 'DELETED' 
        AND datetime(timestamp) > datetime('now', '-30 days')
        AND sender_domain IS NOT NULL
        GROUP BY sender_domain 
        ORDER BY count DESC 
        LIMIT 10
    """)
    spam_domains = [dict(row) for row in spam_domains_raw]
    
    # Get session performance
    session_stats_raw = db.execute_query("""
        SELECT 
            AVG(total_deleted + total_preserved) as avg_emails_per_session,
            AVG(total_deleted * 100.0 / NULLIF(total_deleted + total_preserved, 0)) as avg_deletion_rate,
            COUNT(*) as total_sessions
        FROM sessions 
        WHERE datetime(start_time) > datetime('now', '-30 days')
    """)
    session_stats = dict(session_stats_raw[0]) if session_stats_raw else {}
    
    # Get account breakdown by provider - TOTAL MAIL (last 30 days)
    account_breakdown_total_raw = db.execute_query("""
        SELECT 
            a.provider,
            COUNT(pe.id) as email_count,
            COUNT(pe.id) * 100.0 / SUM(COUNT(pe.id)) OVER() as percentage
        FROM processed_emails_bulletproof pe
        JOIN sessions s ON pe.session_id = s.id
        JOIN accounts a ON s.account_id = a.id
        WHERE datetime(pe.timestamp) > datetime('now', '-30 days')
        GROUP BY a.provider
        ORDER BY email_count DESC
    """)
    account_breakdown_total = [dict(row) for row in account_breakdown_total_raw]
    
    # Get account breakdown by provider - SPAM ONLY (last 30 days)
    account_breakdown_spam_raw = db.execute_query("""
        SELECT 
            a.provider,
            COUNT(pe.id) as spam_count,
            COUNT(pe.id) * 100.0 / SUM(COUNT(pe.id)) OVER() as percentage
        FROM processed_emails_bulletproof pe
        JOIN sessions s ON pe.session_id = s.id
        JOIN accounts a ON s.account_id = a.id
        WHERE datetime(pe.timestamp) > datetime('now', '-30 days')
        AND pe.action = 'DELETED'
        GROUP BY a.provider
        ORDER BY spam_count DESC
    """)
    account_breakdown_spam = [dict(row) for row in account_breakdown_spam_raw]
    
    # Get geographic data breakdown (all time, excluding marketing/promotional/transactional)
    geographic_data_raw = db.execute_query("""
        SELECT 
            sender_country_code,
            sender_country_name,
            COUNT(*) as count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage,
            AVG(geographic_risk_score) as avg_risk_score
        FROM processed_emails_bulletproof 
        WHERE sender_country_code IS NOT NULL
        AND sender_country_name IS NOT NULL
        AND action = 'DELETED'
        AND category NOT IN ('Marketing', 'Promotional', 'Whitelisted', 'Marketing Spam', 'Promotional Email', 'Transactional', 'TRANSACTIONAL', 'BUSINESS_TRANSACTION')
        GROUP BY sender_country_code, sender_country_name
        ORDER BY count DESC 
        LIMIT 15
    """)
    geographic_data = [dict(row) for row in geographic_data_raw]
    
    return {
        'effectiveness': effectiveness,
        'categories': categories,
        'daily_activity': daily_activity,
        'spam_domains': spam_domains,
        'session_stats': session_stats,
        'account_breakdown_total': account_breakdown_total,
        'account_breakdown_spam': account_breakdown_spam,
        'geographic_data': geographic_data
    }


@app.post("/api/batch/run")
async def run_batch_processing():
    """Run batch processing with proper session management"""
    print("🚀 BATCH PROCESSING API CALLED!")
    
    try:
        # Import your main batch processing function
        import subprocess
        import os
        
        # Run the batch processing in a separate process to avoid blocking
        # This ensures proper session management
        result = subprocess.run([
            sys.executable, "-c", 
            """
import sys
sys.path.append('.')
from atlas_email.core.processing_controller import batch_processing_for_timer
result = batch_processing_for_timer()
print(f'BATCH_RESULT: {result}')
            """
        ], 
        capture_output=True, 
        text=True, 
        timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Check if batch processing succeeded
            output = result.stdout
            success = "BATCH_RESULT: True" in output or "BATCH_RESULT: None" in output
            
            return {
                "success": success,
                "message": "Batch processing completed successfully!" if success else "Batch processing completed with warnings",
                "output": output[-500:] if output else ""  # Last 500 chars
            }
        else:
            return {
                "success": False,
                "message": f"Batch processing failed: {result.stderr}",
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Batch processing timed out (took longer than 5 minutes)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error starting batch processing: {str(e)}"
        }



@app.post("/api/feedback")
async def submit_user_feedback(request: Request):
    """Submit user feedback for email classification"""
    print("👍 USER FEEDBACK API called")
    
    try:
        # Parse JSON request body
        feedback_data = await request.json()
        
        # Required fields
        email_uid = feedback_data.get('email_uid')
        feedback_type = feedback_data.get('feedback_type')
        original_classification = feedback_data.get('original_classification')
        
        if not email_uid or not feedback_type or not original_classification:
            return {"success": False, "message": "Missing required fields"}
        
        # Optional fields
        user_classification = feedback_data.get('user_classification')
        sender = feedback_data.get('sender')
        subject = feedback_data.get('subject')
        confidence_rating = feedback_data.get('confidence_rating')
        user_comments = feedback_data.get('user_comments')
        account_email = feedback_data.get('account_email')
        
        # NEW: Immediate deletion support
        immediate_action = feedback_data.get('immediate_action', False)
        folder_name = feedback_data.get('folder_name', 'INBOX')
        
        # Get user IP
        user_ip = request.client.host if request.client else None
        
        # Store feedback in database
        feedback_id = db.store_user_feedback(
            email_uid=email_uid,
            feedback_type=feedback_type,
            original_classification=original_classification,
            user_classification=user_classification,
            sender=sender,
            subject=subject,
            user_ip=user_ip,
            account_email=account_email,
            confidence_rating=confidence_rating,
            user_comments=user_comments
        )
        
        print(f"✅ Feedback stored with ID: {feedback_id}")
        
        # NEW: Handle immediate deletion if requested
        deletion_result = None
        if immediate_action and feedback_type in ['incorrect', 'wrong'] and account_email:
            print(f"🗑️ Immediate deletion requested for UID {email_uid}")
            
            try:
                from immediate_email_deletion import delete_single_email
                deletion_result = delete_single_email(account_email, email_uid, folder_name)
                
                if deletion_result["success"]:
                    print(f"✅ Immediate deletion successful: {deletion_result['message']}")
                    
                    # Update analytics counters
                    from atlas_email.models.analytics import increment_analytics_counter
                    increment_analytics_counter('emails_deleted')
                    
                else:
                    print(f"❌ Immediate deletion failed: {deletion_result['message']}")
                    
            except Exception as e:
                deletion_result = {"success": False, "message": f"Deletion error: {str(e)}"}
                print(f"❌ Deletion exception: {e}")
        
        response = {
            "success": True, 
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id
        }
        
        # Include deletion result if immediate action was requested
        if immediate_action:
            response["deletion_result"] = deletion_result
            if deletion_result and deletion_result["success"]:
                response["message"] = "Feedback submitted and email deleted successfully"
        
        return response
        
    except Exception as e:
        print(f"❌ Feedback submission error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error submitting feedback: {str(e)}"}

@app.get("/api/feedback/stats")
async def get_feedback_statistics():
    """Get user feedback statistics for analytics"""
    print("📊 FEEDBACK STATS API called")
    
    try:
        stats = db.get_feedback_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ Feedback stats error: {e}")
        return {"success": False, "message": f"Error getting feedback stats: {str(e)}"}

@app.get("/api/user-stats")
async def get_user_statistics():
    """Get user contribution statistics for web interface"""
    print("📊 USER STATS API called")
    
    try:
        from atlas_email.models.analytics import get_user_contribution_stats, get_user_achievement_badges, get_user_milestones
        
        # Get base statistics
        stats = get_user_contribution_stats()
        
        # Get achievement badges
        badges = get_user_achievement_badges(stats)
        
        # Get milestone progress
        milestones = get_user_milestones(stats)
        
        return {
            "success": True,
            "stats": stats,
            "badges": badges,
            "milestones": milestones
        }
        
    except Exception as e:
        print(f"❌ User stats error: {e}")
        return {
            "success": False, 
            "message": f"Error getting user stats: {str(e)}",
            "stats": {"emails_analyzed": 0, "feedback_given": 0, "emails_deleted": 0, "accuracy": 100.0},
            "badges": [],
            "milestones": {"next_email_milestone": 100, "next_feedback_milestone": 10, "next_deletion_milestone": 10}
        }

# ============================================================================
# EMAIL FLAGGING API ENDPOINTS
# ============================================================================

@app.post("/api/emails/flag")
async def flag_email(request: Request):
    """Flag an email for protection from deletion"""
    print("🚩 FLAG EMAIL API called")
    
    try:
        data = await request.json()
        
        # Extract required fields
        email_uid = data.get('email_uid')
        folder_name = data.get('folder_name')
        account_id = data.get('account_id')
        
        # Extract optional fields
        session_id = data.get('session_id')
        sender_email = data.get('sender_email')
        subject = data.get('subject')
        flag_reason = data.get('flag_reason', 'User requested protection')
        
        # Validate required fields
        if not all([email_uid, folder_name, account_id]):
            return {
                "success": False,
                "message": "Missing required fields: email_uid, folder_name, account_id"
            }
        
        # Flag the email
        success = db.flag_email_for_protection(
            email_uid=email_uid,
            folder_name=folder_name,
            account_id=int(account_id),
            session_id=session_id,
            sender_email=sender_email,
            subject=subject,
            flag_reason=flag_reason,
            created_by='web_user'
        )
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_uid} flagged for protection",
                "email_uid": email_uid,
                "folder_name": folder_name
            }
        else:
            return {
                "success": False,
                "message": "Failed to flag email"
            }
            
    except Exception as e:
        print(f"❌ Flag email error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error flagging email: {str(e)}"}

@app.post("/api/emails/unflag")
async def unflag_email(request: Request):
    """Remove protection flag from an email"""
    print("🚩 UNFLAG EMAIL API called")
    
    try:
        data = await request.json()
        
        # Extract required fields
        email_uid = data.get('email_uid')
        folder_name = data.get('folder_name')
        account_id = data.get('account_id')
        
        # Validate required fields
        if not all([email_uid, folder_name, account_id]):
            return {
                "success": False,
                "message": "Missing required fields: email_uid, folder_name, account_id"
            }
        
        # Unflag the email
        success = db.unflag_email(
            email_uid=email_uid,
            folder_name=folder_name,
            account_id=int(account_id)
        )
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_uid} unflagged",
                "email_uid": email_uid,
                "folder_name": folder_name
            }
        else:
            return {
                "success": False,
                "message": "Failed to unflag email (may not have been flagged)"
            }
            
    except Exception as e:
        print(f"❌ Unflag email error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error unflagging email: {str(e)}"}

@app.get("/api/emails/flagged")
async def get_flagged_emails(account_id: int = None, limit: int = 100):
    """Get list of flagged emails"""
    print(f"🚩 GET FLAGGED EMAILS API called (account_id={account_id})")
    
    try:
        flagged_emails = db.get_flagged_emails(account_id=account_id, limit=limit)
        flagged_count = db.get_flagged_count(account_id=account_id)
        
        return {
            "success": True,
            "flagged_emails": flagged_emails,
            "total_count": flagged_count,
            "returned_count": len(flagged_emails)
        }
        
    except Exception as e:
        print(f"❌ Get flagged emails error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error getting flagged emails: {str(e)}"}

@app.get("/api/emails/flag-status/{account_id}/{folder_name}/{email_uid}")
async def check_flag_status(account_id: int, folder_name: str, email_uid: str):
    """Check if a specific email is flagged"""
    print(f"🚩 CHECK FLAG STATUS API called for UID {email_uid}")
    
    try:
        is_flagged = db.is_email_flagged(
            email_uid=email_uid,
            folder_name=folder_name,
            account_id=account_id
        )
        
        return {
            "success": True,
            "is_flagged": is_flagged,
            "email_uid": email_uid,
            "folder_name": folder_name,
            "account_id": account_id
        }
        
    except Exception as e:
        print(f"❌ Check flag status error: {e}")
        return {"success": False, "message": f"Error checking flag status: {str(e)}"}

@app.post("/api/emails/bulk-flag")
async def bulk_flag_emails(request: Request):
    """Flag multiple emails for protection"""
    print("🚩 BULK FLAG EMAILS API called")
    
    try:
        data = await request.json()
        
        emails = data.get('emails', [])
        account_id = data.get('account_id')
        flag_reason = data.get('flag_reason', 'Bulk user protection')
        
        if not emails or not account_id:
            return {
                "success": False,
                "message": "Missing required fields: emails array and account_id"
            }
        
        successful_flags = 0
        failed_flags = 0
        results = []
        
        for email_data in emails:
            email_uid = email_data.get('email_uid')
            folder_name = email_data.get('folder_name')
            sender_email = email_data.get('sender_email')
            subject = email_data.get('subject')
            
            if not all([email_uid, folder_name]):
                failed_flags += 1
                results.append({
                    "email_uid": email_uid,
                    "success": False,
                    "message": "Missing email_uid or folder_name"
                })
                continue
            
            success = db.flag_email_for_protection(
                email_uid=email_uid,
                folder_name=folder_name,
                account_id=int(account_id),
                sender_email=sender_email,
                subject=subject,
                flag_reason=flag_reason,
                created_by='web_bulk'
            )
            
            if success:
                successful_flags += 1
                results.append({
                    "email_uid": email_uid,
                    "success": True,
                    "message": "Flagged successfully"
                })
            else:
                failed_flags += 1
                results.append({
                    "email_uid": email_uid,
                    "success": False,
                    "message": "Failed to flag"
                })
        
        return {
            "success": True,
            "message": f"Bulk flagging completed: {successful_flags} successful, {failed_flags} failed",
            "successful_flags": successful_flags,
            "failed_flags": failed_flags,
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Bulk flag emails error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error bulk flagging emails: {str(e)}"}

@app.post("/api/emails/flag-for-deletion")
async def flag_email_for_deletion(request: Request):
    """Flag an email for deletion (override preservation decision)"""
    print("🗑️ FLAG EMAIL FOR DELETION API called")
    
    try:
        data = await request.json()
        
        # Extract required fields
        email_uid = data.get('email_uid')
        folder_name = data.get('folder_name')
        account_id = data.get('account_id')
        
        # Extract optional fields
        session_id = data.get('session_id')
        sender_email = data.get('sender_email')
        subject = data.get('subject')
        flag_reason = data.get('flag_reason', 'User requested deletion')
        
        # Validate required fields
        if not all([email_uid, folder_name, account_id]):
            return {
                "success": False,
                "message": "Missing required fields: email_uid, folder_name, account_id"
            }
        
        # Flag the email for deletion
        success = db.flag_email_for_deletion(
            email_uid=email_uid,
            folder_name=folder_name,
            account_id=int(account_id),
            session_id=session_id,
            sender_email=sender_email,
            subject=subject,
            flag_reason=flag_reason,
            created_by='web_user'
        )
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_uid} flagged for deletion",
                "email_uid": email_uid,
                "folder_name": folder_name
            }
        else:
            return {
                "success": False,
                "message": "Failed to flag email for deletion"
            }
            
    except Exception as e:
        print(f"❌ Flag email for deletion error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error flagging email for deletion: {str(e)}"}

@app.get("/api/emails/flag-status-detailed/{account_id}/{folder_name}/{email_uid}")
async def check_detailed_flag_status(account_id: int, folder_name: str, email_uid: str):
    """Check detailed flag status for a specific email (both protect and delete flags)"""
    print(f"🔍 CHECK DETAILED FLAG STATUS API called for {email_uid}")
    
    try:
        # Get flag type for the email
        flag_type = db.get_email_flag_type(
            email_uid=email_uid,
            folder_name=folder_name,
            account_id=account_id
        )
        
        # Check specific flag types
        is_protected = db.is_email_flagged(email_uid, folder_name, account_id)
        is_flagged_for_deletion = db.is_email_flagged_for_deletion(email_uid, folder_name, account_id)
        
        return {
            "success": True,
            "email_uid": email_uid,
            "folder_name": folder_name,
            "account_id": account_id,
            "flag_type": flag_type,
            "is_protected": is_protected,
            "is_flagged_for_deletion": is_flagged_for_deletion,
            "has_any_flag": flag_type is not None
        }
        
    except Exception as e:
        print(f"❌ Check detailed flag status error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error checking detailed flag status: {str(e)}"}

@app.get("/api/emails/deletion-flagged")
async def get_deletion_flagged_emails(account_id: int = None, limit: int = 100):
    """Get list of emails flagged for deletion"""
    print("🗑️ GET DELETION FLAGGED EMAILS API called")
    
    try:
        # Get deletion-flagged emails specifically
        deletion_flagged_emails = db.get_flagged_emails(account_id=account_id, limit=limit, flag_type='DELETE')
        deletion_flagged_count = db.get_flagged_count(account_id=account_id, flag_type='DELETE')
        
        return {
            "success": True,
            "deletion_flagged_emails": deletion_flagged_emails,
            "total_count": deletion_flagged_count,
            "returned_count": len(deletion_flagged_emails)
        }
        
    except Exception as e:
        print(f"❌ Get deletion flagged emails error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error getting deletion flagged emails: {str(e)}"}

@app.post("/api/flag-for-research")
async def flag_email_for_research(request: Request):
    """Flag an email for research investigation"""
    print("🔍 FLAG EMAIL FOR RESEARCH API called")
    
    try:
        data = await request.json()
        
        # Extract required fields
        email_uid = data.get('email_uid')
        folder_name = data.get('folder_name')
        account_id = data.get('account_id')
        
        # Extract optional fields
        session_id = data.get('session_id')
        sender_email = data.get('sender_email')
        subject = data.get('subject')
        flag_reason = data.get('flag_reason', 'User requested classification investigation')
        
        # Validate required fields
        if not all([email_uid, folder_name, account_id]):
            return {
                "success": False,
                "message": "Missing required fields: email_uid, folder_name, account_id"
            }
        
        # Add research flag using the same database method but with RESEARCH flag type
        success = db.flag_email_for_research(
            email_uid=email_uid,
            folder_name=folder_name,
            account_id=account_id,
            session_id=session_id,
            sender_email=sender_email,
            subject=subject,
            flag_reason=flag_reason,
            created_by='web_user'
        )
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_uid} flagged for research",
                "email_uid": email_uid
            }
        else:
            return {
                "success": False,
                "message": "Failed to flag email for research"
            }
            
    except Exception as e:
        print(f"❌ Flag email for research error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error flagging email for research: {str(e)}"}

@app.post("/api/unflag-research")
async def unflag_email_research(request: Request):
    """Remove research flag from an email"""
    print("🔍 UNFLAG RESEARCH API called")
    
    try:
        data = await request.json()
        
        # Extract required fields
        email_uid = data.get('email_uid')
        folder_name = data.get('folder_name')
        account_id = data.get('account_id')
        
        # Validate required fields
        if not all([email_uid, folder_name, account_id]):
            return {
                "success": False,
                "message": "Missing required fields: email_uid, folder_name, account_id"
            }
        
        # Unflag the email
        success = db.unflag_email(
            email_uid=email_uid,
            folder_name=folder_name,
            account_id=account_id
        )
        
        if success:
            return {
                "success": True,
                "message": f"Email {email_uid} research flag removed",
                "email_uid": email_uid
            }
        else:
            return {
                "success": False,
                "message": "Failed to remove research flag (may not have been flagged)"
            }
    
    except Exception as e:
        print(f"❌ Unflag research error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error removing research flag: {str(e)}"}

@app.get("/api/emails/research-flagged")
async def get_research_flagged_emails(account_id: int = None, limit: int = 100):
    """Get list of emails flagged for research"""
    print("🔍 GET RESEARCH FLAGGED EMAILS API called")
    
    try:
        # Get research-flagged emails specifically
        research_flagged_emails = db.get_flagged_emails(account_id=account_id, limit=limit, flag_type='RESEARCH')
        research_flagged_count = db.get_flagged_count(account_id=account_id, flag_type='RESEARCH')
        
        return {
            "success": True,
            "research_flagged_emails": research_flagged_emails,
            "total_count": research_flagged_count,
            "returned_count": len(research_flagged_emails)
        }
        
    except Exception as e:
        print(f"❌ Get research flagged emails error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error getting research flagged emails: {str(e)}"}


# ========================================
# CATEGORY VALIDATION ROUTES
# ========================================

@app.get("/validate", response_class=HTMLResponse)
async def category_validation_page(request: Request):
    """Category Validation Page - Rebuilt from Scratch"""
    print("🔍 CATEGORY VALIDATION page accessed")
    
    try:
        # Get all categories with email counts
        categories_data = db.execute_query("""
            SELECT category, 
                   COUNT(*) as total,
                   SUM(CASE WHEN user_validated = 0 THEN 1 ELSE 0 END) as unvalidated,
                   SUM(CASE WHEN user_validated = 1 THEN 1 ELSE 0 END) as validated_correct
            FROM processed_emails_bulletproof 
            WHERE category IS NOT NULL 
            AND action = 'DELETED'
            GROUP BY category 
            HAVING COUNT(*) > 0
            ORDER BY unvalidated DESC, total DESC
        """)
        
        # Process categories for template
        categories = []
        for cat in categories_data:
            validation_rate = (cat['validated_correct'] / cat['total'] * 100) if cat['total'] > 0 else 0
            categories.append({
                'category': cat['category'],
                'total': cat['total'],
                'unvalidated': cat['unvalidated'],
                'validated_correct': cat['validated_correct'],
                'validation_rate': validation_rate
            })
        
        context = {
            'request': request,
            'categories': categories
        }
        
        return templates.TemplateResponse("pages/validate.html", context)
        
    except Exception as e:
        print(f"❌ Error loading validation page: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"<h1>Error loading validation page: {e}</h1>")

@app.get("/api/validation/emails/{category}")
async def get_emails_for_validation(category: str, page: int = 1):
    """Get unvalidated emails for a specific category"""
    print(f"📧 GET VALIDATION EMAILS for category: {category}, page: {page}")
    
    try:
        offset = (page - 1) * 10  # 10 emails per page
        
        # Get unvalidated emails for category  
        # Include both DELETED spam and misclassified DELETED HAM emails
        emails = db.execute_query("""
            SELECT id, sender_email, subject, category, confidence_score, timestamp,
                   user_validated, validation_timestamp, action
            FROM processed_emails_bulletproof 
            WHERE category = ? 
            AND action = 'DELETED'
            AND user_validated = 0
            ORDER BY timestamp DESC
            LIMIT 10 OFFSET ?
        """, (category, offset))
        
        # Get total count for pagination
        total_result = db.execute_query("""
            SELECT COUNT(*) as total
            FROM processed_emails_bulletproof 
            WHERE category = ? 
            AND action = 'DELETED'
            AND user_validated = 0
        """, (category,))
        
        total_unvalidated = total_result[0]['total'] if total_result else 0
        total_pages = (total_unvalidated + 9) // 10  # Ceiling division
        
        return {
            "success": True,
            "emails": emails,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_emails": total_unvalidated,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        print(f"❌ Get validation emails error: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/validation/feedback")
async def submit_validation_feedback(request: Request):
    """Submit thumbs up/down validation feedback with ML training integration"""
    print("👍👎 VALIDATION FEEDBACK submitted")
    
    try:
        feedback_data = await request.json()
        email_id = feedback_data.get('email_id')
        feedback = feedback_data.get('feedback')  # 'up' or 'down'
        
        print(f"📧 Feedback: email_id={email_id}, feedback={feedback}")
        
        if not email_id or feedback not in ['up', 'down']:
            print(f"❌ Invalid feedback data: {feedback_data}")
            return {"success": False, "message": "Invalid feedback data"}
        
        # Get email data for feedback storage
        email_data = db.execute_query("""
            SELECT id, sender_email, subject, category, confidence_score, uid
            FROM processed_emails_bulletproof 
            WHERE id = ?
        """, (email_id,))
        
        if not email_data:
            return {"success": False, "message": "Email not found"}
        
        email = email_data[0]
        
        if feedback == 'up':
            # Thumbs up - mark as validated correct
            print(f"👍 Marking email {email_id} as correctly classified")
            
            # Update processed_emails_bulletproof
            rows_updated = db.execute_update("""
                UPDATE processed_emails_bulletproof 
                SET user_validated = 1, validation_timestamp = datetime('now', 'localtime')
                WHERE id = ?
            """, (email_id,))
            
            # Store in user_feedback table for ML training
            feedback_id = db.execute_insert("""
                INSERT INTO user_feedback (
                    email_uid, sender, subject, original_classification, 
                    user_classification, feedback_type, timestamp, processed
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), FALSE)
            """, (
                email['uid'] or f"internal_{email_id}",
                email['sender_email'], 
                email['subject'],
                email['category'],
                email['category'],  # Same category = correct
                'correct'
            ))
            
            print(f"✅ Updated {rows_updated} rows for thumbs up, stored feedback {feedback_id}")
            
            # Trigger async ML training for positive feedback
            try:
                _trigger_ml_training_async(feedback_type='correct')
            except Exception as e:
                print(f"⚠️ ML training trigger failed: {e}")
            
            return {"success": True, "message": "Email marked as correctly classified"}
            
        elif feedback == 'down':
            # Thumbs down - cycle to next logical classification
            print(f"👎 Finding next logical classification for email {email_id}...")
            
            original_category = email['category']
            
            try:
                # Get next logical classification alternative
                new_category = get_next_classification_alternative(
                    email['sender_email'], 
                    email['subject'], 
                    original_category,
                    email_id
                )
                
                # Set confidence based on category type
                if new_category in ['Health & Medical Spam', 'Financial & Investment Spam', 'Phishing']:
                    new_confidence = 0.85  # High confidence for specific categories
                elif new_category in ['Generic Spam', 'Promotional Email']:
                    new_confidence = 0.60  # Lower confidence for generic categories
                else:
                    new_confidence = 0.75  # Medium confidence for other specific categories
                
                if new_category and new_category != 'UNKNOWN':
                    # Update with new classification and reset validation status
                    rows_updated = db.execute_update("""
                        UPDATE processed_emails_bulletproof 
                        SET category = ?, confidence_score = ?, user_validated = 0, validation_timestamp = NULL
                        WHERE id = ?
                    """, (new_category, new_confidence, email_id))
                    
                    # Store corrected feedback in user_feedback table for ML training
                    feedback_id = db.execute_insert("""
                        INSERT INTO user_feedback (
                            email_uid, sender, subject, original_classification, 
                            user_classification, feedback_type, timestamp, processed
                        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), FALSE)
                    """, (
                        email['uid'] or f"internal_{email_id}",
                        email['sender_email'], 
                        email['subject'],
                        original_category,
                        new_category,  # New corrected category
                        'incorrect'
                    ))
                    
                    print(f"✅ Email reclassified: {original_category} → {new_category} (confidence: {new_confidence:.2f})")
                    print(f"📊 Stored correction feedback {feedback_id} for ML training")
                    
                    # Trigger async ML training for negative feedback (more important)
                    try:
                        _trigger_ml_training_async(feedback_type='incorrect')
                    except Exception as e:
                        print(f"⚠️ ML training trigger failed: {e}")
                    
                    return {
                        "success": True, 
                        "message": f"Email reclassified from '{original_category}' to '{new_category}'",
                        "reclassification": {
                            "original_category": original_category,
                            "new_category": new_category,
                            "confidence": round(new_confidence, 2)
                        }
                    }
                else:
                    # Classification failed, just mark as thumbs down for manual review
                    rows_updated = db.execute_update("""
                        UPDATE processed_emails_bulletproof 
                        SET user_validated = -1, validation_timestamp = datetime('now', 'localtime')
                        WHERE id = ?
                    """, (email_id,))
                    
                    # Still store the negative feedback for learning
                    feedback_id = db.execute_insert("""
                        INSERT INTO user_feedback (
                            email_uid, sender, subject, original_classification, 
                            user_classification, feedback_type, timestamp, processed
                        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), FALSE)
                    """, (
                        email['uid'] or f"internal_{email_id}",
                        email['sender_email'], 
                        email['subject'],
                        original_category,
                        "Manual Review Required",
                        'incorrect'
                    ))
                    
                    print(f"📊 Stored failed reclassification feedback {feedback_id} for ML training")
                    
                    return {
                        "success": True, 
                        "message": "Email marked for manual reclassification (auto-classification failed)",
                        "reclassification": {
                            "original_category": original_category,
                            "new_category": "Manual Review Required",
                            "confidence": 0.0
                        }
                    }
                    
            except Exception as e:
                print(f"❌ Auto-reclassification failed: {e}")
                # Fall back to just marking as thumbs down
                rows_updated = db.execute_update("""
                    UPDATE processed_emails_bulletproof 
                    SET user_validated = -1, validation_timestamp = datetime('now', 'localtime')
                    WHERE id = ?
                """, (email_id,))
                
                # Store error feedback for debugging
                try:
                    feedback_id = db.execute_insert("""
                        INSERT INTO user_feedback (
                            email_uid, sender, subject, original_classification, 
                            user_classification, feedback_type, timestamp, processed
                        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), FALSE)
                    """, (
                        email['uid'] or f"internal_{email_id}",
                        email['sender_email'], 
                        email['subject'],
                        original_category,
                        f"Error: {str(e)}",
                        'incorrect'
                    ))
                except:
                    pass  # Don't fail on feedback storage errors
                
                return {
                    "success": True, 
                    "message": f"Email marked for manual reclassification (error: {str(e)})",
                    "reclassification": {
                        "original_category": original_category,
                        "new_category": "Manual Review Required",
                        "confidence": 0.0
                    }
                }
        
    except Exception as e:
        print(f"❌ Validation feedback error: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/validation/save")
async def save_email_for_protection(request: Request):
    """Save email for permanent protection from future deletion"""
    print("💾 SAVE EMAIL API called")
    
    try:
        # Parse request data
        request_data = await request.json()
        email_id = request_data.get('email_id')
        
        print(f"💾 Save: email_id={email_id}")
        
        if not email_id:
            print(f"❌ Invalid save data: {request_data}")
            return {"success": False, "message": "Invalid email ID"}
        
        # Get the email data for pattern extraction
        email_data = db.execute_query("""
            SELECT id, sender_email, subject, category, confidence_score, sender_domain
            FROM processed_emails_bulletproof 
            WHERE id = ?
        """, (email_id,))
        
        if not email_data:
            return {"success": False, "message": "Email not found"}
        
        email = email_data[0]
        print(f"💾 Saving email: {email['sender_email']} | {email['subject']}")
        
        # Step 1: Mark email as user protected and reclassify as "Not Spam"
        rows_updated = db.execute_update("""
            UPDATE processed_emails_bulletproof 
            SET user_protected = 1, 
                protection_date = datetime('now', 'localtime'),
                category = 'Not Spam',
                confidence_score = 0.95,
                user_validated = 1,
                validation_timestamp = datetime('now', 'localtime')
            WHERE id = ?
        """, (email_id,))
        
        print(f"✅ Email marked as protected and reclassified to 'Not Spam'")
        
        # Step 2: Extract and store protection patterns
        protection_patterns = []
        patterns_stored = 0
        
        # Extract sender email pattern
        if email['sender_email']:
            try:
                db.execute_update("""
                    INSERT OR IGNORE INTO protected_patterns 
                    (pattern_type, pattern_value, confidence_score, source_email_id, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, ('sender', email['sender_email'].lower(), 0.90, email_id, f"User saved email from {email['sender_email']}"))
                patterns_stored += 1
                protection_patterns.append({'type': 'sender', 'value': email['sender_email']})
            except Exception as e:
                print(f"⚠️ Error storing sender pattern: {e}")
        
        # Extract domain pattern
        if email['sender_domain']:
            try:
                db.execute_update("""
                    INSERT OR IGNORE INTO protected_patterns 
                    (pattern_type, pattern_value, confidence_score, source_email_id, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, ('domain', email['sender_domain'].lower(), 0.75, email_id, f"User saved email from domain {email['sender_domain']}"))
                patterns_stored += 1
                protection_patterns.append({'type': 'domain', 'value': email['sender_domain']})
            except Exception as e:
                print(f"⚠️ Error storing domain pattern: {e}")
        
        # Extract subject keywords (simple keyword extraction)
        if email['subject']:
            subject_lower = email['subject'].lower()
            # Look for newsletter indicators
            if any(keyword in subject_lower for keyword in ['newsletter', 'update', 'notification', 'alert', 'digest']):
                try:
                    db.execute_update("""
                        INSERT OR IGNORE INTO protected_patterns 
                        (pattern_type, pattern_value, confidence_score, source_email_id, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('subject_keyword', 'newsletter_pattern', 0.60, email_id, f"Newsletter pattern from: {email['subject'][:50]}"))
                    patterns_stored += 1
                    protection_patterns.append({'type': 'subject_keyword', 'value': 'newsletter_pattern'})
                except Exception as e:
                    print(f"⚠️ Error storing newsletter pattern: {e}")
            
            # Look for promotional indicators  
            if any(keyword in subject_lower for keyword in ['sale', 'offer', 'deal', 'discount', 'promo']):
                try:
                    db.execute_update("""
                        INSERT OR IGNORE INTO protected_patterns 
                        (pattern_type, pattern_value, confidence_score, source_email_id, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('subject_keyword', 'promotional_pattern', 0.55, email_id, f"Promotional pattern from: {email['subject'][:50]}"))
                    patterns_stored += 1
                    protection_patterns.append({'type': 'subject_keyword', 'value': 'promotional_pattern'})
                except Exception as e:
                    print(f"⚠️ Error storing promotional pattern: {e}")
        
        protection_message = f"Protecting emails from {email['sender_domain'] or email['sender_email']}"
        
        print(f"✅ Extracted and stored {patterns_stored} protection patterns")
        
        return {
            "success": True, 
            "message": f"Email saved and protected from future deletion",
            "protection_message": protection_message,
            "patterns_learned": patterns_stored,
            "reclassification": {
                "original_category": email['category'],
                "new_category": "Not Spam",
                "confidence": 0.95
            }
        }
        
    except Exception as e:
        print(f"❌ Save email API error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error saving email: {str(e)}"}

@app.post("/api/reclassify-thumbs-down")
async def reclassify_thumbs_down_emails():
    """Reclassify all emails marked with thumbs down"""
    print("🔄 RECLASSIFY THUMBS DOWN API called")
    
    try:
        # Get all emails with thumbs down (user_validated = -1)
        thumbs_down_emails = db.execute_query("""
            SELECT id, sender_email, subject, category, confidence_score
            FROM processed_emails_bulletproof 
            WHERE user_validated = -1 
            AND action = 'DELETED'
            ORDER BY timestamp DESC
        """)
        
        if not thumbs_down_emails:
            return {
                "success": True,
                "summary": {
                    "total_processed": 0,
                    "reclassified": 0,
                    "category_breakdown": {},
                    "message": "No emails marked for reclassification"
                }
            }
        
        print(f"📊 Found {len(thumbs_down_emails)} emails to reclassify")
        
        # Initialize the ensemble classifier
        try:
            from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
            classifier = EnsembleHybridClassifier()
            print("✅ Ensemble classifier initialized")
        except Exception as e:
            print(f"❌ Failed to initialize classifier: {e}")
            return {"success": False, "message": f"Classifier initialization failed: {str(e)}"}
        
        # Reclassify each email
        reclassified_count = 0
        category_breakdown = {}
        
        for email in thumbs_down_emails:
            try:
                # Run classification
                result = classifier.classify_email(
                    sender=email['sender_email'],
                    subject=email['subject'],
                    body="",  # We don't have body content stored
                    headers=""
                )
                
                new_category = result.get('category', 'UNKNOWN')
                new_confidence = result.get('confidence', 0.0)
                
                # Only update if we got a valid new category
                if new_category and new_category != 'UNKNOWN':
                    # Update the email in database
                    db.execute_update("""
                        UPDATE processed_emails_bulletproof 
                        SET category = ?, confidence_score = ?, user_validated = 0, validation_timestamp = NULL
                        WHERE id = ?
                    """, (new_category, new_confidence, email['id']))
                    
                    reclassified_count += 1
                    category_breakdown[new_category] = category_breakdown.get(new_category, 0) + 1
                    
                    if reclassified_count % 10 == 0:
                        print(f"   Processed {reclassified_count}/{len(thumbs_down_emails)}...")
                else:
                    # Reset validation status even if classification failed
                    db.execute_update("""
                        UPDATE processed_emails_bulletproof 
                        SET user_validated = 0, validation_timestamp = NULL
                        WHERE id = ?
                    """, (email['id'],))
                
            except Exception as e:
                print(f"❌ Error reclassifying email {email['id']}: {e}")
                # Reset validation status on error
                db.execute_update("""
                    UPDATE processed_emails_bulletproof 
                    SET user_validated = 0, validation_timestamp = NULL
                    WHERE id = ?
                """, (email['id'],))
        
        print(f"✅ Reclassification complete: {reclassified_count}/{len(thumbs_down_emails)} emails reclassified")
        
        return {
            "success": True,
            "summary": {
                "total_processed": len(thumbs_down_emails),
                "reclassified": reclassified_count,
                "category_breakdown": category_breakdown,
                "message": f"Successfully reclassified {reclassified_count} emails"
            }
        }
        
    except Exception as e:
        print(f"❌ Reclassification API error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/last-import/info")
async def get_last_import_info():
    """Get information about the last import session"""
    try:
        # Get the most recent non-preview session
        last_session = db.execute_query("""
            SELECT s.id, s.account_id, s.start_time, s.end_time, 
                   s.total_deleted, s.total_preserved, s.session_type,
                   a.email_address as account_email
            FROM sessions s
            LEFT JOIN accounts a ON s.account_id = a.id
            WHERE s.session_type IS NULL OR s.session_type != 'preview'
            ORDER BY s.start_time DESC 
            LIMIT 1
        """)
        
        if not last_session:
            return {"success": False, "message": "No import sessions found"}
        
        session = last_session[0]
        
        # Get count of emails from this session
        email_count = db.execute_query("""
            SELECT COUNT(*) as count
            FROM processed_emails_bulletproof 
            WHERE session_id = ?
        """, (session['id'],))
        
        total_emails = email_count[0]['count'] if email_count else 0
        
        return {
            "success": True,
            "session": {
                "id": session['id'],
                "account_email": session['account_email'],
                "start_time": session['start_time'],
                "end_time": session['end_time'],
                "total_emails": total_emails,
                "total_deleted": session['total_deleted'],
                "total_preserved": session['total_preserved'],
                "session_type": session['session_type']
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting last import info: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/last-import/remove")
async def remove_last_import():
    """Remove all emails from the last import session"""
    try:
        # Get the most recent non-preview session
        last_session = db.execute_query("""
            SELECT s.id, s.account_id, s.start_time, s.end_time,
                   a.email_address as account_email
            FROM sessions s
            LEFT JOIN accounts a ON s.account_id = a.id
            WHERE s.session_type IS NULL OR s.session_type != 'preview'
            ORDER BY s.start_time DESC 
            LIMIT 1
        """)
        
        if not last_session:
            return {"success": False, "message": "No import sessions found"}
        
        session = last_session[0]
        session_id = session['id']
        
        # Count emails to be removed
        email_count = db.execute_query("""
            SELECT COUNT(*) as count
            FROM processed_emails_bulletproof 
            WHERE session_id = ?
        """, (session_id,))
        
        emails_to_remove = email_count[0]['count'] if email_count else 0
        
        if emails_to_remove == 0:
            return {"success": False, "message": "No emails found for this session"}
        
        # Remove emails from the last import session
        db.execute_update("""
            DELETE FROM processed_emails_bulletproof 
            WHERE session_id = ?
        """, (session_id,))
        
        # Also remove the session record
        db.execute_update("""
            DELETE FROM sessions 
            WHERE id = ?
        """, (session_id,))
        
        print(f"✅ Removed last import: {emails_to_remove} emails from session {session_id}")
        
        return {
            "success": True,
            "message": f"Successfully removed {emails_to_remove} emails from last import",
            "details": {
                "emails_removed": emails_to_remove,
                "session_id": session_id,
                "account_email": session['account_email'],
                "import_time": session['start_time']
            }
        }
        
    except Exception as e:
        print(f"❌ Error removing last import: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/report", response_class=HTMLResponse)
async def report_page(request: Request):
    """Last Import Processing Report with detailed breakdown"""
    try:
        # Get the most recent import session
        last_session = db.execute_query("""
            SELECT s.id, s.account_id, s.start_time, s.end_time,
                   s.total_deleted, s.total_preserved, s.total_validated,
                   a.email_address as account_email
            FROM sessions s
            LEFT JOIN accounts a ON s.account_id = a.id
            WHERE s.session_type IS NULL OR s.session_type != 'preview'
            ORDER BY s.start_time DESC 
            LIMIT 1
        """)
        
        if not last_session:
            return templates.TemplateResponse(
                "pages/report.html",
                {
                    "request": request,
                    "session_info": None,
                    "stats": {},
                    "category_stats": [],
                    "confidence_stats": [],
                    "validation_stats": [],
                    "category_chart_data": {"labels": [], "values": []}
                }
            )
        
        session = last_session[0]
        session_id = session['id']
        
        # Get total processing stats
        total_stats = db.execute_query("""
            SELECT 
                COUNT(*) as total_emails,
                SUM(CASE WHEN action = 'DELETED' THEN 1 ELSE 0 END) as total_deleted,
                SUM(CASE WHEN action = 'PRESERVED' THEN 1 ELSE 0 END) as total_preserved
            FROM processed_emails_bulletproof 
            WHERE session_id = ?
        """, (session_id,))
        
        stats = dict(total_stats[0]) if total_stats else {'total_emails': 0, 'total_deleted': 0, 'total_preserved': 0}
        stats['total_validated'] = session['total_validated'] if session['total_validated'] else 0
        
        # Get spam categories breakdown for DELETED emails
        deleted_categories = db.execute_query("""
            SELECT category, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM processed_emails_bulletproof 
                                                   WHERE session_id = ? AND action = 'DELETED'), 0), 1) as percentage
            FROM processed_emails_bulletproof 
            WHERE session_id = ? AND action = 'DELETED'
            GROUP BY category 
            ORDER BY count DESC
        """, (session_id, session_id))
        
        # Get preserved categories breakdown
        preserved_categories = db.execute_query("""
            SELECT category, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM processed_emails_bulletproof 
                                                   WHERE session_id = ? AND action = 'PRESERVED'), 0), 1) as percentage
            FROM processed_emails_bulletproof 
            WHERE session_id = ? AND action = 'PRESERVED'
            GROUP BY category 
            ORDER BY count DESC
        """, (session_id, session_id))
        
        # Get preservation reasons breakdown
        preservation_reasons = db.execute_query("""
            SELECT reason, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM processed_emails_bulletproof 
                                                   WHERE session_id = ? AND action = 'PRESERVED'), 0), 1) as percentage
            FROM processed_emails_bulletproof 
            WHERE session_id = ? AND action = 'PRESERVED'
            GROUP BY reason 
            ORDER BY count DESC
            LIMIT 10
        """, (session_id, session_id))
        
        # Get geographic data from raw_data JSON
        geographic_stats = db.execute_query("""
            SELECT 
                json_extract(raw_data, '$.sender_country_name') as country,
                json_extract(raw_data, '$.sender_country_code') as country_code,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM processed_emails_bulletproof 
                                                WHERE session_id = ? AND action = 'DELETED'), 0), 1) as percentage
            FROM processed_emails_bulletproof 
            WHERE session_id = ? 
                AND action = 'DELETED'
                AND json_extract(raw_data, '$.sender_country_name') IS NOT NULL
            GROUP BY country 
            ORDER BY count DESC
            LIMIT 10
        """, (session_id, session_id))
        
        # Calculate processing time
        start_time = session['start_time']
        end_time = session['end_time']
        processing_time = "Unknown"
        if start_time and end_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = (end_dt - start_dt).total_seconds()
                processing_time = f"{duration:.1f} seconds"
            except:
                processing_time = "Unknown"
        
        # Calculate percentages
        total_emails = stats['total_emails']
        deleted_pct = (stats['total_deleted'] / total_emails * 100) if total_emails > 0 else 0
        preserved_pct = (stats['total_preserved'] / total_emails * 100) if total_emails > 0 else 0
        
        # Get actual confidence score distribution
        confidence_distribution = db.execute_query("""
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.7 THEN 'High (70%+)'
                    WHEN confidence_score >= 0.4 THEN 'Medium (40-70%)'
                    ELSE 'Low (<40%)'
                END as level,
                COUNT(*) as count
            FROM processed_emails_bulletproof 
            WHERE session_id = ? AND confidence_score IS NOT NULL
            GROUP BY level
        """, (session_id,))
        
        # Convert to expected format
        total_with_scores = sum(c['count'] for c in confidence_distribution) if confidence_distribution else 0
        confidence_stats = []
        level_order = ['High (70%+)', 'Medium (40-70%)', 'Low (<40%)']
        
        for level in level_order:
            conf = next((c for c in confidence_distribution if c['level'] == level), None)
            if conf:
                percentage = (conf['count'] / total_with_scores * 100) if total_with_scores > 0 else 0
                confidence_stats.append({
                    "level": conf['level'],
                    "count": conf['count'],
                    "percentage": percentage
                })
            else:
                confidence_stats.append({
                    "level": level,
                    "count": 0,
                    "percentage": 0
                })
        
        # Prepare validation stats
        validation_stats = []
        if session['total_validated'] > 0:
            validation_stats = [
                {"method": "SPF/DKIM/DMARC", "count": session['total_validated']}
            ]
        
        # Prepare category chart data
        category_chart_data = {
            "labels": [cat['category'] for cat in deleted_categories] if deleted_categories else [],
            "values": [cat['count'] for cat in deleted_categories] if deleted_categories else []
        }
        
        # Prepare session info
        session_info = {
            "account_email": session['account_email'],
            "start_time": session['start_time'],
            "duration": processing_time
        }
        
        return templates.TemplateResponse(
            "pages/report.html",
            {
                "request": request,
                "session_info": session_info,
                "stats": stats,
                "deleted_pct": deleted_pct,
                "preserved_pct": preserved_pct,
                "category_stats": deleted_categories,
                "preserved_categories": preserved_categories,
                "preservation_reasons": preservation_reasons,
                "confidence_stats": confidence_stats,
                "validation_stats": validation_stats,
                "category_chart_data": category_chart_data,
                "geographic_stats": geographic_stats
            }
        )
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        
        return HTMLResponse(f"""
        <html>
        <head><title>Report Error</title></head>
        <body>
            <h1>Error Generating Report</h1>
            <p>Error: {str(e)}</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """, status_code=500)

# ==========================================
# SINGLE ACCOUNT FILTER INTERFACE
# ==========================================

@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Account selection page - lists all saved accounts"""
    try:
        # Import here to avoid circular imports
        from config.credentials import db_credentials
        
        # Load all saved accounts
        accounts_data = db_credentials.load_credentials()
        
        # Provider icons mapping
        provider_icons = {
            'iCloud': '🍎',
            'Gmail': '📧', 
            'Outlook': '🏢',
            'Yahoo': '🟣',
            'Custom': '⚙️'
        }
        
        # Format accounts for template
        accounts = []
        if accounts_data:
            for i, account in enumerate(accounts_data):
                provider = account.get('provider', 'Custom')
                icon = provider_icons.get(provider, '📧')
                last_used = account.get('last_used', 'Never')
                target_folders = account.get('target_folders', [])
                folder_count = len(target_folders) if target_folders else 0
                
                accounts.append({
                    'email_address': account.get('email_address', 'Unknown'),
                    'provider': provider,
                    'icon': icon,
                    'last_used': last_used,
                    'folder_count': folder_count,
                    'index': i
                })
        
        context = {
            'request': request,
            'accounts': accounts
        }
        
        return templates.TemplateResponse("pages/accounts.html", context)
        
    except Exception as e:
        print(f"❌ Error loading accounts: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"<h1>Error loading accounts: {e}</h1>")


@app.get("/single-account/{account_id}", response_class=HTMLResponse)
async def single_account_page(request: Request, account_id: str):
    """Single account filtering dashboard - replicates CLI functionality"""
    try:
        from config.credentials import db_credentials
        
        # Load account details
        accounts = db_credentials.load_credentials()
        
        # Handle "all" accounts special case
        if account_id == "all":
            # Create a virtual "all accounts" object
            account = {
                'email_address': 'All Accounts',
                'provider': f'Processing {len(accounts)} accounts',
                'target_folders': []
            }
            # Show target accounts instead of folders
            target_accounts = []
            for acc in accounts:
                folders = acc.get('target_folders', [])
                folder_count = len(folders) if folders else 0
                provider = acc.get('provider', 'Custom')
                target_accounts.append(f"{acc['email_address']} ({provider}) - {folder_count} folders")
            account['target_folders'] = target_accounts
        else:
            # Handle individual account
            try:
                account_idx = int(account_id)
                if account_idx >= len(accounts):
                    return HTMLResponse("""
                    <html><body>
                        <h1>Account Not Found</h1>
                        <a href="/accounts">← Back to Accounts</a>
                    </body></html>
                    """)
                account = accounts[account_idx]
                    
            except ValueError:
                return HTMLResponse("""
                <html><body>
                    <h1>Invalid Account ID</h1>
                    <a href="/accounts">← Back to Accounts</a>
                </body></html>
                """)
        
        provider_icons = {
            'iCloud': '🍎',
            'Gmail': '📧', 
            'Outlook': '🏢',
            'Yahoo': '🟣',
            'Custom': '⚙️'
        }
        
        provider = account.get('provider', 'Custom')
        # Special icon for "all accounts"
        if account_id == "all":
            icon = '🌐'
        else:
            icon = provider_icons.get(provider, '📧')
        target_folders = account.get('target_folders', [])
        
        context = {
            'request': request,
            'account': account,
            'account_id': account_id,
            'icon': icon,
            'provider': provider,
            'target_folders': target_folders
        }
        
        return templates.TemplateResponse("pages/single_account.html", context)
        
    except Exception as e:
        print(f"❌ Error loading single account page: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"<h1>Error loading account: {e}</h1>")

@app.get("/api/accounts")
async def get_accounts_api():
    """API endpoint to get all accounts"""
    try:
        from config.credentials import db_credentials
        accounts = db_credentials.load_credentials()
        
        # Remove sensitive data like passwords
        safe_accounts = []
        for i, account in enumerate(accounts):
            safe_account = {
                'id': i,
                'email_address': account.get('email_address', ''),
                'provider': account.get('provider', 'Custom'),
                'last_used': account.get('last_used', 'Never'),
                'target_folders': account.get('target_folders', []),
                'folder_count': len(account.get('target_folders', []))
            }
            safe_accounts.append(safe_account)
        
        return {"success": True, "accounts": safe_accounts}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/single-account/{account_id}/preview")
async def single_account_preview_api(account_id: str):
    """Preview mode for single account - calls EXACT CLI function with preview_mode=True"""
    try:
        # Import the EXACT CLI function that replicates the working CLI flow
        from atlas_email.core.processing_controller import run_exact_cli_processing_for_account
        from config.credentials import db_credentials
        from atlas_email.models.database import DatabaseManager
        
        # Helper function to get database account ID from array index
        def get_database_account_id(account_idx):
            """Map array index to database account ID"""
            accounts = db_credentials.load_credentials()
            if 0 <= account_idx < len(accounts):
                account_email = accounts[account_idx]['email_address']
                db = DatabaseManager()
                db_account = db.execute_query(
                    "SELECT id FROM accounts WHERE email_address = ?",
                    (account_email,)
                )
                if db_account:
                    return db_account[0][0]
            return account_idx + 1  # Fallback to 1-based index
        
        # Handle "all" accounts special case
        if account_id == "all":
            print(f"🔍 Running preview for ALL accounts")
            accounts = db_credentials.load_credentials()
            
            # Aggregate results from all accounts
            all_results = {
                'total_emails': 0,
                'total_deleted': 0,
                'total_preserved': 0,
                'categories': {},
                'account_email': f'All {len(accounts)} Accounts',
                'session_id': 'all_preview',
                'account_breakdown': [],
                'session_ids': []  # Collect individual session IDs for email details
            }
            
            # Process each account
            for idx, account in enumerate(accounts):
                print(f"🔍 Preview account {idx}: {account['email_address']}")
                try:
                    result = run_exact_cli_processing_for_account(idx, preview_mode=True)
                    
                    # Aggregate totals
                    all_results['total_emails'] += result.get('total_emails', 0)
                    all_results['total_deleted'] += result.get('total_deleted', 0)
                    all_results['total_preserved'] += result.get('total_preserved', 0)
                    
                    # Aggregate categories
                    for category, count in result.get('categories', {}).items():
                        all_results['categories'][category] = all_results['categories'].get(category, 0) + count
                    
                    # Add account breakdown
                    all_results['account_breakdown'].append({
                        'email': account['email_address'],
                        'deleted': result.get('total_deleted', 0),
                        'preserved': result.get('total_preserved', 0)
                    })
                    
                    # Collect session ID for email details
                    if result.get('session_id'):
                        all_results['session_ids'].append({
                            'session_id': result.get('session_id'),
                            'account_email': account['email_address']
                        })
                except Exception as e:
                    print(f"❌ Error processing account {idx}: {e}")
                    all_results['account_breakdown'].append({
                        'email': account['email_address'],
                        'error': str(e)
                    })
            
            return {"success": True, "data": all_results}
        else:
            # Handle single account
            account_idx = int(account_id)
            print(f"🔍 Calling EXACT CLI preview function for account {account_idx}")
            
            # Call the EXACT CLI function with preview_mode=True for preview
            result = run_exact_cli_processing_for_account(account_idx, preview_mode=True)
            
            # Add the database account ID to the result
            database_account_id = get_database_account_id(account_idx)
            if isinstance(result, dict):
                result['database_account_id'] = database_account_id
            
            return {"success": True, "data": result}
    except Exception as e:
        print(f"❌ Error calling EXACT CLI preview: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/single-account/{account_id}/process")
async def single_account_process_api(account_id: str):
    """Actual processing for single account - calls EXACT CLI deletion flow directly"""
    print("🍎🍎🍎 PROCESS ENDPOINT CALLED - USING EXACT CLI FLOW 🍎🍎🍎")
    try:
        # Import the EXACT CLI function that replicates the working CLI deletion flow
        from atlas_email.core.processing_controller import run_exact_cli_processing_for_account
        from config.credentials import db_credentials
        
        # Handle "all" accounts special case
        if account_id == "all":
            print(f"🍎 Running PROCESS for ALL accounts")
            accounts = db_credentials.load_credentials()
            
            # Aggregate results from all accounts
            all_results = {
                'total_emails': 0,
                'total_deleted': 0,
                'total_preserved': 0,
                'categories': {},
                'account_email': f'All {len(accounts)} Accounts',
                'session_id': 'all_process',
                'account_breakdown': [],
                'session_ids': []  # Collect individual session IDs for email details
            }
            
            # Process each account
            for idx, account in enumerate(accounts):
                print(f"🍎 Processing account {idx}: {account['email_address']}")
                try:
                    result = run_exact_cli_processing_for_account(idx, preview_mode=False)
                    
                    # Aggregate totals
                    all_results['total_emails'] += result.get('total_emails', 0)
                    all_results['total_deleted'] += result.get('total_deleted', 0)
                    all_results['total_preserved'] += result.get('total_preserved', 0)
                    
                    # Aggregate categories
                    for category, count in result.get('categories', {}).items():
                        all_results['categories'][category] = all_results['categories'].get(category, 0) + count
                    
                    # Add account breakdown
                    all_results['account_breakdown'].append({
                        'email': account['email_address'],
                        'deleted': result.get('total_deleted', 0),
                        'preserved': result.get('total_preserved', 0)
                    })
                    
                    # Collect session ID for email details
                    if result.get('session_id'):
                        all_results['session_ids'].append({
                            'session_id': result.get('session_id'),
                            'account_email': account['email_address']
                        })
                except Exception as e:
                    print(f"❌ Error processing account {idx}: {e}")
                    all_results['account_breakdown'].append({
                        'email': account['email_address'],
                        'error': str(e)
                    })
            
            return {"success": True, "data": all_results}
        else:
            # Handle single account
            account_idx = int(account_id)
            print(f"🍎 Calling EXACT CLI processing function for account {account_idx}")
            print("🍎 This uses the EXACT same flow as CLI: Main → Option 2 → Option 1 (iCloud) → Option 1 (delete)")
            
            # Call the EXACT CLI function with preview_mode=False for actual deletion
            cli_result = run_exact_cli_processing_for_account(account_idx, preview_mode=False)
            
            if cli_result["success"]:
                print(f"🍎 EXACT CLI processing SUCCESS: {cli_result['total_deleted']} deleted, {cli_result['total_preserved']} preserved")
                return {
                    "success": True, 
                    "data": {
                        "success": True,
                        "total_deleted": cli_result['total_deleted'],
                        "total_preserved": cli_result['total_preserved'],
                        "total_validated": cli_result['total_validated'],
                        "total_legitimate": cli_result['total_legitimate'],
                        "session_id": cli_result['session_id'],
                        "account_email": cli_result['account_email'],
                        "folders_processed": cli_result['folders_processed'],
                        "categories": cli_result['categories'],
                        "message": cli_result['message'],
                        "mode": "process"
                    }
                }
            else:
                print(f"🍎 EXACT CLI processing FAILED: {cli_result['message']}")
                return {"success": False, "error": cli_result['message']}
            
    except Exception as e:
        print(f"❌ Error calling EXACT CLI processing: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Error calling exact CLI processing: {str(e)}"}

@app.get("/api/single-account/{account_id}/emails/{session_id}")
async def get_account_session_emails(account_id: int, session_id: str):
    """Get individual email details for a specific account processing session"""
    try:
        from atlas_email.models.database import DatabaseManager
        
        # Initialize database connection
        db = DatabaseManager()
        
        # Handle undefined or invalid session_id
        if session_id == 'undefined' or not session_id:
            return {
                "success": False, 
                "error": "Invalid session ID. Please run preview/process first."
            }
        
        # Convert session_id to integer (database expects INTEGER type)
        try:
            session_id_int = int(session_id)
        except ValueError:
            return {
                "success": False, 
                "error": f"Invalid session ID format: {session_id}"
            }
        
        # Query individual emails from the session
        emails = db.execute_query("""
            SELECT 
                pe.id,
                pe.sender_email,
                pe.subject,
                pe.category,
                pe.confidence_score,
                pe.action,
                pe.timestamp,
                pe.sender_domain,
                pe.uid,
                pe.folder_name,
                s.account_id,
                CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as is_flagged,
                COALESCE(f.flag_type, '') as flag_type,
                CASE WHEN f.flag_type = 'PROTECT' THEN 1 ELSE 0 END as is_protected,
                CASE WHEN f.flag_type = 'DELETE' THEN 1 ELSE 0 END as is_flagged_for_deletion,
                CASE WHEN f.flag_type = 'RESEARCH' THEN 1 ELSE 0 END as is_research_flagged
            FROM processed_emails_bulletproof pe
            JOIN sessions s ON pe.session_id = s.id
            LEFT JOIN email_flags f ON (
                pe.uid = f.email_uid AND 
                pe.folder_name = f.folder_name AND 
                s.account_id = f.account_id AND 
                f.is_active = 1
            )
            WHERE pe.session_id = ?
            ORDER BY pe.timestamp DESC
        """, (session_id_int,))
        
        # Format the results for frontend display
        formatted_emails = []
        for email in emails:
            formatted_emails.append({
                'id': email[0],
                'sender': email[1] or 'Unknown',
                'subject': email[2] or '(No Subject)',
                'category': email[3] or 'Unclassified',
                'confidence': float(email[4]) if email[4] else 0.0,
                'action': email[5] or 'UNKNOWN',
                'timestamp': email[6] or '',
                'domain': email[7] or '',
                'uid': email[8] or '',
                'folder_name': email[9] or '',
                'account_id': email[10] or account_id,
                'is_flagged': bool(email[11]),
                'flag_type': email[12] or '',
                'is_protected': bool(email[13]),
                'is_flagged_for_deletion': bool(email[14]),
                'is_research_flagged': bool(email[15])
            })
        
        return {
            "success": True, 
            "emails": formatted_emails,
            "count": len(formatted_emails),
            "account_id": account_id,
            "session_id": session_id
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/single-account/{account_id}/all-emails")
async def get_all_account_emails(account_id: int):
    """Get all email details for a specific account (from all sessions)"""
    try:
        from atlas_email.models.database import DatabaseManager
        from config.credentials import db_credentials
        
        # Initialize database connection
        db = DatabaseManager()
        
        # Load account to get email address
        accounts = db_credentials.load_credentials()
        if account_id >= len(accounts):
            return {"success": False, "error": "Account not found"}
        
        account = accounts[account_id]
        account_email = account['email_address']
        
        # Query all emails for this account (last 30 days to avoid huge results)
        emails = db.execute_query("""
            SELECT 
                pe.id,
                pe.sender_email,
                pe.subject,
                pe.category,
                pe.confidence_score,
                pe.action,
                pe.timestamp,
                pe.sender_domain,
                pe.uid,
                pe.folder_name,
                s.account_id,
                s.id as session_id,
                CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as is_flagged,
                COALESCE(f.flag_type, '') as flag_type,
                CASE WHEN f.flag_type = 'PROTECT' THEN 1 ELSE 0 END as is_protected,
                CASE WHEN f.flag_type = 'DELETE' THEN 1 ELSE 0 END as is_flagged_for_deletion,
                CASE WHEN f.flag_type = 'RESEARCH' THEN 1 ELSE 0 END as is_research_flagged
            FROM processed_emails_bulletproof pe
            JOIN sessions s ON pe.session_id = s.id
            LEFT JOIN email_flags f ON (
                pe.uid = f.email_uid AND 
                pe.folder_name = f.folder_name AND 
                s.account_id = f.account_id AND 
                f.is_active = 1
            )
            WHERE pe.timestamp > datetime('now', '-30 days')
            AND EXISTS (
                SELECT 1 FROM sessions s2 
                WHERE s2.id = pe.session_id 
                AND s2.account_id = (
                    SELECT id FROM accounts WHERE email_address = ?
                )
            )
            ORDER BY pe.timestamp DESC
            LIMIT 200
        """, (account_email,))
        
        # Format the results for frontend display
        formatted_emails = []
        for email in emails:
            formatted_emails.append({
                'id': email[0],
                'sender': email[1] or 'Unknown',
                'subject': email[2] or '(No Subject)',
                'category': email[3] or 'Unclassified',
                'confidence': float(email[4]) if email[4] else 0.0,
                'action': email[5] or 'UNKNOWN',
                'timestamp': email[6] or '',
                'domain': email[7] or '',
                'uid': email[8] or '',
                'folder_name': email[9] or '',
                'account_id': email[10] or account_id,
                'session_id': email[11] or '',
                'is_flagged': bool(email[12]),
                'flag_type': email[13] or '',
                'is_protected': bool(email[14]),
                'is_flagged_for_deletion': bool(email[15]),
                'is_research_flagged': bool(email[16])
            })
        
        return {
            "success": True, 
            "emails": formatted_emails,
            "count": len(formatted_emails),
            "account_id": account_id,
            "account_email": account_email,
            "note": "Showing last 30 days, max 200 emails"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/all-accounts/emails")
async def get_all_accounts_emails(session_ids: str):
    """Get emails from multiple session IDs for 'all accounts' view"""
    try:
        from atlas_email.models.database import DatabaseManager
        import json
        
        # Initialize database connection
        db = DatabaseManager()
        
        # Parse session_ids parameter (JSON string of session info)
        try:
            session_info_list = json.loads(session_ids)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid session_ids format"}
        
        all_emails = []
        
        # Query emails for each session
        for session_info in session_info_list:
            session_id = session_info.get('session_id')
            account_email = session_info.get('account_email')
            
            if not session_id:
                continue
                
            # Query emails for this session
            emails = db.execute_query("""
                SELECT 
                    pe.id,
                    pe.sender_email,
                    pe.subject,
                    pe.category,
                    pe.confidence_score,
                    pe.action,
                    pe.timestamp,
                    pe.sender_domain,
                    pe.uid,
                    pe.folder_name,
                    s.account_id,
                    CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as is_flagged,
                    COALESCE(f.flag_type, '') as flag_type,
                    CASE WHEN f.flag_type = 'PROTECT' THEN 1 ELSE 0 END as is_protected,
                    CASE WHEN f.flag_type = 'DELETE' THEN 1 ELSE 0 END as is_flagged_for_deletion
                FROM processed_emails_bulletproof pe
                JOIN sessions s ON pe.session_id = s.id
                LEFT JOIN email_flags f ON (
                    pe.uid = f.email_uid AND 
                    pe.folder_name = f.folder_name AND 
                    s.account_id = f.account_id AND 
                    f.is_active = 1
                )
                WHERE pe.session_id = ?
                ORDER BY pe.timestamp DESC
            """, (session_id,))
            
            # Format emails and add account info
            for email in emails:
                formatted_email = {
                    'id': email[0],
                    'sender': email[1] or 'Unknown',
                    'subject': email[2] or '(No Subject)',
                    'category': email[3] or 'Unclassified',
                    'confidence': float(email[4]) if email[4] else 0.0,
                    'action': email[5] or 'UNKNOWN',
                    'timestamp': email[6] or '',
                    'domain': email[7] or '',
                    'uid': email[8] or '',
                    'folder_name': email[9] or '',
                    'account_id': email[10],
                    'is_flagged': bool(email[11]),
                    'flag_type': email[12] or '',
                    'is_protected': bool(email[13]),
                    'is_flagged_for_deletion': bool(email[14]),
                    'is_research_flagged': bool(email[15]),
                    'account_email': account_email  # Add account info for display
                }
                all_emails.append(formatted_email)
        
        # Sort by timestamp descending
        all_emails.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "success": True,
            "emails": all_emails,
            "count": len(all_emails),
            "session_count": len(session_info_list)
        }
        
    except Exception as e:
        print(f"❌ Error getting all accounts emails: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("🚀 Starting Fresh Mail Filter Web Interface...")
    print("📱 Rebuilt from scratch for reliability")
    print("🌐 Access at: http://localhost:8001")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
    except Exception as e:
        print(f"❌ Server error: {e}")
