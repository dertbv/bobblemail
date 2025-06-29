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
async def dashboard():
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
        print(f"👤 Accounts: {len(accounts) if accounts else 0}")
        
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
        for i, email in enumerate(latest_emails[:3]):
            print(f"  {i+1}. {email['timestamp']} - {email['action']} - {email['sender_email']}")
        
        return build_dashboard_html(stats, accounts, latest_emails)
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error: {e}</h1>"

def build_dashboard_html(stats, accounts, emails):
    """Build dashboard HTML"""
    
    # Build email rows
    email_rows = ""
    for email in emails:
        try:
            # Parse timestamp - already in local time, no timezone conversion needed
            dt = datetime.fromisoformat(email['timestamp'].replace('T', ' ').replace('Z', ''))
            time_display = dt.strftime("%H:%M:%S")
            date_display = dt.strftime("%m/%d")
        except:
            time_display = "Unknown"
            date_display = "Unknown"
        
        action_emoji = "🗑️" if email['action'] == 'DELETED' else "🛡️"
        action_color = "#dc3545" if email['action'] == 'DELETED' else "#28a745"
        
        sender = (email['sender_email'] or '')[:30] + "..." if len(email['sender_email'] or '') > 30 else (email['sender_email'] or '')
        subject = (email['subject'] or '')[:40] + "..." if len(email['subject'] or '') > 40 else (email['subject'] or '')
        category = email['category'] or 'Unknown'
        
        email_rows += f"""
            <tr>
                <td>{date_display}</td>
                <td>{time_display}</td>
                <td style="color: {action_color}; font-weight: bold;">{action_emoji} {email['action']}</td>
                <td>{category}</td>
                <td style="font-family: monospace; font-size: 0.9em;">{sender}</td>
                <td>{subject}</td>
            </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mail Filter Dashboard - Fresh</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no, user-scalable=yes">
        <meta http-equiv="refresh" content="30">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ 
                max-width: 1400px; 
                margin: 0 auto; 
                background: rgba(255,255,255,0.95); 
                border-radius: 20px; 
                padding: 30px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
                backdrop-filter: blur(10px);
            }}
            h1 {{ 
                color: #2c3e50; 
                text-align: center; 
                font-size: 2.5em; 
                margin-bottom: 30px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stats-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 25px; 
                margin-bottom: 40px; 
            }}
            .stat-card {{ 
                background: rgba(255,255,255,0.95);
                padding: 30px; 
                border-radius: 20px; 
                text-align: left; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                transform: translateY(0);
                transition: all 0.3s ease;
                border: 1px solid rgba(255,255,255,0.2);
                position: relative;
                overflow: hidden;
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            .stat-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            }}
            .stat-card:hover {{
                transform: translateY(-8px);
                box-shadow: 0 25px 50px rgba(0,0,0,0.2);
            }}
            .stat-card.email-accounts::before {{ background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); }}
            .stat-card.emails-processed::before {{ background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%); }}
            .stat-card.total-sessions::before {{ background: linear-gradient(90deg, #fa709a 0%, #fee140 100%); }}
            .stat-card.database-size::before {{ background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%); }}
            
            .stat-icon {{
                font-size: 3em;
                opacity: 0.8;
                flex-shrink: 0;
            }}
            .stat-content {{
                flex: 1;
            }}
            .stat-value {{ 
                font-size: 2.5em; 
                font-weight: 700; 
                margin-bottom: 5px;
                color: #2c3e50;
                line-height: 1;
            }}
            .stat-label {{ 
                font-size: 1.1em; 
                color: #34495e;
                font-weight: 600;
                margin-bottom: 3px;
            }}
            .stat-sublabel {{
                font-size: 0.85em;
                color: #7f8c8d;
                opacity: 0.8;
            }}
            .controls {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 15px; 
                margin: 30px 0; 
            }}
            .btn {{ 
                display: block; 
                padding: 15px 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                text-decoration: none; 
                text-align: center; 
                border-radius: 10px; 
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
            }}
            .btn:hover {{ 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            .btn-success {{ background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); }}
            .btn-danger {{ background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); }}
            .btn-info {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
            .btn-warning {{ background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); color: #333; }}
            .recent-activity {{ 
                margin-top: 40px; 
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }}
            .activity-table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px; 
            }}
            .activity-table th {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 10px; 
                text-align: left; 
                border: none;
                font-weight: 600;
            }}
            .activity-table th:first-child {{ border-top-left-radius: 10px; }}
            .activity-table th:last-child {{ border-top-right-radius: 10px; }}
            .activity-table td {{ 
                padding: 12px 10px; 
                border-bottom: 1px solid #eee; 
                vertical-align: top;
            }}
            .activity-table tbody tr:hover {{
                background: #f8f9fa;
            }}
            .status-indicator {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 0.9em;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            /* ===== MOBILE-RESPONSIVE CSS ===== */
            
            /* Table container for horizontal scroll */
            .table-container {{
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                margin: 15px 0;
                border-radius: 8px;
            }}
            
            /* iOS input fixes */
            input, select {{
                font-size: 16px; /* Prevents iOS zoom */
                -webkit-appearance: none;
            }}
            
            /* Touch-friendly buttons */
            .btn {{
                min-height: 44px; /* iOS/Android touch standard */
                min-width: 44px;
                -webkit-tap-highlight-color: transparent;
            }}
            
            /* Small phones: 320px - 480px */
            @media (max-width: 480px) {{
                body {{
                    padding: 5px;
                }}
                
                .container {{ 
                    padding: 10px; 
                    border-radius: 8px;
                }}
                
                h1 {{ 
                    font-size: 1.5em;
                    margin-bottom: 15px;
                }}
                
                .stats-grid {{ 
                    grid-template-columns: 1fr;
                    gap: 15px;
                }}
                
                .controls {{ 
                    grid-template-columns: 1fr;
                    gap: 10px;
                }}
                
                .stat-card {{ 
                    padding: 15px; 
                    flex-direction: column; 
                    text-align: center; 
                    gap: 10px; 
                }}
                
                .stat-icon {{ 
                    font-size: 2em; 
                }}
                
                .stat-value {{ 
                    font-size: 1.8em; 
                }}
                
                .btn {{ 
                    padding: 12px 15px; 
                    font-size: 0.9em; 
                }}
                
                .activity-table th,
                .activity-table td {{
                    padding: 8px 6px;
                    font-size: 0.8em;
                }}
                
                .status-indicator {{
                    position: static;
                    display: block;
                    text-align: center;
                    margin-bottom: 15px;
                    top: auto;
                    right: auto;
                }}
            }}
            
            /* Large phones/small tablets: 481px - 768px */
            @media (min-width: 481px) and (max-width: 768px) {{
                .container {{ 
                    padding: 15px; 
                }}
                
                h1 {{ 
                    font-size: 2em; 
                }}
                
                .stats-grid {{ 
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                }}
                
                .controls {{ 
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                }}
            }}
            
            /* Tablets: 769px - 1024px */
            @media (min-width: 769px) and (max-width: 1024px) {{
                .stats-grid {{ 
                    grid-template-columns: repeat(3, 1fr);
                    gap: 25px;
                }}
                
                .controls {{ 
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="status-indicator">🟢 Live Dashboard</div>
        
        <div class="container">
            <h1>🛡️ Mail Filter Dashboard</h1>
            
            <div class="stats-grid">
                <div class="stat-card email-accounts">
                    <div class="stat-icon">📧</div>
                    <div class="stat-content">
                        <div class="stat-value">{len(accounts) if accounts else 0}</div>
                        <div class="stat-label">Email Accounts</div>
                        <div class="stat-sublabel">{"Active" if accounts else "None configured"}</div>
                    </div>
                </div>
                <div class="stat-card emails-processed">
                    <div class="stat-icon">📊</div>
                    <div class="stat-content">
                        <div class="stat-value">{stats.get('processed_emails_count', 0):,}</div>
                        <div class="stat-label">Emails Processed</div>
                        <div class="stat-sublabel">Total lifetime</div>
                    </div>
                </div>
                <div class="stat-card total-sessions">
                    <div class="stat-icon">🎯</div>
                    <div class="stat-content">
                        <div class="stat-value">{stats.get('sessions_count', 0)}</div>
                        <div class="stat-label">Total Sessions</div>
                        <div class="stat-sublabel">Processing runs</div>
                    </div>
                </div>
                <div class="stat-card database-size">
                    <div class="stat-icon">💾</div>
                    <div class="stat-content">
                        <div class="stat-value">{stats.get('db_size_mb', 0):.1f}MB</div>
                        <div class="stat-label">Database Size</div>
                        <div class="stat-sublabel">SQLite storage</div>
                    </div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-success" onclick="runBatch()">🚀 Run Batch Processing</button>
                <a href="/accounts" class="btn btn-primary">🎯 Single Account Filter</a>
                <a href="/analytics" class="btn btn-warning">📊 Analytics & Reports</a>
                <a href="/report" class="btn btn-primary">📋 Last Import Report</a>
                <a href="/validate" class="btn btn-info">🔍 Category Validation</a>
                <a href="/timer" class="btn btn-info">⏰ Timer Control</a>
                <button class="btn" onclick="window.location.reload()">🔄 Refresh Data</button>
            </div>
            
            <div class="recent-activity">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">📋 Latest Email Activity</h2>
                <div class="table-container">
                    <table class="activity-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Action</th>
                            <th>Category</th>
                            <th>Sender</th>
                            <th>Subject</th>
                        </tr>
                    </thead>
                    <tbody>
                        {email_rows}
                    </tbody>
                    </table>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 40px; color: #666;">
                <small>Fresh Mail Filter Interface • Auto-refresh every 30 seconds • Last updated: {datetime.now().strftime('%H:%M:%S')}</small>
            </div>
        </div>
        
        <script>
            async function runBatch() {{
                if (!confirm('Run batch processing on all accounts? This will process and potentially delete spam emails.')) {{
                    return;
                }}
                
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '⏳ Processing...';
                btn.disabled = true;
                
                try {{
                    const response = await fetch('/api/batch/run', {{
                        method: 'POST'
                    }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert('✅ Batch processing completed successfully!');
                        window.location.reload();
                    }} else {{
                        alert('❌ Batch processing failed: ' + result.message);
                    }}
                }} catch (error) {{
                    alert('❌ Error: ' + error.message);
                }} finally {{
                    btn.textContent = originalText;
                    btn.disabled = false;
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return html

@app.get("/timer", response_class=HTMLResponse)
async def timer_control():
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
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Timer Control - Mail Filter</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: rgba(255,255,255,0.95); 
                border-radius: 20px; 
                padding: 30px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }}
            .back-link {{ 
                color: #667eea; 
                text-decoration: none; 
                margin-bottom: 20px; 
                display: inline-block;
                font-weight: 600;
            }}
            h1 {{ 
                color: #2c3e50; 
                text-align: center; 
                font-size: 2.5em; 
                margin-bottom: 30px;
            }}
            .status-card {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.08);
                border-left: 6px solid {'#28a745' if timer_active else '#dc3545'};
            }}
            .status-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            .status-row:last-child {{ margin-bottom: 0; }}
            .status-label {{
                font-weight: 600;
                color: #34495e;
            }}
            .status-value {{
                font-weight: 700;
                color: {'#28a745' if timer_active else '#dc3545'};
            }}
            .form-group {{ 
                margin: 20px 0; 
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            }}
            label {{ 
                display: block; 
                margin-bottom: 8px; 
                font-weight: 600;
                color: #34495e;
            }}
            input, select {{ 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #e9ecef; 
                border-radius: 8px; 
                font-size: 1em;
                transition: border-color 0.3s ease;
            }}
            input:focus, select:focus {{
                border-color: #667eea;
                outline: none;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            .button-group {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-top: 30px;
            }}
            .btn {{ 
                padding: 15px 20px; 
                border: none; 
                border-radius: 10px; 
                cursor: pointer; 
                font-size: 1em;
                font-weight: 600;
                transition: all 0.3s ease;
                text-decoration: none;
                text-align: center;
                display: block;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            .btn:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }}
            .btn-primary {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
            }}
            .btn-success {{ 
                background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); 
                color: white; 
            }}
            .btn-danger {{ 
                background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); 
                color: white; 
            }}
            .btn-warning {{ 
                background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); 
                color: #333; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>⏰ Timer Control</h1>
            
            <div class="status-card">
                <div class="status-row">
                    <div class="status-label">Status:</div>
                    <div class="status-value">{'🟢 Active' if timer_active else '🔴 Inactive'}</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Duration:</div>
                    <div class="status-value">{timer_minutes} minutes</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Mode:</div>
                    <div class="status-value">{'🔄 Repeating' if repeat_mode else '🔂 One-time'}</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Executions:</div>
                    <div class="status-value">{execution_count}</div>
                </div>
                {f'<div class="status-row"><div class="status-label">Time Remaining:</div><div class="status-value">{timer_details}</div></div>' if timer_details else ''}
            </div>
            
            <div class="form-group">
                <label for="minutes">Timer Duration (minutes):</label>
                <input type="number" id="minutes" name="minutes" value="{timer_minutes}" min="1" max="10080" placeholder="Enter minutes (1-10080)">
            </div>
            
            <div class="form-group">
                <label for="repeat">Timer Mode:</label>
                <select id="repeat" name="repeat">
                    <option value="false" {'selected' if not repeat_mode else ''}>One-time execution</option>
                    <option value="true" {'selected' if repeat_mode else ''}>Repeating timer</option>
                </select>
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="setTimer()">⚙️ Set Timer</button>
                <button class="btn btn-success" onclick="startTimer()" {'disabled' if timer_active else ''}>▶️ Start Timer</button>
                <button class="btn btn-danger" onclick="stopTimer()" {'disabled' if not timer_active else ''}>⏹️ Stop Timer</button>
                <button class="btn btn-warning" onclick="testBatch()">🧪 Test Batch Now</button>
            </div>
        </div>
        
        <script>
            async function setTimer() {{
                const minutes = document.getElementById('minutes').value;
                const repeat = document.getElementById('repeat').value;
                
                if (!minutes || minutes < 1) {{
                    alert('Please enter a valid duration (1+ minutes)');
                    return;
                }}
                
                try {{
                    const response = await fetch('/api/timer/set', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            minutes: parseInt(minutes),
                            repeat_mode: repeat === 'true'
                        }})
                    }});
                    
                    const result = await response.json();
                    alert(result.message);
                    if (result.success) location.reload();
                }} catch (error) {{
                    alert('Error setting timer: ' + error.message);
                }}
            }}
            
            async function startTimer() {{
                try {{
                    const response = await fetch('/api/timer/start', {{method: 'POST'}});
                    const result = await response.json();
                    alert(result.message);
                    if (result.success) location.reload();
                }} catch (error) {{
                    alert('Error starting timer: ' + error.message);
                }}
            }}
            
            async function stopTimer() {{
                try {{
                    const response = await fetch('/api/timer/stop', {{method: 'POST'}});
                    const result = await response.json();
                    alert(result.message);
                    if (result.success) location.reload();
                }} catch (error) {{
                    alert('Error stopping timer: ' + error.message);
                }}
            }}
            
            async function testBatch() {{
                if (confirm('Run batch processing now? This will process emails on all accounts.')) {{
                    try {{
                        const response = await fetch('/api/batch/run', {{method: 'POST'}});
                        const result = await response.json();
                        alert(result.message);
                    }} catch (error) {{
                        alert('Error running batch: ' + error.message);
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return html

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


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard():
    """Analytics and reporting dashboard"""
    print("📊 ANALYTICS DASHBOARD CALLED!")
    
    try:
        # Get comprehensive analytics data
        analytics_data = get_analytics_data()
        return build_analytics_html(analytics_data)
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return f"<h1>Analytics Error: {e}</h1>"

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
    
    return {
        'effectiveness': effectiveness,
        'categories': categories,
        'daily_activity': daily_activity,
        'spam_domains': spam_domains,
        'session_stats': session_stats,
        'account_breakdown_total': account_breakdown_total,
        'account_breakdown_spam': account_breakdown_spam
    }

def build_analytics_html(data):
    """Build analytics dashboard HTML"""
    
    # Calculate effectiveness metrics
    eff = data['effectiveness']
    total = eff.get('total_count', 0)
    deleted = eff.get('deleted_count', 0)
    preserved = eff.get('preserved_count', 0)
    effectiveness_rate = (deleted / total * 100) if total > 0 else 0
    
    # Build category chart data
    category_rows = ""
    max_percentage = max([cat['percentage'] for cat in data['categories']], default=1)
    
    for cat in data['categories']:
        percentage = cat['percentage']
        count = cat['count']
        category_name = cat['category'] or 'Unknown'
        
        # Normalize bar width - highest percentage gets 100% width
        bar_width = (percentage / max_percentage * 100) if max_percentage > 0 else 0
        
        category_rows += f"""
            <div class="chart-bar">
                <div class="bar-label">{category_name}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: {bar_width:.1f}%"></div>
                </div>
                <div class="bar-value">{count:,} ({percentage:.1f}%)</div>
            </div>
        """
    
    # Build daily activity chart
    activity_rows = ""
    for day in data['daily_activity']:
        date = day['date']
        deleted = day['deleted']
        preserved = day['preserved']
        total_day = deleted + preserved
        
        activity_rows += f"""
            <tr>
                <td>{date}</td>
                <td style="color: #dc3545; font-weight: bold;">{deleted:,}</td>
                <td style="color: #28a745; font-weight: bold;">{preserved:,}</td>
                <td>{total_day:,}</td>
            </tr>
        """
    
    # Build spam domains list
    domain_rows = ""
    for domain in data['spam_domains']:
        domain_name = domain['sender_domain']
        count = domain['count']
        
        domain_rows += f"""
            <tr>
                <td style="font-family: monospace; color: #dc3545;">{domain_name}</td>
                <td>{count:,}</td>
            </tr>
        """
    
    # Build account breakdown chart - TOTAL MAIL
    account_total_rows = ""
    max_account_total_percentage = max([acc['percentage'] for acc in data['account_breakdown_total']], default=1)
    
    for account in data['account_breakdown_total']:
        provider = account['provider']
        count = account['email_count']
        percentage = account['percentage']
        
        # Normalize bar width - highest percentage gets 100% width
        bar_width = (percentage / max_account_total_percentage * 100) if max_account_total_percentage > 0 else 0
        
        # Provider icons
        provider_icon = {
            'gmail': '📧',
            'icloud': '☁️', 
            'outlook': '📨',
            'yahoo': '📬',
            'aol': '📭'
        }.get(provider.lower(), '📮')
        
        account_total_rows += f"""
            <div class="chart-bar">
                <div class="bar-label">{provider_icon} {provider.title()}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: {bar_width:.1f}%"></div>
                </div>
                <div class="bar-value">{count:,} ({percentage:.1f}%)</div>
            </div>
        """
    
    # Build account breakdown chart - SPAM ONLY
    account_spam_rows = ""
    max_spam_percentage = max([acc['percentage'] for acc in data['account_breakdown_spam']], default=1)
    
    for account in data['account_breakdown_spam']:
        provider = account['provider']
        count = account.get('spam_count', account.get('email_count', 0))
        percentage = account['percentage']
        
        # Normalize bar width - highest percentage gets 100% width
        bar_width = (percentage / max_spam_percentage * 100) if max_spam_percentage > 0 else 0
        
        # Provider icons
        provider_icon = {
            'gmail': '📧',
            'icloud': '☁️', 
            'outlook': '📨',
            'yahoo': '📬',
            'aol': '📭'
        }.get(provider.lower(), '📮')
        
        account_spam_rows += f"""
            <div class="chart-bar">
                <div class="bar-label">{provider_icon} {provider.title()}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: {bar_width:.1f}%; background-color: #dc3545;"></div>
                </div>
                <div class="bar-value" style="color: #dc3545;">{count:,} ({percentage:.1f}%)</div>
            </div>
        """
    
    # Session stats - now using proper dictionary access
    session_stats = data['session_stats']
    avg_emails = session_stats.get('avg_emails_per_session', 0) or 0
    avg_deletion_rate = session_stats.get('avg_deletion_rate', 0) or 0
    total_sessions = session_stats.get('total_sessions', 0) or 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytics & Reports - Mail Filter</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ 
                max-width: 1400px; 
                margin: 0 auto; 
                background: rgba(255,255,255,0.95); 
                border-radius: 20px; 
                padding: 30px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }}
            .back-link {{ 
                color: #667eea; 
                text-decoration: none; 
                margin-bottom: 20px; 
                display: inline-block;
                font-weight: 600;
            }}
            h1 {{ 
                color: #2c3e50; 
                text-align: center; 
                font-size: 2.5em; 
                margin-bottom: 30px;
            }}
            .analytics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin-bottom: 40px;
            }}
            .analytics-card {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.08);
                border-top: 4px solid #667eea;
            }}
            .card-title {{
                font-size: 1.3em;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .metric-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }}
            .metric-row:last-child {{ border-bottom: none; }}
            .metric-label {{ font-weight: 600; color: #34495e; }}
            .metric-value {{ font-weight: 700; color: #667eea; }}
            .chart-bar {{
                display: grid;
                grid-template-columns: 120px 1fr 80px;
                gap: 15px;
                align-items: center;
                margin-bottom: 12px;
            }}
            .bar-label {{ 
                font-size: 0.9em; 
                font-weight: 600; 
                color: #34495e;
                text-align: right;
            }}
            .bar-container {{
                background: #e9ecef;
                border-radius: 10px;
                height: 20px;
                position: relative;
                overflow: hidden;
            }}
            .bar-fill {{
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                height: 100%;
                border-radius: 10px;
                transition: width 0.5s ease;
            }}
            .bar-value {{ 
                font-size: 0.85em; 
                font-weight: 600; 
                color: #34495e;
                text-align: right;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            .data-table th {{
                background: #f8f9fa;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                color: #34495e;
                border-bottom: 2px solid #dee2e6;
            }}
            .data-table td {{
                padding: 10px 12px;
                border-bottom: 1px solid #dee2e6;
            }}
            .data-table tbody tr:hover {{
                background: #f8f9fa;
            }}
            .effectiveness-card {{ border-top-color: #28a745; }}
            .categories-card {{ border-top-color: #fd7e14; }}
            .activity-card {{ border-top-color: #6610f2; }}
            .domains-card {{ border-top-color: #dc3545; }}
            .sessions-card {{ border-top-color: #20c997; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>📊 Analytics & Reports</h1>
            
            <div class="analytics-grid">
                <div class="analytics-card effectiveness-card">
                    <div class="card-title">
                        🎯 Processing Effectiveness (30 Days)
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">Total Emails Processed</div>
                        <div class="metric-value">{total:,}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">Spam Deleted</div>
                        <div class="metric-value" style="color: #dc3545;">{deleted:,}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">Emails Preserved</div>
                        <div class="metric-value" style="color: #28a745;">{preserved:,}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">Detection Rate</div>
                        <div class="metric-value" style="color: #fd7e14;">{effectiveness_rate:.1f}%</div>
                    </div>
                </div>
                
                <div class="analytics-card sessions-card">
                    <div class="card-title">
                        ⚡ Session Performance (30 Days)
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">Total Sessions</div>
                        <div class="metric-value">{total_sessions}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">Avg Emails/Session</div>
                        <div class="metric-value">{avg_emails:.0f}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">Avg Deletion Rate</div>
                        <div class="metric-value">{avg_deletion_rate:.1f}%</div>
                    </div>
                </div>
            </div>
            
            <div class="analytics-grid">
                <div class="analytics-card categories-card">
                    <div class="card-title">
                        🏷️ Top Spam Categories (30 Days)
                    </div>
                    {category_rows}
                </div>
                
                <div class="analytics-card accounts-total-card">
                    <div class="card-title">
                        👤 Total Mail by Account (30 Days)
                    </div>
                    {account_total_rows}
                </div>
            </div>
            
            <div class="analytics-grid">
                <div class="analytics-card accounts-spam-card">
                    <div class="card-title">
                        🗑️ Spam Mail by Account (30 Days)
                    </div>
                    {account_spam_rows}
                </div>
            </div>
            
            <div class="analytics-grid">
                <div class="analytics-card domains-card">
                    <div class="card-title">
                        🌐 Top Spam Domains (30 Days)
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Domain</th>
                                <th>Blocked Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {domain_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="analytics-card activity-card">
                <div class="card-title">
                    📈 Daily Activity (Last 14 Days)
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Deleted</th>
                            <th>Preserved</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {activity_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        
        <script>
            // Data refresh functionality
            setInterval(function() {{
                window.location.reload();
            }}, 30000); // Refresh every 30 seconds
        </script>
    </body>
    </html>
    """
    
    return html


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
async def category_validation_page():
    """Category Validation Page - Rebuilt from Scratch"""
    print("🔍 CATEGORY VALIDATION page accessed")
    
    try:
        # Get all categories with email counts
        categories = db.execute_query("""
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
        
        # Build category options
        category_options = ""
        for cat in categories:
            category_name = cat['category']
            total = cat['total']
            unvalidated = cat['unvalidated']
            validated = cat['validated_correct']
            
            validation_rate = (validated / total * 100) if total > 0 else 0
            
            category_options += f'<option value="{category_name}">{category_name} ({unvalidated} unvalidated of {total} total - {validation_rate:.1f}% validated)</option>\n'
        
        # Simple HTML page
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Category Validation - Mail Filter</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
                h1 {{ color: #333; text-align: center; }}
                .controls {{ margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 5px; }}
                select {{ padding: 10px; font-size: 16px; width: 400px; margin-right: 10px; }}
                button {{ padding: 10px 20px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
                .email-list {{ margin-top: 20px; }}
                .email-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #fafafa; }}
                .sender {{ font-weight: bold; color: #333; margin-bottom: 5px; }}
                .sender-encoded {{ font-family: monospace; font-size: 12px; color: #888; margin-bottom: 5px; background: #f0f0f0; padding: 4px; border-radius: 3px; border-left: 3px solid #007bff; }}
                .subject {{ color: #666; margin-bottom: 10px; }}
                .feedback-buttons {{ margin-top: 10px; }}
                .feedback-buttons button {{ margin-right: 10px; }}
                .thumbs-up {{ background: #28a745; }}
                .thumbs-up:hover {{ background: #218838; }}
                .thumbs-down {{ background: #dc3545; }}
                .thumbs-down:hover {{ background: #c82333; }}
                .save-email {{ background: #17a2b8; }}
                .save-email:hover {{ background: #138496; }}
                .loading {{ text-align: center; padding: 20px; color: #666; }}
                .pagination {{ text-align: center; margin: 20px 0; }}
                .pagination button {{ margin: 0 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📋 Category Validation</h1>
                <p><a href="/">← Back to Dashboard</a></p>
                
                <div class="controls">
                    <label for="categorySelect">Select Category:</label>
                    <select id="categorySelect">
                        <option value="">Choose a category...</option>
                        {category_options}
                    </select>
                    <button onclick="loadEmails()">Load Emails</button>
                </div>
                
                <div id="emailList" class="email-list"></div>
                <div id="pagination" class="pagination"></div>
            </div>
            
            <script>
                let currentCategory = '';
                let currentPage = 1;
                
                function decodeEmailContent(content) {{
                    if (!content) return '';
                    
                    try {{
                        // Clean up content first - remove newlines and extra whitespace
                        let cleaned = content.replace(/\\r\\n/g, ' ').replace(/\\n/g, ' ').replace(/\\s+/g, ' ').trim();
                        
                        // Handle UTF-8 Q-encoding (=?UTF-8?Q?...?=)
                        if (cleaned.includes('=?UTF-8?Q?')) {{
                            let decoded = cleaned.replace(/=\\?UTF-8\\?Q\\?([^?]+)\\?=/g, function(match, encoded) {{
                                // Replace encoded characters
                                let result = encoded
                                    .replace(/=([0-9A-F]{{2}})/g, function(match, hex) {{
                                        return String.fromCharCode(parseInt(hex, 16));
                                    }})
                                    .replace(/_/g, ' ');
                                return result;
                            }});
                            return decoded;
                        }}
                        
                        // Handle UTF-8 B-encoding (=?UTF-8?B?...?=) - Base64
                        if (cleaned.includes('=?UTF-8?B?')) {{
                            let decoded = cleaned.replace(/=\\?UTF-8\\?B\\?([^?]+)\\?=/g, function(match, encoded) {{
                                try {{
                                    return atob(encoded);
                                }} catch(e) {{
                                    return encoded + ' (decode error)';
                                }}
                            }});
                            return decoded;
                        }}
                        
                        // Handle other encodings or return cleaned content
                        return cleaned;
                    }} catch(e) {{
                        console.error('Decoding error:', e);
                        return content + ' (decode error)';
                    }}
                }}
                
                async function loadEmails() {{
                    const select = document.getElementById('categorySelect');
                    const category = select.value;
                    
                    if (!category) {{
                        alert('Please select a category');
                        return;
                    }}
                    
                    currentCategory = category;
                    currentPage = 1;
                    
                    console.log('Loading emails for category:', category);
                    
                    const emailList = document.getElementById('emailList');
                    emailList.innerHTML = '<div class="loading">Loading emails...</div>';
                    
                    try {{
                        const response = await fetch(`/api/validation/emails/${{encodeURIComponent(category)}}?page=${{currentPage}}`);
                        const data = await response.json();
                        
                        console.log('API response:', data);
                        
                        if (data.success) {{
                            displayEmails(data.emails, data.pagination);
                        }} else {{
                            emailList.innerHTML = `<div class="loading">Error: ${{data.message}}</div>`;
                        }}
                    }} catch (error) {{
                        console.error('Error loading emails:', error);
                        emailList.innerHTML = `<div class="loading">Error: ${{error.message}}</div>`;
                    }}
                }}
                
                function displayEmails(emails, pagination) {{
                    const emailList = document.getElementById('emailList');
                    
                    if (emails.length === 0) {{
                        emailList.innerHTML = '<div class="loading">🎉 All emails in this category have been validated!</div>';
                        document.getElementById('pagination').innerHTML = '';
                        return;
                    }}
                    
                    let html = '';
                    emails.forEach(email => {{
                        // Decode sender and subject
                        const decodedSender = decodeEmailContent(email.sender_email);
                        const decodedSubject = decodeEmailContent(email.subject);
                        
                        // Enhanced sender display for brand impersonation detection
                        let senderDisplay = '';
                        
                        // Debug logging
                        console.log('Email ID:', email.id);
                        console.log('Raw sender:', email.sender_email);
                        console.log('Decoded sender:', decodedSender);
                        
                        // HTML escape function to prevent <email@domain.com> being interpreted as HTML tags
                        function htmlEscape(str) {{
                            return str.replace(/&/g, '&amp;')
                                     .replace(/</g, '&lt;')
                                     .replace(/>/g, '&gt;')
                                     .replace(/"/g, '&quot;')
                                     .replace(/'/g, '&#x27;');
                        }}
                        
                        // Always show decoded sender prominently (fully qualified address)
                        const escapedDecoded = htmlEscape(decodedSender);
                        senderDisplay = `<div class="sender">From: ${{escapedDecoded}}</div>`;
                        
                        // Always show raw version for comparison and brand impersonation detection
                        // This helps users spot spoofing, encoding tricks, and verify domains
                        if (email.sender_email && email.sender_email.trim() !== '') {{
                            const escapedRaw = htmlEscape(email.sender_email);
                            senderDisplay += `<div class="sender-encoded">Raw: ${{escapedRaw}}</div>`;
                        }}
                        
                        html += `
                            <div class="email-item" id="email-${{email.id}}">
                                ${{senderDisplay}}
                                <div class="subject">Subject: ${{decodedSubject}}</div>
                                <div class="feedback-buttons">
                                    <button class="thumbs-up" onclick="submitFeedback(${{email.id}}, 'up')">👍 Correct</button>
                                    <button class="thumbs-down" onclick="submitFeedback(${{email.id}}, 'down')">👎 Wrong</button>
                                    <button class="save-email" onclick="saveEmail(${{email.id}})">💾 Save</button>
                                </div>
                            </div>
                        `;
                    }});
                    
                    emailList.innerHTML = html;
                    
                    // Show pagination
                    displayPagination(pagination);
                }}
                
                function displayPagination(pagination) {{
                    const paginationDiv = document.getElementById('pagination');
                    
                    if (pagination.total_pages <= 1) {{
                        paginationDiv.innerHTML = '';
                        return;
                    }}
                    
                    let html = '';
                    
                    if (pagination.has_prev) {{
                        html += `<button onclick="changePage(${{pagination.current_page - 1}})">← Previous</button>`;
                    }}
                    
                    html += `<span>Page ${{pagination.current_page}} of ${{pagination.total_pages}} (${{pagination.total_emails}} emails)</span>`;
                    
                    if (pagination.has_next) {{
                        html += `<button onclick="changePage(${{pagination.current_page + 1}})">Next →</button>`;
                    }}
                    
                    paginationDiv.innerHTML = html;
                }}
                
                function changePage(page) {{
                    currentPage = page;
                    loadEmails();
                }}
                
                async function submitFeedback(emailId, feedback) {{
                    console.log('Submitting feedback:', emailId, feedback);
                    
                    try {{
                        const response = await fetch('/api/validation/feedback', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                email_id: emailId,
                                feedback: feedback
                            }})
                        }});
                        
                        const result = await response.json();
                        console.log('Feedback result:', result);
                        
                        if (result.success) {{
                            // Remove the email from the list
                            const emailElement = document.getElementById(`email-${{emailId}}`);
                            if (emailElement) {{
                                emailElement.remove();
                            }}
                            
                            // Show feedback message
                            if (feedback === 'down') {{
                                if (result.reclassification) {{
                                    alert(`🔄 Email reclassified from '${{result.reclassification.original_category}}' to '${{result.reclassification.new_category}}'`);
                                }} else {{
                                    alert('👎 Email marked for manual review');
                                }}
                            }}
                            // No popup for thumbs up - just silently remove the email
                            
                            // Check if we need to reload the page
                            const remainingEmails = document.querySelectorAll('.email-item').length;
                            if (remainingEmails === 0) {{
                                loadEmails();
                            }}
                        }} else {{
                            alert('Error: ' + result.message);
                        }}
                    }} catch (error) {{
                        console.error('Error submitting feedback:', error);
                        alert('Error submitting feedback: ' + error.message);
                    }}
                }}
                
                async function saveEmail(emailId) {{
                    console.log('Saving email for protection:', emailId);
                    
                    try {{
                        const response = await fetch('/api/validation/save', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                email_id: emailId
                            }})
                        }});
                        
                        const result = await response.json();
                        console.log('Save result:', result);
                        
                        if (result.success) {{
                            // Remove the email from the list
                            const emailElement = document.getElementById(`email-${{emailId}}`);
                            if (emailElement) {{
                                emailElement.remove();
                            }}
                            
                            // Show success message
                            alert(`💾 Email saved and protected! ${{result.protection_message || 'Future similar emails will be protected.'}}`);
                            
                            // Check if we need to reload the page
                            const remainingEmails = document.querySelectorAll('.email-item').length;
                            if (remainingEmails === 0) {{
                                loadEmails();
                            }}
                        }} else {{
                            alert('Error: ' + result.message);
                        }}
                    }} catch (error) {{
                        console.error('Error saving email:', error);
                        alert('Error saving email: ' + error.message);
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        print(f"❌ Validation page error: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error: {e}</h1>"

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
async def report_page():
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
            return """
            <html><head><title>Import Report</title></head>
            <body><h1>No Import Sessions Found</h1><p>No import data available to generate report.</p></body>
            </html>
            """
        
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
        
        stats = total_stats[0] if total_stats else {'total_emails': 0, 'total_deleted': 0, 'total_preserved': 0}
        
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
        
        # Generate HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>📊 Last Import Processing Report</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .header .subtitle {{
                    margin-top: 10px;
                    font-size: 1.2em;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .stat-number {{
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 5px;
                }}
                .stat-label {{
                    color: #666;
                    font-size: 1.1em;
                }}
                .section {{
                    margin-bottom: 40px;
                }}
                .section h2 {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 20px;
                    margin: 0 0 20px 0;
                    border-radius: 8px;
                    font-size: 1.5em;
                }}
                .category-table {{
                    width: 100%;
                    border-collapse: collapse;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .category-table th {{
                    background: #f8f9fa;
                    padding: 15px;
                    text-align: left;
                    font-weight: 600;
                    color: #333;
                    border-bottom: 2px solid #dee2e6;
                }}
                .category-table td {{
                    padding: 12px 15px;
                    border-bottom: 1px solid #f1f3f4;
                }}
                .category-table tr:hover {{
                    background-color: #f8f9fa;
                }}
                .percentage-bar {{
                    background: #e9ecef;
                    border-radius: 10px;
                    height: 20px;
                    overflow: hidden;
                    margin-left: 10px;
                    display: inline-block;
                    width: 100px;
                }}
                .percentage-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    transition: width 0.3s ease;
                }}
                .performance-highlight {{
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .nav-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 10px;
                    transition: all 0.3s ease;
                }}
                .nav-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
                }}
                .timestamp {{
                    color: #666;
                    font-style: italic;
                    text-align: center;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Import Processing Report</h1>
                    <div class="subtitle">Last Import Session Analysis</div>
                </div>
                
                <div class="content">
                    <!-- Navigation -->
                    <div style="text-align: center; margin-bottom: 30px;">
                        <a href="/" class="nav-button">🏠 Home</a>
                        <a href="/analytics" class="nav-button">📈 Analytics</a>
                        <a href="/validate" class="nav-button">✅ Validate</a>
                    </div>
                    
                    <!-- Key Statistics -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{stats['total_emails']:,}</div>
                            <div class="stat-label">Total Emails Processed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{stats['total_deleted']:,}</div>
                            <div class="stat-label">🗑️ Deleted (Spam)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{stats['total_preserved']:,}</div>
                            <div class="stat-label">🛡️ Preserved (Legitimate)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{deleted_pct:.1f}%</div>
                            <div class="stat-label">Spam Detection Rate</div>
                        </div>
                    </div>
                    
                    <!-- Performance Highlight -->
                    <div class="performance-highlight">
                        <h3>🎯 Processing Complete</h3>
                        <p><strong>Account:</strong> {session['account_email'] or 'Unknown'} | 
                        <strong>Processing Time:</strong> {processing_time} | 
                        <strong>Session ID:</strong> {session_id}</p>
                    </div>
        """
        
        # Add deleted categories breakdown
        if deleted_categories:
            html += """
                    <div class="section">
                        <h2>🗑️ Spam Categories Breakdown (Deleted Emails)</h2>
                        <table class="category-table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Count</th>
                                    <th>Percentage</th>
                                    <th>Visual</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for category in deleted_categories:
                category_name = category['category']
                count = category['count']
                percentage = category['percentage'] or 0
                
                html += f"""
                                <tr>
                                    <td><strong>{category_name}</strong></td>
                                    <td>{count:,}</td>
                                    <td>{percentage:.1f}%</td>
                                    <td>
                                        <div class="percentage-bar">
                                            <div class="percentage-fill" style="width: {min(percentage, 100)}%"></div>
                                        </div>
                                    </td>
                                </tr>
                """
            
            html += """
                            </tbody>
                        </table>
                    </div>
            """
        
        # Add preserved categories breakdown
        if preserved_categories:
            html += """
                    <div class="section">
                        <h2>🛡️ Preserved Email Categories</h2>
                        <table class="category-table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Count</th>
                                    <th>Percentage</th>
                                    <th>Visual</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for category in preserved_categories:
                category_name = category['category']
                count = category['count']
                percentage = category['percentage'] or 0
                
                html += f"""
                                <tr>
                                    <td><strong>{category_name}</strong></td>
                                    <td>{count:,}</td>
                                    <td>{percentage:.1f}%</td>
                                    <td>
                                        <div class="percentage-bar">
                                            <div class="percentage-fill" style="width: {min(percentage, 100)}%"></div>
                                        </div>
                                    </td>
                                </tr>
                """
            
            html += """
                            </tbody>
                        </table>
                    </div>
            """
        
        # Add preservation reasons breakdown
        if preservation_reasons:
            html += """
                    <div class="section">
                        <h2>🔍 Preservation Reasons Breakdown</h2>
                        <table class="category-table">
                            <thead>
                                <tr>
                                    <th>Reason</th>
                                    <th>Count</th>
                                    <th>Percentage</th>
                                    <th>Visual</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for reason in preservation_reasons:
                reason_text = reason['reason']
                count = reason['count']
                percentage = reason['percentage'] or 0
                
                # Truncate long reasons
                display_reason = reason_text[:80] + "..." if len(reason_text) > 80 else reason_text
                
                html += f"""
                                <tr>
                                    <td><strong>{display_reason}</strong></td>
                                    <td>{count:,}</td>
                                    <td>{percentage:.1f}%</td>
                                    <td>
                                        <div class="percentage-bar">
                                            <div class="percentage-fill" style="width: {min(percentage, 100)}%"></div>
                                        </div>
                                    </td>
                                </tr>
                """
            
            html += """
                            </tbody>
                        </table>
                    </div>
            """
        
        # Add summary section
        html += f"""
                    <div class="section">
                        <h2>📋 Processing Summary</h2>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-number">{deleted_pct:.1f}%</div>
                                <div class="stat-label">🗑️ Deleted Rate</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">{preserved_pct:.1f}%</div>
                                <div class="stat-label">🛡️ Preserved Rate</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">{len(deleted_categories) if deleted_categories else 0}</div>
                                <div class="stat-label">Spam Categories</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">{len(preserved_categories) if preserved_categories else 0}</div>
                                <div class="stat-label">Preserved Categories</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="timestamp">
                        Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                        Import session: {session['start_time']} | 
                        <a href="/report" style="color: #667eea;">🔄 Refresh Report</a>
                    </div>
                    
                    <!-- Remove Last Import Section -->
                    <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3 style="margin-bottom: 15px; color: #dc3545;">🗑️ Database Management</h3>
                        <p style="margin-bottom: 15px; color: #6c757d;">
                            Remove the most recent email import to re-import with updated classification rules.
                        </p>
                        
                        <div id="last-import-info" style="margin-bottom: 15px; padding: 10px; background: #e9ecef; border-radius: 4px; font-family: monospace; font-size: 0.9em;">
                            Loading last import information...
                        </div>
                        
                        <button 
                            id="remove-last-import-btn" 
                            class="btn" 
                            style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;"
                            onclick="removeLastImport()"
                            disabled
                        >
                            🗑️ Remove Last Import
                        </button>
                        
                        <p style="margin-top: 10px; font-size: 0.85em; color: #6c757d;">
                            ⚠️ This action cannot be undone. Only removes the most recent import session.
                        </p>
                    </div>
                </div>
            </div>
            
            <script>
                // Load last import information when page loads
                async function loadLastImportInfo() {{
                    try {{
                        const response = await fetch('/api/last-import/info');
                        const data = await response.json();
                        
                        const infoDiv = document.getElementById('last-import-info');
                        const removeBtn = document.getElementById('remove-last-import-btn');
                        
                        if (data.success) {{
                            const session = data.session;
                            infoDiv.innerHTML = `
                                <strong>Last Import Session:</strong><br>
                                📧 Account: ${{session.account_email}}<br>
                                📅 Date: ${{new Date(session.start_time).toLocaleString()}}<br>
                                📊 Total Emails: ${{session.total_emails}}<br>
                                🗑️ Deleted: ${{session.total_deleted}}<br>
                                💾 Preserved: ${{session.total_preserved}}<br>
                                🆔 Session ID: ${{session.id}}
                            `;
                            removeBtn.disabled = false;
                        }} else {{
                            infoDiv.innerHTML = `❌ ${{data.message}}`;
                            removeBtn.disabled = true;
                        }}
                    }} catch (error) {{
                        document.getElementById('last-import-info').innerHTML = `❌ Error loading import info: ${{error.message}}`;
                    }}
                }}
                
                // Remove last import function
                async function removeLastImport() {{
                    if (!confirm('⚠️ Are you sure you want to remove the last email import?\\n\\nThis will permanently delete all emails from the most recent import session and cannot be undone.')) {{
                        return;
                    }}
                    
                    const btn = document.getElementById('remove-last-import-btn');
                    const originalText = btn.textContent;
                    btn.textContent = '⏳ Removing...';
                    btn.disabled = true;
                    
                    try {{
                        const response = await fetch('/api/last-import/remove', {{
                            method: 'POST'
                        }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            alert(`✅ ${{result.message}}\\n\\nDetails:\\n- Emails removed: ${{result.details.emails_removed}}\\n- Account: ${{result.details.account_email}}\\n- Session ID: ${{result.details.session_id}}`);
                            
                            // Reload the page to refresh analytics and import info
                            window.location.reload();
                        }} else {{
                            alert(`❌ Failed to remove last import: ${{result.message}}`);
                            btn.textContent = originalText;
                            btn.disabled = false;
                        }}
                    }} catch (error) {{
                        alert(`❌ Error: ${{error.message}}`);
                        btn.textContent = originalText;
                        btn.disabled = false;
                    }}
                }}
                
                // Load import info when page loads
                document.addEventListener('DOMContentLoaded', loadLastImportInfo);
            </script>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        
        return f"""
        <html>
        <head><title>Report Error</title></head>
        <body>
            <h1>Error Generating Report</h1>
            <p>Error: {str(e)}</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """

# ==========================================
# SINGLE ACCOUNT FILTER INTERFACE
# ==========================================

@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page():
    """Account selection page - lists all saved accounts"""
    try:
        # Import here to avoid circular imports
        from config.credentials import db_credentials
        
        # Load all saved accounts
        accounts = db_credentials.load_credentials()
        
        # Provider icons mapping
        provider_icons = {
            'iCloud': '🍎',
            'Gmail': '📧', 
            'Outlook': '🏢',
            'Yahoo': '🟣',
            'Custom': '⚙️'
        }
        
        # Build account cards
        account_cards = ""
        if accounts:
            # Add "All Accounts" option first
            total_accounts = len(accounts)
            account_cards += f"""
            <div class="account-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <div class="account-icon">🌐</div>
                <div class="account-info">
                    <div class="account-email" style="color: white;">All Accounts</div>
                    <div class="account-provider" style="color: #f0f0f0;">Process all {total_accounts} accounts at once</div>
                    <div class="account-meta" style="color: #f0f0f0;">
                        Batch filtering with preview option
                    </div>
                </div>
                <div class="account-actions">
                    <a href="/single-account/all" class="btn" style="background: white; color: #667eea;">Select All</a>
                </div>
            </div>
            """
            # Then add individual accounts
            for i, account in enumerate(accounts):
                provider = account.get('provider', 'Custom')
                icon = provider_icons.get(provider, '📧')
                last_used = account.get('last_used', 'Never')
                target_folders = account.get('target_folders', [])
                folder_count = len(target_folders) if target_folders else 0
                
                account_cards += f"""
                <div class="account-card">
                    <div class="account-icon">{icon}</div>
                    <div class="account-info">
                        <div class="account-email">{account['email_address']}</div>
                        <div class="account-provider">{provider}</div>
                        <div class="account-meta">
                            {folder_count} folders configured • Last used: {last_used}
                        </div>
                    </div>
                    <div class="account-actions">
                        <a href="/single-account/{i}" class="btn btn-primary">Select</a>
                        <button onclick="testConnection({i})" class="btn btn-secondary">Test</button>
                    </div>
                </div>
                """
        else:
            account_cards = """
            <div class="no-accounts">
                <h3>📧 No Email Accounts Configured</h3>
                <p>Use the CLI to add email accounts first:</p>
                <code>python3 main.py</code>
                <p>Then return here to manage single account filtering.</p>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>📧 Email Accounts - Mail Filter</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .nav-links {{
                    padding: 20px 30px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #dee2e6;
                }}
                .back-link {{
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 600;
                    margin-right: 20px;
                }}
                .back-link:hover {{ text-decoration: underline; }}
                .content {{
                    padding: 30px;
                }}
                .account-card {{
                    display: flex;
                    align-items: center;
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 15px;
                    border: 1px solid #dee2e6;
                    transition: all 0.3s ease;
                }}
                .account-card:hover {{
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    transform: translateY(-2px);
                }}
                .account-icon {{
                    font-size: 2.5em;
                    margin-right: 20px;
                }}
                .account-info {{
                    flex: 1;
                }}
                .account-email {{
                    font-size: 1.3em;
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 5px;
                }}
                .account-provider {{
                    color: #667eea;
                    font-weight: 500;
                    margin-bottom: 5px;
                }}
                .account-meta {{
                    color: #6c757d;
                    font-size: 0.9em;
                }}
                .account-actions {{
                    display: flex;
                    gap: 10px;
                }}
                .btn {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .btn-secondary {{
                    background: #6c757d;
                    color: white;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }}
                .no-accounts {{
                    text-align: center;
                    padding: 40px;
                    color: #6c757d;
                }}
                .no-accounts h3 {{ color: #333; }}
                .no-accounts code {{
                    background: #f8f9fa;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-family: monospace;
                }}
                .status-message {{
                    display: none;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .status-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .status-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Email Accounts</h1>
                    <div class="subtitle">Select an account for single account filtering</div>
                </div>
                
                <div class="nav-links">
                    <a href="/" class="back-link">← Back to Dashboard</a>
                </div>
                
                <div class="content">
                    <div id="status-message" class="status-message"></div>
                    
                    {account_cards}
                </div>
            </div>
            
            <script>
                async function testConnection(accountId) {{
                    const statusDiv = document.getElementById('status-message');
                    statusDiv.className = 'status-message status-success';
                    statusDiv.textContent = 'Testing connection...';
                    statusDiv.style.display = 'block';
                    
                    try {{
                        const response = await fetch(`/api/testing/connection/${{accountId}}`, {{
                            method: 'POST'
                        }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            statusDiv.className = 'status-message status-success';
                            statusDiv.textContent = `✅ Connection successful! Found ${{result.total_folders || 0}} folders.`;
                        }} else {{
                            statusDiv.className = 'status-message status-error';
                            statusDiv.textContent = `❌ Connection failed: ${{result.error || 'Unknown error'}}`;
                        }}
                    }} catch (error) {{
                        statusDiv.className = 'status-message status-error';
                        statusDiv.textContent = `❌ Error testing connection: ${{error.message}}`;
                    }}
                    
                    // Hide message after 5 seconds
                    setTimeout(() => {{
                        statusDiv.style.display = 'none';
                    }}, 5000);
                }}
            </script>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"""
        <html>
        <head><title>Accounts Error</title></head>
        <body>
            <h1>Error Loading Accounts</h1>
            <p>Error: {str(e)}</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """

@app.get("/single-account/{account_id}", response_class=HTMLResponse)
async def single_account_page(account_id: str):
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
            account_idx = "all"
        else:
            # Handle individual account
            try:
                account_idx = int(account_id)
                if account_idx >= len(accounts):
                    return """
                    <html><body>
                        <h1>Account Not Found</h1>
                        <a href="/accounts">← Back to Accounts</a>
                    </body></html>
                    """
                account = accounts[account_idx]
                    
            except ValueError:
                return """
                <html><body>
                    <h1>Invalid Account ID</h1>
                    <a href="/accounts">← Back to Accounts</a>
                </body></html>
                """
        provider_icons = {
            'iCloud': '🍎',
            'Gmail': '📧', 
            'Outlook': '🏢',
            'Yahoo': '🟣',
            'Custom': '⚙️',
            'Processing 0 accounts': '🌐',
            'Processing 1 accounts': '🌐',
            'Processing 2 accounts': '🌐',
            'Processing 3 accounts': '🌐',
            'Processing 4 accounts': '🌐',
            'Processing 5 accounts': '🌐',
            'Processing 6 accounts': '🌐',
            'Processing 7 accounts': '🌐',
            'Processing 8 accounts': '🌐',
            'Processing 9 accounts': '🌐',
            'Processing 10 accounts': '🌐'
        }
        
        provider = account.get('provider', 'Custom')
        # Special icon for "all accounts"
        if account_id == "all":
            icon = '🌐'
        else:
            icon = provider_icons.get(provider, '📧')
        target_folders = account.get('target_folders', [])
        
        # Build folder list
        folder_list = ""
        if target_folders:
            for folder in target_folders:
                folder_list += f"""
                <div class="folder-item">
                    <span class="folder-name">📁 {folder}</span>
                    <span class="folder-status" id="folder-status-{folder.replace(' ', '_')}">Ready</span>
                </div>
                """
        else:
            folder_list = """
            <div class="no-folders">
                <p>❌ No folders configured for this account.</p>
                <p>Use the CLI to set up folders: <code>python3 main.py</code></p>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎯 Single Account Filter - {account['email_address']}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.2em;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .nav-links {{
                    padding: 20px 30px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #dee2e6;
                }}
                .back-link {{
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 600;
                    margin-right: 20px;
                }}
                .back-link:hover {{ text-decoration: underline; }}
                .content {{
                    padding: 30px;
                }}
                .account-header {{
                    display: flex;
                    align-items: center;
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 25px;
                    margin-bottom: 30px;
                    border: 1px solid #dee2e6;
                }}
                .account-icon {{
                    font-size: 3em;
                    margin-right: 25px;
                }}
                .account-details {{
                    flex: 1;
                }}
                .account-email {{
                    font-size: 1.5em;
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 5px;
                }}
                .account-provider {{
                    color: #667eea;
                    font-weight: 500;
                    margin-bottom: 10px;
                }}
                .account-meta {{
                    color: #6c757d;
                    font-size: 0.95em;
                }}
                .section {{
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 10px;
                    margin-bottom: 25px;
                    overflow: hidden;
                }}
                .section-header {{
                    background: #f8f9fa;
                    padding: 20px 25px;
                    border-bottom: 1px solid #dee2e6;
                    font-weight: 600;
                    color: #333;
                }}
                .section-content {{
                    padding: 25px;
                }}
                .folder-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 0;
                    border-bottom: 1px solid #eee;
                }}
                .folder-item:last-child {{ border-bottom: none; }}
                .folder-name {{
                    font-weight: 500;
                    color: #333;
                }}
                .folder-status {{
                    font-size: 0.9em;
                    color: #6c757d;
                    padding: 4px 8px;
                    background: #e9ecef;
                    border-radius: 4px;
                }}
                .actions-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-top: 20px;
                }}
                .action-card {{
                    background: white;
                    border: 2px solid #dee2e6;
                    border-radius: 10px;
                    padding: 25px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .action-card:hover {{
                    border-color: #667eea;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    transform: translateY(-3px);
                }}
                .action-card.preview {{
                    border-color: #28a745;
                }}
                .action-card.process {{
                    border-color: #dc3545;
                }}
                .action-icon {{
                    font-size: 3em;
                    margin-bottom: 15px;
                }}
                .action-title {{
                    font-size: 1.3em;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                .action-description {{
                    color: #6c757d;
                    font-size: 0.95em;
                    line-height: 1.4;
                }}
                .results-section {{
                    display: none;
                    margin-top: 30px;
                }}
                .results-header {{
                    background: #667eea;
                    color: white;
                    padding: 20px 25px;
                    font-weight: 600;
                }}
                .results-content {{
                    padding: 25px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 25px;
                }}
                .stat-card {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    border: 1px solid #dee2e6;
                }}
                .stat-value {{
                    font-size: 2em;
                    font-weight: 600;
                    color: #667eea;
                    margin-bottom: 5px;
                }}
                .stat-label {{
                    color: #6c757d;
                    font-size: 0.9em;
                }}
                .no-folders {{
                    text-align: center;
                    color: #6c757d;
                    padding: 20px;
                }}
                .no-folders code {{
                    background: #f8f9fa;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-family: monospace;
                }}
                .status-message {{
                    display: none;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .status-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .status-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .status-info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
                .loading {{
                    text-align: center;
                    padding: 40px;
                    color: #6c757d;
                }}
                .loading-spinner {{
                    font-size: 2em;
                    margin-bottom: 15px;
                    animation: spin 1s linear infinite;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                /* Mobile responsive styles */
                @media (max-width: 768px) {{
                    .actions-grid {{ grid-template-columns: 1fr; }}
                    .stats-grid {{ grid-template-columns: 1fr; }}
                    .account-header {{ flex-direction: column; text-align: center; }}
                    .account-icon {{ margin-right: 0; margin-bottom: 15px; }}
                    
                    /* Mobile email table improvements */
                    .email-table-container {{
                        overflow-x: auto;
                        -webkit-overflow-scrolling: touch;
                    }}
                    
                    .email-table {{
                        min-width: 100%;
                        font-size: 0.85em;
                    }}
                    
                    .email-cell {{
                        max-width: none !important;
                        min-width: 0;
                        white-space: normal !important;
                        overflow: visible !important;
                        text-overflow: initial !important;
                        padding: 8px 6px !important;
                        line-height: 1.4;
                    }}
                    
                    .email-cell-sender {{
                        max-width: 120px;
                        word-break: break-word;
                    }}
                    
                    .email-cell-subject {{
                        max-width: 150px;
                        word-break: break-word;
                    }}
                    
                    .email-cell-compact {{
                        padding: 6px 4px !important;
                        font-size: 0.8em;
                    }}
                    
                    .email-cell-account {{
                        max-width: 100px;
                        word-break: break-word;
                    }}
                }}
                
                @media (max-width: 480px) {{
                    /* iPhone specific optimizations */
                    .container {{
                        margin: 0 10px;
                        border-radius: 10px;
                    }}
                    
                    .content {{
                        padding: 15px;
                    }}
                    
                    .account-header {{
                        padding: 15px;
                    }}
                    
                    .email-table {{
                        font-size: 0.8em;
                    }}
                    
                    .email-cell {{
                        padding: 6px 4px !important;
                    }}
                    
                    .email-cell-sender {{
                        max-width: 100px;
                    }}
                    
                    .email-cell-subject {{
                        max-width: 120px;
                    }}
                    
                    .email-cell-account {{
                        max-width: 80px;
                    }}                    
                    /* Hide less critical columns on very small screens */
                    .email-column-confidence,
                    .email-column-date {{
                        display: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Single Account Filter</h1>
                    <div class="subtitle">Process emails for specific account</div>
                </div>
                
                <div class="nav-links">
                    <a href="/accounts" class="back-link">← Back to Accounts</a>
                    <a href="/" class="back-link">🏠 Dashboard</a>
                </div>
                
                <div class="content">
                    <div id="status-message" class="status-message"></div>
                    
                    <div class="account-header">
                        <div class="account-icon">{icon}</div>
                        <div class="account-details">
                            <div class="account-email">{account['email_address']}</div>
                            <div class="account-provider">{provider}</div>
                            <div class="account-meta">
                                {len(target_folders)} folders configured • Account ID: {account_id}
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-header">{'🌐 Target Accounts' if account_id == 'all' else '📁 Target Folders'}</div>
                        <div class="section-content">
                            {folder_list}
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-header">⚡ Processing Options</div>
                        <div class="section-content">
                            <div class="actions-grid">
                                <div class="action-card preview" onclick="runPreview()">
                                    <div class="action-icon">🔍</div>
                                    <div class="action-title">Preview Mode</div>
                                    <div class="action-description">
                                        See what emails would be deleted without actually deleting them. 
                                        Safe way to test the filter settings.
                                    </div>
                                </div>
                                
                                <div class="action-card process" onclick="runProcess()">
                                    <div class="action-icon">🚀</div>
                                    <div class="action-title">Process Emails</div>
                                    <div class="action-description">
                                        Actually delete spam emails and preserve important ones. 
                                        This will make permanent changes.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="results-section" class="section results-section">
                        <div class="results-header">📊 Processing Results</div>
                        <div class="results-content">
                            <div id="loading" class="loading">
                                <div class="loading-spinner">⏳</div>
                                <div>Processing emails, please wait...</div>
                            </div>
                            <div id="results-content"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                const accountId = "{account_id}";
                
                async function runPreview() {{
                    await runAction('preview');
                }}
                
                async function runProcess() {{
                    if (!confirm('⚠️  This will permanently delete spam emails. Are you sure?')) {{
                        return;
                    }}
                    await runAction('process');
                }}
                
                async function runAction(mode) {{
                    const statusDiv = document.getElementById('status-message');
                    const resultsSection = document.getElementById('results-section');
                    const loadingDiv = document.getElementById('loading');
                    const resultsContent = document.getElementById('results-content');
                    
                    // Show status and results section
                    statusDiv.className = 'status-message status-info';
                    statusDiv.textContent = mode === 'preview' ? '🔍 Running preview...' : '🚀 Processing emails...';
                    statusDiv.style.display = 'block';
                    
                    resultsSection.style.display = 'block';
                    loadingDiv.style.display = 'block';
                    resultsContent.style.display = 'none';
                    
                    try {{
                        if (mode === 'preview') {{
                            // Preview mode: just call preview endpoint
                            const response = await fetch(`/api/single-account/${{accountId}}/preview`, {{
                                method: 'POST'
                            }});
                            const result = await response.json();
                            
                            if (result.success) {{
                                statusDiv.className = 'status-message status-success';
                                statusDiv.textContent = `✅ Preview completed successfully!`;
                                
                                // Display results
                                const stats = result.data;
                            resultsContent.innerHTML = `
                                <div class="stats-grid">
                                    <div class="stat-card">
                                        <div class="stat-value">${{stats.total_emails || 0}}</div>
                                        <div class="stat-label">Total Emails</div>
                                    </div>
                                    <div class="stat-card">
                                        <div class="stat-value" style="color: #dc3545;">${{stats.total_deleted || 0}}</div>
                                        <div class="stat-label">${{mode === 'preview' ? 'Would Delete' : 'Deleted'}}</div>
                                    </div>
                                    <div class="stat-card">
                                        <div class="stat-value" style="color: #28a745;">${{stats.total_preserved || 0}}</div>
                                        <div class="stat-label">Preserved</div>
                                    </div>
                                    <div class="stat-card">
                                        <div class="stat-value">${{Object.keys(stats.categories || {{}}).length}}</div>
                                        <div class="stat-label">Categories</div>
                                    </div>
                                </div>
                                
                                <div style="margin-top: 25px;">
                                    <h4>📊 Category Breakdown:</h4>
                                    <div id="categories-list">
                                        ${{Object.entries(stats.categories || {{}}).map(([category, count]) => 
                                            `<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                                <span>${{category}}</span>
                                                <span style="font-weight: 600;">${{count}} emails</span>
                                            </div>`
                                        ).join('')}}
                                    </div>
                                </div>
                                
                                ${{stats.account_breakdown ? `
                                <div style="margin-top: 25px;">
                                    <h4>🌐 Account Breakdown:</h4>
                                    <div id="account-breakdown-list">
                                        ${{stats.account_breakdown.map(account => 
                                            account.error ? 
                                            `<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; background-color: #fff5f5;">
                                                <span style="color: #dc3545;">${{account.email}}</span>
                                                <span style="color: #dc3545; font-weight: 600;">Error: ${{account.error}}</span>
                                            </div>` :
                                            `<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                                <span>${{account.email}}</span>
                                                <span style="font-weight: 600;">
                                                    <span style="color: #dc3545;">${{account.deleted}}</span> deleted, 
                                                    <span style="color: #28a745;">${{account.preserved}}</span> preserved
                                                </span>
                                            </div>`
                                        ).join('')}}
                                    </div>
                                </div>
                                ` : ''}}
                                
                                <div id="email-details-section" style="margin-top: 30px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                        <h4 style="margin: 0;">📧 Email Details:</h4>
                                        ${{!(typeof stats.session_id === 'string' && stats.session_id.startsWith('all_')) ? `
                                        <div>
                                            <button id="show-session-emails" onclick="toggleEmailView('session')" style="background: #667eea; color: white; border: none; padding: 8px 12px; border-radius: 5px; margin-right: 5px; cursor: pointer; font-size: 0.9em;">Current Session</button>
                                            <button id="show-all-emails" onclick="toggleEmailView('all')" style="background: #6c757d; color: white; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9em;">All Account Emails</button>
                                        </div>
                                        ` : ''}}
                                    </div>
                                    <div id="email-details-loading" style="text-align: center; padding: 20px; color: #6c757d;">
                                        <div style="font-size: 1.5em; margin-bottom: 10px;">⏳</div>
                                        Loading email details...
                                    </div>
                                    <div id="email-details-table" style="display: none;"></div>
                                </div>
                                
                                <div style="margin-top: 25px; font-size: 0.9em; color: #6c757d;">
                                    Account: ${{stats.account_email}}<br>
                                    Processing Time: ${{new Date().toLocaleString()}}
                                </div>
                            `;
                            
                            // Load email details table (only if session_id is valid and not "all accounts")
                            if (stats.session_id && stats.session_id !== 'undefined' && !(typeof stats.session_id === 'string' && stats.session_id.startsWith('all_'))) {{
                                currentSessionId = stats.session_id;
                                loadEmailDetails(stats.session_id);
                            }} else if (stats.session_id && typeof stats.session_id === 'string' && stats.session_id.startsWith('all_')) {{
                                // Handle "all accounts" mode - load emails from multiple sessions
                                if (stats.session_ids && stats.session_ids.length > 0) {{
                                    loadAllAccountsEmailDetails(stats.session_ids);
                                }} else {{
                                    document.getElementById('email-details-loading').innerHTML = `
                                        <div style="text-align: center; padding: 20px; color: #17a2b8;">
                                            <div style="font-size: 1.5em; margin-bottom: 10px;">🌐</div>
                                            All accounts processing complete. See account breakdown above for detailed results.
                                        </div>
                                    `;
                                }}
                            }} else {{
                                document.getElementById('email-details-loading').innerHTML = `
                                    <div style="text-align: center; padding: 20px; color: #ffc107;">
                                        <div style="font-size: 1.5em; margin-bottom: 10px;">⚠️</div>
                                        Session ID not available. Email details cannot be loaded.
                                    </div>
                                `;
                            }}
                            
                            loadingDiv.style.display = 'none';
                            resultsContent.style.display = 'block';
                            }} else {{
                                statusDiv.className = 'status-message status-error';
                                statusDiv.textContent = `❌ Preview failed: ${{result.error || 'Unknown error'}}`;
                                
                                resultsContent.innerHTML = `
                                    <div style="text-align: center; padding: 40px; color: #dc3545;">
                                        <div style="font-size: 2em; margin-bottom: 15px;">❌</div>
                                        <div>Preview failed. Please try again or check the CLI for more details.</div>
                                    </div>
                                `;
                                
                                loadingDiv.style.display = 'none';
                                resultsContent.style.display = 'block';
                            }}
                        }} else {{
                            // Process mode: first process, then automatically run preview
                            statusDiv.className = 'status-message status-info';
                            statusDiv.textContent = `🔄 Processing emails in background...`;
                            
                            const processResponse = await fetch(`/api/single-account/${{accountId}}/process`, {{
                                method: 'POST'
                            }});
                            const processResult = await processResponse.json();
                            
                            if (processResult.success) {{
                                // Processing successful - now automatically run preview to show remaining emails
                                statusDiv.textContent = `🔄 Processing completed! Loading current inbox state...`;
                                
                                const previewResponse = await fetch(`/api/single-account/${{accountId}}/preview`, {{
                                    method: 'POST'
                                }});
                                const previewResult = await previewResponse.json();
                                
                                if (previewResult.success) {{
                                    statusDiv.className = 'status-message status-success';
                                    statusDiv.textContent = `✅ Processing completed! Showing remaining emails in your inbox:`;
                                    
                                    // Display preview results (current state of inbox)
                                    const stats = previewResult.data;
                                    resultsContent.innerHTML = `
                                        <div class="stats-grid">
                                            <div class="stat-card">
                                                <div class="stat-value">${{stats.total_emails || 0}}</div>
                                                <div class="stat-label">Remaining Emails</div>
                                            </div>
                                            <div class="stat-card">
                                                <div class="stat-value" style="color: #dc3545;">${{stats.total_deleted || 0}}</div>
                                                <div class="stat-label">Would Delete</div>
                                            </div>
                                            <div class="stat-card">
                                                <div class="stat-value" style="color: #28a745;">${{stats.total_preserved || 0}}</div>
                                                <div class="stat-label">Preserved</div>
                                            </div>
                                            <div class="stat-card">
                                                <div class="stat-value">${{Object.keys(stats.categories || {{}}).length}}</div>
                                                <div class="stat-label">Categories</div>
                                            </div>
                                        </div>
                                        
                                        <div style="margin-top: 25px;">
                                            <h4>📊 Category Breakdown:</h4>
                                            <div id="categories-list">
                                                ${{Object.entries(stats.categories || {{}}).map(([category, count]) => 
                                                    `<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                                        <span>${{category}}</span>
                                                        <span style="font-weight: 600;">${{count}} emails</span>
                                                    </div>`
                                                ).join('')}}
                                            </div>
                                        </div>
                                        
                                        ${{stats.account_breakdown ? `
                                        <div style="margin-top: 25px;">
                                            <h4>🌐 Account Breakdown:</h4>
                                            <div id="account-breakdown-list">
                                                ${{stats.account_breakdown.map(account => 
                                                    account.error ? 
                                                    `<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; background-color: #fff5f5;">
                                                        <span style="color: #dc3545;">${{account.email}}</span>
                                                        <span style="color: #dc3545; font-weight: 600;">Error: ${{account.error}}</span>
                                                    </div>` :
                                                    `<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                                        <span>${{account.email}}</span>
                                                        <span style="font-weight: 600;">
                                                            <span style="color: #dc3545;">${{account.deleted}}</span> deleted, 
                                                            <span style="color: #28a745;">${{account.preserved}}</span> preserved
                                                        </span>
                                                    </div>`
                                                ).join('')}}
                                            </div>
                                        </div>
                                        ` : ''}}
                                        
                                        <div id="email-details-section" style="margin-top: 30px;">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                                <h4 style="margin: 0;">📧 Email Details:</h4>
                                                ${{!(typeof stats.session_id === 'string' && stats.session_id.startsWith('all_')) ? `
                                                <div>
                                                    <button id="show-session-emails" onclick="toggleEmailView('session')" style="background: #667eea; color: white; border: none; padding: 8px 12px; border-radius: 5px; margin-right: 5px; cursor: pointer; font-size: 0.9em;">Current Session</button>
                                                    <button id="show-all-emails" onclick="toggleEmailView('all')" style="background: #6c757d; color: white; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9em;">All Account Emails</button>
                                                </div>
                                                ` : ''}}
                                            </div>
                                            <div id="email-details-loading" style="text-align: center; padding: 20px; color: #6c757d;">
                                                <div style="font-size: 1.5em; margin-bottom: 10px;">⏳</div>
                                                Loading email details...
                                            </div>
                                            <div id="email-details-table" style="display: none;"></div>
                                        </div>
                                        
                                        <div style="margin-top: 25px; font-size: 0.9em; color: #6c757d;">
                                            Account: ${{stats.account_email}}<br>
                                            Processing Time: ${{new Date().toLocaleString()}}
                                        </div>
                                    `;
                                    
                                    // Load email details table (only if session_id is valid and not "all accounts")
                                    if (stats.session_id && stats.session_id !== 'undefined' && !(typeof stats.session_id === 'string' && stats.session_id.startsWith('all_'))) {{
                                        currentSessionId = stats.session_id;
                                        loadEmailDetails(stats.session_id);
                                    }} else if (stats.session_id && typeof stats.session_id === 'string' && stats.session_id.startsWith('all_')) {{
                                        // Handle "all accounts" mode - load emails from multiple sessions
                                        if (stats.session_ids && stats.session_ids.length > 0) {{
                                            loadAllAccountsEmailDetails(stats.session_ids);
                                        }} else {{
                                            document.getElementById('email-details-loading').innerHTML = `
                                                <div style="text-align: center; padding: 20px; color: #17a2b8;">
                                                    <div style="font-size: 1.5em; margin-bottom: 10px;">🌐</div>
                                                    All accounts processing complete. See account breakdown above for detailed results.
                                                </div>
                                            `;
                                        }}
                                    }} else {{
                                        document.getElementById('email-details-loading').innerHTML = `
                                            <div style="text-align: center; padding: 20px; color: #ffc107;">
                                                <div style="font-size: 1.5em; margin-bottom: 10px;">⚠️</div>
                                                Session ID not available. Email details cannot be loaded.
                                            </div>
                                        `;
                                    }}
                                    
                                    loadingDiv.style.display = 'none';
                                    resultsContent.style.display = 'block';
                                }} else {{
                                    statusDiv.className = 'status-message status-error';
                                    statusDiv.textContent = `❌ Failed to load current inbox state: ${{previewResult.error || 'Unknown error'}}`;
                                    
                                    resultsContent.innerHTML = `
                                        <div style="text-align: center; padding: 40px; color: #dc3545;">
                                            <div style="font-size: 2em; margin-bottom: 15px;">❌</div>
                                            <div>Processing completed but failed to load current state. Please try Preview to see remaining emails.</div>
                                        </div>
                                    `;
                                    
                                    loadingDiv.style.display = 'none';
                                    resultsContent.style.display = 'block';
                                }}
                            }} else {{
                                statusDiv.className = 'status-message status-error';
                                statusDiv.textContent = `❌ Processing failed: ${{processResult.error || 'Unknown error'}}`;
                                
                                resultsContent.innerHTML = `
                                    <div style="text-align: center; padding: 40px; color: #dc3545;">
                                        <div style="font-size: 2em; margin-bottom: 15px;">❌</div>
                                        <div>Processing failed. Please try again or check the CLI for more details.</div>
                                    </div>
                                `;
                                
                                loadingDiv.style.display = 'none';
                                resultsContent.style.display = 'block';
                            }}
                        }}
                    }} catch (error) {{
                        statusDiv.className = 'status-message status-error';
                        statusDiv.textContent = `❌ Error: ${{error.message}}`;
                        
                        resultsContent.innerHTML = `
                            <div style="text-align: center; padding: 40px; color: #dc3545;">
                                <div style="font-size: 2em; margin-bottom: 15px;">⚠️</div>
                                <div>Network error. Please check your connection and try again.</div>
                            </div>
                        `;
                        
                        loadingDiv.style.display = 'none';
                        resultsContent.style.display = 'block';
                    }}
                    
                    // Auto-hide status message after 10 seconds
                    setTimeout(() => {{
                        statusDiv.style.display = 'none';
                    }}, 10000);
                }}
                
                async function loadEmailDetails(sessionId) {{
                    const loadingDiv = document.getElementById('email-details-loading');
                    const tableDiv = document.getElementById('email-details-table');
                    
                    try {{
                        const response = await fetch(`/api/single-account/${{accountId}}/emails/${{sessionId}}`);
                        const result = await response.json();
                        
                        if (result.success && result.emails) {{
                            const emails = result.emails;
                            
                            if (emails.length === 0) {{
                                tableDiv.innerHTML = `
                                    <div style="text-align: center; padding: 20px; color: #6c757d;">
                                        <div style="font-size: 1.5em; margin-bottom: 10px;">📭</div>
                                        No emails found for this session.
                                    </div>
                                `;
                            }} else {{
                                displayEmailTable(emails, `all ${{emails.length}} emails from session ${{sessionId}}`);
                            }}
                            
                            loadingDiv.style.display = 'none';
                            tableDiv.style.display = 'block';
                        }} else {{
                            tableDiv.innerHTML = `
                                <div style="text-align: center; padding: 20px; color: #dc3545;">
                                    <div style="font-size: 1.5em; margin-bottom: 10px;">❌</div>
                                    Failed to load email details: ${{result.error || 'Unknown error'}}
                                </div>
                            `;
                            loadingDiv.style.display = 'none';
                            tableDiv.style.display = 'block';
                        }}
                    }} catch (error) {{
                        tableDiv.innerHTML = `
                            <div style="text-align: center; padding: 20px; color: #dc3545;">
                                <div style="font-size: 1.5em; margin-bottom: 10px;">⚠️</div>
                                Network error loading email details: ${{error.message}}
                            </div>
                        `;
                        loadingDiv.style.display = 'none';
                        tableDiv.style.display = 'block';
                    }}
                }}
                
                function getCategoryColor(category) {{
                    const colors = {{
                        'Phishing': '#dc3545',
                        'Brand Impersonation': '#fd7e14',
                        'Financial & Investment Spam': '#6f42c1',
                        'Adult & Dating Spam': '#e83e8c',
                        'Marketing Spam': '#20c997',
                        'Health & Medical Spam': '#17a2b8',
                        'Payment Scam': '#dc3545',
                        'Prize & Reward Scam': '#ffc107',
                        'Promotional Email': '#28a745',
                        'Storage & Backup Scam': '#6c757d',
                        'Not Spam': '#28a745'
                    }};
                    return colors[category] || '#6c757d';
                }}
                
                let currentSessionId = null;
                
                function toggleEmailView(view) {{
                    const sessionBtn = document.getElementById('show-session-emails');
                    const allBtn = document.getElementById('show-all-emails');
                    const loadingDiv = document.getElementById('email-details-loading');
                    const tableDiv = document.getElementById('email-details-table');
                    
                    // Update button styles
                    if (view === 'session') {{
                        sessionBtn.style.background = '#667eea';
                        allBtn.style.background = '#6c757d';
                        
                        if (currentSessionId) {{
                            loadEmailDetails(currentSessionId);
                        }}
                    }} else {{
                        sessionBtn.style.background = '#6c757d';
                        allBtn.style.background = '#667eea';
                        
                        loadAllAccountEmails();
                    }}
                }}
                
                async function loadAllAccountEmails() {{
                    const loadingDiv = document.getElementById('email-details-loading');
                    const tableDiv = document.getElementById('email-details-table');
                    
                    loadingDiv.style.display = 'block';
                    tableDiv.style.display = 'none';
                    loadingDiv.innerHTML = `
                        <div style="text-align: center; padding: 20px; color: #6c757d;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">⏳</div>
                            Loading all account emails...
                        </div>
                    `;
                    
                    try {{
                        const response = await fetch(`/api/single-account/${{accountId}}/all-emails`);
                        const result = await response.json();
                        
                        if (result.success && result.emails) {{
                            const emails = result.emails;
                            
                            if (emails.length === 0) {{
                                tableDiv.innerHTML = `
                                    <div style="text-align: center; padding: 20px; color: #6c757d;">
                                        <div style="font-size: 1.5em; margin-bottom: 10px;">📭</div>
                                        No emails found for this account.
                                    </div>
                                `;
                            }} else {{
                                displayEmailTable(emails, `all ${{emails.length}} account emails`);
                            }}
                            
                            loadingDiv.style.display = 'none';
                            tableDiv.style.display = 'block';
                        }} else {{
                            tableDiv.innerHTML = `
                                <div style="text-align: center; padding: 20px; color: #dc3545;">
                                    <div style="font-size: 1.5em; margin-bottom: 10px;">❌</div>
                                    Failed to load account emails: ${{result.error || 'Unknown error'}}
                                </div>
                            `;
                            loadingDiv.style.display = 'none';
                            tableDiv.style.display = 'block';
                        }}
                    }} catch (error) {{
                        tableDiv.innerHTML = `
                            <div style="text-align: center; padding: 20px; color: #dc3545;">
                                <div style="font-size: 1.5em; margin-bottom: 10px;">⚠️</div>
                                Network error loading account emails: ${{error.message}}
                            </div>
                        `;
                        loadingDiv.style.display = 'none';
                        tableDiv.style.display = 'block';
                    }}
                }}
                
                function displayEmailTable(emails, description) {{
                    const tableDiv = document.getElementById('email-details-table');
                    
                    tableDiv.innerHTML = `
                        <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
                            <div class="email-table-container" style="overflow-x: auto;">
                                <table class="email-table" style="width: 100%; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600; width: 80px;">🔍 Research</th>
                                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; font-weight: 600;">Sender</th>
                                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; font-weight: 600;">Subject</th>
                                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; font-weight: 600;">Category</th>
                                            <th class="email-column-confidence" style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600;">Confidence</th>
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600;">Protection</th>
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600;">Action</th>
                                            <th class="email-column-date" style="padding: 12px; text-align: center; font-weight: 600;">Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${{emails.map(email => `
                                            <tr style="border-bottom: 1px solid #eee;">
                                                <td class="email-cell email-cell-compact" style="padding: 10px; border-right: 1px solid #eee; text-align: center; width: 80px;">
                                                    <input type="checkbox" 
                                                           onchange="toggleResearchFlag('${{email.uid || ''}}', '${{email.folder_name || ''}}', ${{email.account_id || 0}}, this)"
                                                           ${{email.is_research_flagged ? 'checked' : ''}}
                                                           style="cursor: pointer; transform: scale(1.2);"
                                                           title="Flag for research investigation">
                                                </td>
                                                <td class="email-cell email-cell-sender" style="padding: 10px; border-right: 1px solid #eee; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${{email.sender}}">
                                                    ${{email.sender}}
                                                </td>
                                                <td class="email-cell email-cell-subject" style="padding: 10px; border-right: 1px solid #eee; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${{email.subject}}">
                                                    ${{email.subject}}
                                                </td>
                                                <td class="email-cell" style="padding: 10px; border-right: 1px solid #eee;">
                                                    <span style="background: ${{getCategoryColor(email.category)}}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;">
                                                        ${{email.category}}
                                                    </span>
                                                </td>
                                                <td class="email-cell email-column-confidence" style="padding: 10px; border-right: 1px solid #eee; text-align: center;">
                                                    <span style="font-weight: 500; color: ${{email.confidence >= 70 ? '#28a745' : email.confidence >= 40 ? '#ffc107' : '#dc3545'}};">
                                                        ${{Math.round(email.confidence)}}%
                                                    </span>
                                                </td>
                                                <td class="email-cell" style="padding: 10px; border-right: 1px solid #eee; text-align: center;">
                                                    <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                                                        <span style="font-size: 0.8em; color: #6c757d; font-weight: 500;">
                                                            ${{email.is_protected ? 'Protected' : (email.action === 'DELETED' && !email.is_protected) || email.is_flagged_for_deletion ? 'Delete' : ''}}
                                                        </span>
                                                        ${{email.action === 'DELETED' ? `
                                                            <button onclick="toggleEmailFlagInTable('${{email.uid || ''}}', '${{email.folder_name || ''}}', ${{email.account_id || 0}}, ${{email.is_protected || false}}, this, 'protect')" 
                                                                    style="border: 1px solid ${{email.is_protected ? '#dc3545' : '#28a745'}}; background: #f8f9fa; color: ${{email.is_protected ? '#dc3545' : '#28a745'}}; padding: 2px 6px; border-radius: 3px; font-size: 0.75em; cursor: pointer; transition: all 0.2s;">
                                                                ${{email.is_protected ? 'Unmark Protection' : 'Mark for Protection'}}
                                                            </button>
                                                        ` : `
                                                            <button onclick="toggleEmailFlagInTable('${{email.uid || ''}}', '${{email.folder_name || ''}}', ${{email.account_id || 0}}, ${{email.is_flagged_for_deletion || false}}, this, 'delete')" 
                                                                    style="border: 1px solid ${{email.is_flagged_for_deletion ? '#dc3545' : '#fd7e14'}}; background: #f8f9fa; color: ${{email.is_flagged_for_deletion ? '#dc3545' : '#fd7e14'}}; padding: 2px 6px; border-radius: 3px; font-size: 0.75em; cursor: pointer; transition: all 0.2s;">
                                                                ${{email.is_flagged_for_deletion ? 'Unmark for Deletion' : 'Mark for Deletion'}}
                                                            </button>
                                                        `}}
                                                    </div>
                                                </td>
                                                <td class="email-cell" style="padding: 10px; border-right: 1px solid #eee; text-align: center;">
                                                    <span style="background: ${{email.action === 'DELETED' ? '#dc3545' : '#28a745'}}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;">
                                                        ${{email.action}}
                                                    </span>
                                                </td>
                                                <td class="email-cell email-column-date" style="padding: 10px; text-align: center; font-size: 0.85em; color: #6c757d;">
                                                    ${{new Date(email.timestamp).toLocaleDateString()}}
                                                </td>
                                            </tr>
                                        `).join('')}}
                                    </tbody>
                                </table>
                            </div>
                            <div style="padding: 15px; background: #f8f9fa; border-top: 1px solid #dee2e6; font-size: 0.9em; color: #6c757d; text-align: center;">
                                Showing ${{description}}
                                <br>
                                <span style="font-size: 0.85em;">(${{emails.filter(e => e.action === 'DELETED' || e.action === 'WOULD DELETE').length}} deleted, ${{emails.filter(e => e.action === 'PRESERVED' || e.action === 'WOULD PRESERVE').length}} preserved)</span>
                            </div>
                        </div>
                    `;
                }}
                
                // Toggle email flag function for table view (handles both protect and delete flags)
                async function toggleEmailFlagInTable(emailUid, folderName, accountId, currentlyFlagged, buttonElement, flagType = 'protect') {{
                    try {{
                        console.log('toggleEmailFlagInTable called:', {{ emailUid, folderName, accountId, currentlyFlagged, flagType }});
                        
                        // Validate required parameters
                        if (!emailUid || !folderName || !accountId || accountId === 0) {{
                            throw new Error(`❌ Cannot flag this email: Missing email UID or folder information. This email may be from an older session before flagging was enabled.`);
                        }}
                        
                        // Disable button during operation
                        buttonElement.disabled = true;
                        const originalText = buttonElement.textContent;
                        buttonElement.textContent = 'Working...';
                        
                        let endpoint, requestData, successMessage;
                        
                        if (flagType === 'protect') {{
                            // Handle protection flags (for DELETED emails)
                            const action = currentlyFlagged ? 'unflag' : 'flag';
                            endpoint = '/api/emails/' + action;
                            requestData = {{
                                email_uid: emailUid,
                                folder_name: folderName,
                                account_id: parseInt(accountId)
                            }};
                            if (action === 'flag') {{
                                requestData.flag_reason = 'User requested protection from deletion';
                            }}
                            successMessage = currentlyFlagged ? 
                                'Email protection removed' : 
                                'Email protected from deletion';
                        }} else {{
                            // Handle delete flags (for PRESERVED emails)
                            if (currentlyFlagged) {{
                                // Remove delete flag (unflag)
                                endpoint = '/api/emails/unflag';
                                requestData = {{
                                    email_uid: emailUid,
                                    folder_name: folderName,
                                    account_id: parseInt(accountId)
                                }};
                                successMessage = 'Email unmarked for deletion';
                            }} else {{
                                // Add delete flag
                                endpoint = '/api/emails/flag-for-deletion';
                                requestData = {{
                                    email_uid: emailUid,
                                    folder_name: folderName,
                                    account_id: parseInt(accountId),
                                    flag_reason: 'User requested deletion override'
                                }};
                                successMessage = 'Email marked for deletion';
                            }}
                        }}
                        
                        // Make API call
                        const response = await fetch(endpoint, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify(requestData)
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            // Update UI to reflect new state
                            const newFlaggedState = !currentlyFlagged;
                            
                            // Update the status text and button based on flag type
                            const statusSpan = buttonElement.parentElement.querySelector('span');
                            
                            if (flagType === 'protect') {{
                                statusSpan.textContent = newFlaggedState ? 'Protected' : '';
                                buttonElement.textContent = newFlaggedState ? 'Unmark Protection' : 'Mark for Protection';
                                buttonElement.style.borderColor = newFlaggedState ? '#dc3545' : '#28a745';
                                buttonElement.style.color = newFlaggedState ? '#dc3545' : '#28a745';
                                
                                // Update onclick handler for new state
                                buttonElement.onclick = function() {{
                                    toggleEmailFlagInTable(emailUid, folderName, accountId, newFlaggedState, this, 'protect');
                                }};
                            }} else {{
                                statusSpan.textContent = newFlaggedState ? 'Delete' : '';
                                buttonElement.textContent = newFlaggedState ? 'Unmark for Deletion' : 'Mark for Deletion';
                                buttonElement.style.borderColor = newFlaggedState ? '#dc3545' : '#fd7e14';
                                buttonElement.style.color = newFlaggedState ? '#dc3545' : '#fd7e14';
                                
                                // Update onclick handler for new state
                                buttonElement.onclick = function() {{
                                    toggleEmailFlagInTable(emailUid, folderName, accountId, newFlaggedState, this, 'delete');
                                }};
                            }}
                            
                            // Show success message
                            showSuccessMessage(successMessage);
                            
                        }} else {{
                            throw new Error(result.message || 'Failed to update email flag');
                        }}
                        
                    }} catch (error) {{
                        console.error('Flag toggle error:', error);
                        alert('❌ Error updating protection: ' + error.message);
                        
                        // Reset button on error
                        buttonElement.disabled = false;
                        buttonElement.textContent = originalText;
                    }} finally {{
                        // Re-enable button
                        buttonElement.disabled = false;
                    }}
                }}
                
                // Toggle research flag function for checkbox
                async function toggleResearchFlag(emailUid, folderName, accountId, checkboxElement) {{
                    try {{
                        console.log('toggleResearchFlag called:', {{ emailUid, folderName, accountId, checked: checkboxElement.checked }});
                        
                        // Validate required parameters
                        if (!emailUid || !folderName || !accountId || accountId === 0) {{
                            throw new Error(`❌ Cannot flag this email: Missing email UID or folder information.`);
                        }}
                        
                        // Disable checkbox during operation
                        checkboxElement.disabled = true;
                        
                        const endpoint = checkboxElement.checked ? '/api/flag-for-research' : '/api/unflag-research';
                        const requestData = {{
                            email_uid: emailUid,
                            folder_name: folderName,
                            account_id: parseInt(accountId),
                            flag_reason: 'User requested classification investigation'
                        }};
                        
                        const response = await fetch(endpoint, {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify(requestData)
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            const message = checkboxElement.checked ? 
                                'Email flagged for research investigation' : 
                                'Email research flag removed';
                            showSuccessMessage(message);
                        }} else {{
                            throw new Error(result.message || 'Failed to update research flag');
                        }}
                        
                    }} catch (error) {{
                        console.error('Research flag toggle error:', error);
                        alert('❌ Error updating research flag: ' + error.message);
                        
                        // Reset checkbox on error
                        checkboxElement.checked = !checkboxElement.checked;
                    }} finally {{
                        // Re-enable checkbox
                        checkboxElement.disabled = false;
                    }}
                }}
                
                function showSuccessMessage(message) {{
                    // Create and show a temporary success message
                    const messageDiv = document.createElement('div');
                    messageDiv.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #28a745;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                        z-index: 1000;
                        animation: slideIn 0.3s ease;
                    `;
                    messageDiv.textContent = message;
                    
                    document.body.appendChild(messageDiv);
                    
                    // Remove after 3 seconds
                    setTimeout(() => {{
                        messageDiv.style.animation = 'slideOut 0.3s ease';
                        setTimeout(() => messageDiv.remove(), 300);
                    }}, 3000);
                }}
                
                async function loadAllAccountsEmailDetails(sessionIds) {{
                    const loadingDiv = document.getElementById('email-details-loading');
                    const tableDiv = document.getElementById('email-details-table');
                    
                    loadingDiv.style.display = 'block';
                    tableDiv.style.display = 'none';
                    loadingDiv.innerHTML = `
                        <div style="text-align: center; padding: 20px; color: #6c757d;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">⏳</div>
                            Loading emails from all accounts...
                        </div>
                    `;
                    
                    try {{
                        // Convert sessionIds array to JSON string for API call
                        const sessionIdsParam = encodeURIComponent(JSON.stringify(sessionIds));
                        const response = await fetch(`/api/all-accounts/emails?session_ids=${{sessionIdsParam}}`);
                        const result = await response.json();
                        
                        if (result.success && result.emails) {{
                            const emails = result.emails;
                            
                            if (emails.length === 0) {{
                                tableDiv.innerHTML = `
                                    <div style="text-align: center; padding: 20px; color: #6c757d;">
                                        <div style="font-size: 1.5em; margin-bottom: 10px;">📭</div>
                                        No emails found across all accounts.
                                    </div>
                                `;
                            }} else {{
                                displayAllAccountsEmailTable(emails, `${{emails.length}} emails from ${{result.session_count}} accounts`);
                            }}
                            
                            loadingDiv.style.display = 'none';
                            tableDiv.style.display = 'block';
                        }} else {{
                            tableDiv.innerHTML = `
                                <div style="text-align: center; padding: 20px; color: #dc3545;">
                                    <div style="font-size: 1.5em; margin-bottom: 10px;">❌</div>
                                    Failed to load all accounts emails: ${{result.error || 'Unknown error'}}
                                </div>
                            `;
                            loadingDiv.style.display = 'none';
                            tableDiv.style.display = 'block';
                        }}
                    }} catch (error) {{
                        tableDiv.innerHTML = `
                            <div style="text-align: center; padding: 20px; color: #dc3545;">
                                <div style="font-size: 1.5em; margin-bottom: 10px;">⚠️</div>
                                Network error loading all accounts emails: ${{error.message}}
                            </div>
                        `;
                        loadingDiv.style.display = 'none';
                        tableDiv.style.display = 'block';
                    }}
                }}
                
                function displayAllAccountsEmailTable(emails, description) {{
                    const tableDiv = document.getElementById('email-details-table');
                    
                    tableDiv.innerHTML = `
                        <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
                            <div class="email-table-container" style="overflow-x: auto;">
                                <table class="email-table" style="width: 100%; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600; width: 80px;">🔍 Research</th>
                                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; font-weight: 600; width: 140px;">Account</th>
                                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; font-weight: 600; width: 180px;">Sender</th>
                                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; font-weight: 600; width: 250px;">Subject</th>
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600; width: 140px;">Category</th>
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600; width: 90px;" class="email-column-confidence">Confidence</th>
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600; width: 110px;">Protection</th>
                                            <th style="padding: 12px; text-align: center; border-right: 1px solid #dee2e6; font-weight: 600; width: 100px;">Action</th>
                                            <th style="padding: 12px; text-align: center; font-weight: 600; width: 100px;" class="email-column-date">Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${{emails.map(email => `
                                            <tr style="border-bottom: 1px solid #eee;">
                                                <td class="email-cell email-cell-compact" style="padding: 10px; border-right: 1px solid #eee; text-align: center; width: 80px;">
                                                    <input type="checkbox" 
                                                           onchange="toggleResearchFlag('${{email.uid || ''}}', '${{email.folder_name || ''}}', ${{email.account_id || 0}}, this)"
                                                           ${{email.is_research_flagged ? 'checked' : ''}}
                                                           style="cursor: pointer; transform: scale(1.2);"
                                                           title="Flag for research investigation">
                                                </td>
                                                <td class="email-cell email-cell-account" style="padding: 10px; border-right: 1px solid #eee; width: 140px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.85em; color: #6c757d;" title="${{email.account_email}}">
                                                    ${{email.account_email}}
                                                </td>
                                                <td class="email-cell email-cell-sender" style="padding: 10px; border-right: 1px solid #eee; width: 180px; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${{email.sender}}">
                                                    ${{email.sender}}
                                                </td>
                                                <td class="email-cell email-cell-subject" style="padding: 10px; border-right: 1px solid #eee; width: 250px; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${{email.subject}}">
                                                    ${{email.subject}}
                                                </td>
                                                <td class="email-cell" style="padding: 10px; border-right: 1px solid #eee; width: 140px; text-align: center;">
                                                    <span style="background: ${{getCategoryColor(email.category)}}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;">
                                                        ${{email.category}}
                                                    </span>
                                                </td>
                                                <td class="email-cell email-column-confidence" style="padding: 10px; border-right: 1px solid #eee; width: 90px; text-align: center;">
                                                    <span style="font-weight: 500; color: ${{email.confidence >= 70 ? '#28a745' : email.confidence >= 40 ? '#ffc107' : '#dc3545'}};">
                                                        ${{Math.round(email.confidence)}}%
                                                    </span>
                                                </td>
                                                <td class="email-cell" style="padding: 10px; border-right: 1px solid #eee; width: 110px; text-align: center;">
                                                    <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                                                        <span style="font-size: 0.8em; color: #6c757d; font-weight: 500;">
                                                            ${{email.is_protected ? 'Protected' : (email.action === 'DELETED' && !email.is_protected) || email.is_flagged_for_deletion ? 'Delete' : ''}}
                                                        </span>
                                                        ${{email.action === 'DELETED' ? `
                                                            <button onclick="toggleEmailFlagInTable('${{email.uid || ''}}', '${{email.folder_name || ''}}', ${{email.account_id || 0}}, ${{email.is_protected || false}}, this, 'protect')" 
                                                                    style="border: 1px solid ${{email.is_protected ? '#dc3545' : '#28a745'}}; background: #f8f9fa; color: ${{email.is_protected ? '#dc3545' : '#28a745'}}; padding: 2px 6px; border-radius: 3px; font-size: 0.75em; cursor: pointer; transition: all 0.2s;">
                                                                ${{email.is_protected ? 'Unmark Protection' : 'Mark for Protection'}}
                                                            </button>
                                                        ` : `
                                                            <button onclick="toggleEmailFlagInTable('${{email.uid || ''}}', '${{email.folder_name || ''}}', ${{email.account_id || 0}}, ${{email.is_flagged_for_deletion || false}}, this, 'delete')" 
                                                                    style="border: 1px solid ${{email.is_flagged_for_deletion ? '#dc3545' : '#fd7e14'}}; background: #f8f9fa; color: ${{email.is_flagged_for_deletion ? '#dc3545' : '#fd7e14'}}; padding: 2px 6px; border-radius: 3px; font-size: 0.75em; cursor: pointer; transition: all 0.2s;">
                                                                ${{email.is_flagged_for_deletion ? 'Unmark for Deletion' : 'Mark for Deletion'}}
                                                            </button>
                                                        `}}
                                                    </div>
                                                </td>
                                                <td class="email-cell" style="padding: 10px; border-right: 1px solid #eee; width: 100px; text-align: center;">
                                                    <span style="background: ${{email.action === 'DELETED' ? '#dc3545' : '#28a745'}}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;">
                                                        ${{email.action}}
                                                    </span>
                                                </td>
                                                <td class="email-cell email-column-date" style="padding: 10px; width: 100px; text-align: center; font-size: 0.85em; color: #6c757d;">
                                                    ${{new Date(email.timestamp).toLocaleDateString()}}
                                                </td>
                                            </tr>
                                        `).join('')}}
                                    </tbody>
                                </table>
                            </div>
                            <div style="padding: 15px; background: #f8f9fa; border-top: 1px solid #dee2e6; font-size: 0.9em; color: #6c757d; text-align: center;">
                                Showing ${{description}}
                                <br>
                                <span style="font-size: 0.85em;">(${{emails.filter(e => e.action === 'DELETED' || e.action === 'WOULD DELETE').length}} deleted, ${{emails.filter(e => e.action === 'PRESERVED' || e.action === 'WOULD PRESERVE').length}} preserved)</span>
                            </div>
                        </div>
                    `;
                }}
            </script>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"""
        <html>
        <head><title>Single Account Error</title></head>
        <body>
            <h1>Error Loading Account</h1>
            <p>Error: {str(e)}</p>
            <a href="/accounts">← Back to Accounts</a>
        </body>
        </html>
        """

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
