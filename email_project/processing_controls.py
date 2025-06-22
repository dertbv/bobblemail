#!/usr/bin/env python3
"""
Real-time Processing Controls
Enhanced web interface for email processing with live/preview modes
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union

# Import existing modules
from database import db
from db_logger import logger, LogCategory
from db_credentials import db_credentials
from processing_controller import run_preview_for_account
from email_processor import EmailProcessor
from config_auth import IMAPConnectionManager

class ProcessingController:
    """Main controller for real-time email processing operations"""
    
    def __init__(self):
        self.supported_modes = ['preview', 'live', 'folder_management']
        self.processing_state = {}
        
    def get_account_folders(self, account_id: int) -> Dict:
        """Get folder structure for an account"""
        try:
            account = db_credentials.get_account_by_id(account_id)
            if not account:
                return {"success": False, "message": "Account not found"}
            
            # Create temporary connection to get folder list
            class SingleAccountCredentials:
                def select_account(self):
                    return account
            
            temp_credentials = SingleAccountCredentials()
            connection_manager = IMAPConnectionManager(temp_credentials)
            mail = connection_manager.connect_to_imap()
            
            if not mail:
                return {"success": False, "message": "Failed to connect to IMAP"}
            
            # Get folder list
            folders = []
            try:
                result, folder_list = mail.list()
                if result == 'OK':
                    for folder_data in folder_list:
                        if folder_data:
                            # Parse folder names (simplified)
                            folder_name = folder_data.decode().split(' "/" ')[-1].strip('"')
                            folders.append({
                                "name": folder_name,
                                "selectable": True,
                                "message_count": None  # We'll get this on demand
                            })
            except Exception as e:
                print(f"Error getting folders: {e}")
                
            connection_manager.disconnect()
            
            return {
                "success": True,
                "account_email": account['email_address'],
                "provider": account.get('provider', 'unknown'),
                "folders": folders
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error getting folders: {str(e)}"}
    
    def get_folder_message_count(self, account_id: int, folder_name: str) -> Dict:
        """Get message count for a specific folder"""
        try:
            account = db_credentials.get_account_by_id(account_id)
            if not account:
                return {"success": False, "message": "Account not found"}
            
            # Create temporary connection
            class SingleAccountCredentials:
                def select_account(self):
                    return account
            
            temp_credentials = SingleAccountCredentials()
            connection_manager = IMAPConnectionManager(temp_credentials)
            mail = connection_manager.connect_to_imap()
            
            if not mail:
                return {"success": False, "message": "Failed to connect to IMAP"}
            
            try:
                # Select folder and get count
                result, _ = mail.select(folder_name, readonly=True)
                if result == 'OK':
                    result, messages = mail.search(None, 'ALL')
                    if result == 'OK':
                        message_count = len(messages[0].split()) if messages[0] else 0
                        connection_manager.disconnect()
                        return {
                            "success": True,
                            "folder_name": folder_name,
                            "message_count": message_count
                        }
                        
            except Exception as e:
                print(f"Error counting messages in {folder_name}: {e}")
                
            connection_manager.disconnect()
            return {"success": False, "message": f"Could not access folder {folder_name}"}
            
        except Exception as e:
            return {"success": False, "message": f"Error counting messages: {str(e)}"}
    
    def run_preview_mode(self, account_id: int, folders: Optional[List[str]] = None) -> Dict:
        """Run preview mode on specified account and folders"""
        try:
            print(f"🔍 Running preview mode for account {account_id}")
            
            # Use existing preview function
            result = run_preview_for_account(account_id, debug_mode=True)
            
            if not result["success"]:
                return result
            
            # Get detailed email preview from the session
            session_id = result["session_id"]
            preview_emails = db.execute_query("""
                SELECT 
                    datetime(timestamp) as formatted_time,
                    timestamp,
                    folder_name,
                    uid,
                    sender_email, 
                    sender_domain,
                    subject, 
                    action,
                    reason,
                    category,
                    confidence_score
                FROM processed_emails_bulletproof 
                WHERE session_id = ?
                ORDER BY datetime(timestamp) DESC
                LIMIT 50
            """, (session_id,))
            
            # Format for display with flag status
            formatted_emails = []
            for email in preview_emails:
                try:
                    dt = datetime.fromisoformat(email['timestamp'].replace('T', ' ').replace('Z', ''))
                    action = "WOULD DELETE" if email['action'] == 'DELETED' else "WOULD PRESERVE"
                    
                    # Check if email is flagged for protection
                    is_flagged = False
                    if email['uid'] and email['folder_name']:
                        is_flagged = db.is_email_flagged(
                            email_uid=email['uid'],
                            folder_name=email['folder_name'],
                            account_id=account_id
                        )
                    
                    formatted_emails.append({
                        "date": dt.strftime("%m/%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "folder": email['folder_name'] or "",
                        "uid": email['uid'] or "",
                        "action": action,
                        "sender_email": email['sender_email'] or "",
                        "subject": email['subject'] or "",
                        "reason": email['reason'] or "",
                        "category": email['category'] or "Unknown",
                        "confidence": f"{email['confidence_score']:.1f}" if email['confidence_score'] else "",
                        "is_flagged": is_flagged,
                        "account_id": account_id  # Include for flagging operations
                    })
                except Exception as e:
                    print(f"Error formatting email: {e}")
                    continue
            
            return {
                "success": True,
                "mode": "preview",
                "account_email": result.get("account_email", ""),
                "total_emails": len(formatted_emails),
                "would_delete": len([e for e in formatted_emails if "DELETE" in e['action']]),
                "would_preserve": len([e for e in formatted_emails if "PRESERVE" in e['action']]),
                "emails": formatted_emails,
                "session_id": session_id
            }
            
        except Exception as e:
            print(f"❌ Preview mode error: {e}")
            return {"success": False, "message": f"Preview mode failed: {str(e)}"}
    
    def run_live_mode(self, account_id: int, folders: Optional[List[str]] = None, 
                     confirmation_token: Optional[str] = None) -> Dict:
        """Run live processing mode with actual email deletion"""
        try:
            print(f"🚀 Running LIVE processing mode for account {account_id}")
            
            # Require confirmation for live mode
            if not confirmation_token or confirmation_token != "CONFIRM_LIVE_PROCESSING":
                return {
                    "success": False, 
                    "message": "Live processing requires explicit confirmation",
                    "confirmation_required": True
                }
            
            # Use existing function with preview_mode=False for actual processing
            result = run_preview_for_account(account_id, debug_mode=True, preview_mode=False)
            
            if not result["success"]:
                return result
            
            # Get actual processing results
            session_id = result["session_id"]
            processed_emails = db.execute_query("""
                SELECT 
                    datetime(timestamp) as formatted_time,
                    timestamp,
                    folder_name,
                    uid,
                    sender_email, 
                    subject, 
                    action,
                    reason,
                    category,
                    confidence_score
                FROM processed_emails_bulletproof 
                WHERE session_id = ?
                ORDER BY datetime(timestamp) DESC
                LIMIT 50
            """, (session_id,))
            
            # Format results
            formatted_emails = []
            actual_deleted = 0
            actual_preserved = 0
            
            for email in processed_emails:
                try:
                    dt = datetime.fromisoformat(email['timestamp'].replace('T', ' ').replace('Z', ''))
                    
                    if email['action'] == 'DELETED':
                        actual_deleted += 1
                    else:
                        actual_preserved += 1
                    
                    formatted_emails.append({
                        "date": dt.strftime("%m/%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "folder": email['folder_name'] or "",
                        "uid": email['uid'] or "",
                        "action": email['action'],
                        "sender_email": email['sender_email'] or "",
                        "subject": email['subject'] or "",
                        "reason": email['reason'] or "",
                        "category": email['category'] or "Unknown",
                        "confidence": f"{email['confidence_score']:.1f}" if email['confidence_score'] else ""
                    })
                except Exception as e:
                    print(f"Error formatting email: {e}")
                    continue
            
            return {
                "success": True,
                "mode": "live",
                "account_email": result.get("account_email", ""),
                "total_emails": len(formatted_emails),
                "actual_deleted": actual_deleted,
                "actual_preserved": actual_preserved,
                "emails": formatted_emails,
                "session_id": session_id
            }
            
        except Exception as e:
            print(f"❌ Live processing error: {e}")
            return {"success": False, "message": f"Live processing failed: {str(e)}"}
    
    def get_processing_config(self, account_id: int) -> Dict:
        """Get processing configuration for an account"""
        try:
            # Get saved config from database (if exists)
            config = db.execute_query("""
                SELECT config_data FROM processing_configs 
                WHERE account_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (account_id,))
            
            if config:
                return {
                    "success": True,
                    "config": json.loads(config[0]['config_data'])
                }
            else:
                # Default configuration
                return {
                    "success": True,
                    "config": {
                        "default_mode": "preview",
                        "auto_confirm": False,
                        "debug_mode": False,
                        "enabled_folders": ["INBOX"],
                        "custom_keywords": [],
                        "provider_optimizations": True
                    }
                }
                
        except Exception as e:
            return {"success": False, "message": f"Error getting config: {str(e)}"}
    
    def save_processing_config(self, account_id: int, config: Dict) -> Dict:
        """Save processing configuration for an account"""
        try:
            # Create processing_configs table if it doesn't exist
            db.execute_query("""
                CREATE TABLE IF NOT EXISTS processing_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    config_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """)
            
            # Save configuration
            db.execute_query("""
                INSERT INTO processing_configs (account_id, config_data)
                VALUES (?, ?)
            """, (account_id, json.dumps(config)))
            
            return {"success": True, "message": "Configuration saved successfully"}
            
        except Exception as e:
            return {"success": False, "message": f"Error saving config: {str(e)}"}

def create_processing_controls_routes():
    """Create FastAPI routes for processing controls - to be imported by web_app.py"""
    
    from fastapi import Request
    from fastapi.responses import JSONResponse, HTMLResponse
    
    controller = ProcessingController()
    
    routes = []
    
    # API Routes
    async def get_account_folders_api(account_id: int):
        """Get folders for an account"""
        result = controller.get_account_folders(account_id)
        return JSONResponse(result)
    
    async def get_folder_count_api(account_id: int, folder_name: str):
        """Get message count for a folder"""
        result = controller.get_folder_message_count(account_id, folder_name)
        return JSONResponse(result)
    
    async def run_preview_api(account_id: int, request: Request):
        """Run preview mode"""
        data = await request.json() if request.method == 'POST' else {}
        folders = data.get('folders', None)
        result = controller.run_preview_mode(account_id, folders)
        return JSONResponse(result)
    
    async def run_live_api(account_id: int, request: Request):
        """Run live processing mode"""
        data = await request.json()
        folders = data.get('folders', None)
        confirmation = data.get('confirmation_token', None)
        result = controller.run_live_mode(account_id, folders, confirmation)
        return JSONResponse(result)
    
    async def get_config_api(account_id: int):
        """Get processing configuration"""
        result = controller.get_processing_config(account_id)
        return JSONResponse(result)
    
    async def save_config_api(account_id: int, request: Request):
        """Save processing configuration"""
        config = await request.json()
        result = controller.save_processing_config(account_id, config)
        return JSONResponse(result)
    
    # Processing Controls Page
    async def processing_controls_page():
        """Main processing controls page"""
        try:
            accounts = db_credentials.load_credentials()
            return build_processing_controls_html(accounts)
        except Exception as e:
            return HTMLResponse(f"<h1>Error: {e}</h1>")
    
    return {
        'processing_controls_page': processing_controls_page,
        'get_account_folders_api': get_account_folders_api,
        'get_folder_count_api': get_folder_count_api,
        'run_preview_api': run_preview_api,
        'run_live_api': run_live_api,
        'get_config_api': get_config_api,
        'save_config_api': save_config_api
    }

def build_processing_controls_html(accounts):
    """Build the processing controls HTML interface"""
    
    # Build account dropdown options
    account_options = ""
    if accounts:
        for account in accounts:
            account_options += f'<option value="{account["id"]}">{account["email_address"]} ({account.get("provider", "unknown")})</option>\n'
    else:
        account_options = '<option value="">No accounts configured</option>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real-time Processing Controls - Mail Filter</title>
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
                backdrop-filter: blur(10px);
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
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .control-section {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.08);
                border-top: 4px solid #667eea;
            }}
            
            .section-title {{
                font-size: 1.3em;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .form-group {{ 
                margin: 20px 0; 
            }}
            
            label {{ 
                display: block; 
                margin-bottom: 8px; 
                font-weight: 600;
                color: #34495e;
            }}
            
            select, input {{ 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #e9ecef; 
                border-radius: 8px; 
                font-size: 1em;
                transition: border-color 0.3s ease;
            }}
            
            select:focus, input:focus {{
                border-color: #667eea;
                outline: none;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
                display: inline-block;
                margin: 5px;
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
            
            .mode-selector {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
            }}
            
            .mode-card {{
                padding: 20px;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            
            .mode-card:hover {{
                border-color: #667eea;
                background: #f8f9fa;
            }}
            
            .mode-card.selected {{
                border-color: #667eea;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            
            .mode-title {{
                font-size: 1.2em;
                font-weight: 700;
                margin-bottom: 10px;
            }}
            
            .mode-description {{
                font-size: 0.9em;
                opacity: 0.8;
            }}
            
            .folder-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 10px;
                margin: 15px 0;
            }}
            
            .folder-item {{
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: #f8f9fa;
            }}
            
            .folder-item input[type="checkbox"] {{
                width: auto;
            }}
            
            .results-section {{
                margin-top: 30px;
                display: none;
            }}
            
            .results-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            
            .results-table th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 10px;
                text-align: left;
                border: none;
                font-weight: 600;
            }}
            
            .results-table th:first-child {{ border-top-left-radius: 10px; }}
            .results-table th:last-child {{ border-top-right-radius: 10px; }}
            
            .results-table td {{
                padding: 12px 10px;
                border-bottom: 1px solid #eee;
                vertical-align: top;
            }}
            
            .results-table tbody tr:hover {{
                background: #f8f9fa;
            }}
            
            .flag-btn {{
                padding: 4px 8px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.8em;
                margin: 0 2px;
                transition: all 0.2s ease;
            }}
            
            .flag-btn:hover {{
                transform: translateY(-1px);
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }}
            
            .flag-btn.flag {{
                background: #28a745;
                color: white;
            }}
            
            .flag-btn.unflag {{
                background: #dc3545;
                color: white;
            }}
            
            .flag-btn.flagged {{
                background: #ffc107;
                color: #333;
            }}
            
            .flag-btn:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }}
            
            .protection-indicator {{
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }}
            
            .flag-status {{
                font-size: 0.9em;
                padding: 2px 6px;
                border-radius: 12px;
            }}
            
            .flag-status.protected {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            
            .flag-status.not-protected {{
                background: #f8f9fa;
                color: #6c757d;
                border: 1px solid #dee2e6;
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
                z-index: 1000;
            }}
            
            .confirmation-modal {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 2000;
            }}
            
            .modal-content {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                max-width: 500px;
                width: 90%;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            }}
            
            .modal-title {{
                font-size: 1.5em;
                font-weight: 700;
                color: #dc3545;
                margin-bottom: 15px;
            }}
            
            .modal-text {{
                margin-bottom: 25px;
                line-height: 1.6;
            }}
            
            .modal-buttons {{
                display: flex;
                gap: 15px;
                justify-content: center;
            }}
            
            @media (max-width: 768px) {{
                .mode-selector {{
                    grid-template-columns: 1fr;
                }}
                
                .folder-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .container {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="status-indicator" id="status-indicator">🟢 Processing Controls Ready</div>
        
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>⚙️ Real-time Processing Controls</h1>
            
            <!-- Account Selection -->
            <div class="control-section">
                <div class="section-title">
                    📧 Account Selection
                </div>
                <div class="form-group">
                    <label for="account-select">Select Account:</label>
                    <select id="account-select" onchange="loadAccountFolders()">
                        <option value="">Choose an account...</option>
                        {account_options}
                    </select>
                </div>
            </div>
            
            <!-- Processing Mode Selection -->
            <div class="control-section" id="mode-section" style="display: none;">
                <div class="section-title">
                    🎯 Processing Mode
                </div>
                <div class="mode-selector">
                    <div class="mode-card" data-mode="preview" onclick="selectMode('preview')">
                        <div class="mode-title">🔍 Preview Mode</div>
                        <div class="mode-description">Show what would be deleted without making changes</div>
                    </div>
                    <div class="mode-card" data-mode="live" onclick="selectMode('live')">
                        <div class="mode-title">🚀 Live Processing</div>
                        <div class="mode-description">Actually delete spam emails (requires confirmation)</div>
                    </div>
                </div>
            </div>
            
            <!-- Folder Management -->
            <div class="control-section" id="folder-section" style="display: none;">
                <div class="section-title">
                    📁 Folder Management
                </div>
                <div id="folder-loading" style="text-align: center; padding: 20px;">
                    🔄 Loading folders...
                </div>
                <div id="folder-grid" class="folder-grid" style="display: none;">
                    <!-- Folders will be loaded dynamically -->
                </div>
            </div>
            
            <!-- Configuration Options -->
            <div class="control-section" id="config-section" style="display: none;">
                <div class="section-title">
                    ⚙️ Configuration Options
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                    <label>
                        <input type="checkbox" id="debug-mode"> Enable Debug Mode
                    </label>
                    <label>
                        <input type="checkbox" id="provider-optimizations" checked> Provider Optimizations
                    </label>
                    <label>
                        <input type="checkbox" id="auto-confirm"> Auto-confirm Actions
                    </label>
                </div>
            </div>
            
            <!-- Control Buttons -->
            <div class="control-section" id="control-buttons" style="display: none;">
                <div style="text-align: center;">
                    <button class="btn btn-primary" onclick="runProcessing()" id="run-btn">
                        🔍 Run Preview
                    </button>
                    <button class="btn btn-warning" onclick="saveConfiguration()">
                        💾 Save Configuration
                    </button>
                    <button class="btn btn-secondary" onclick="resetForm()">
                        🔄 Reset
                    </button>
                </div>
            </div>
            
            <!-- Results Section -->
            <div class="control-section results-section" id="results-section">
                <div class="section-title" id="results-title">
                    📊 Processing Results
                </div>
                <div id="results-summary" style="margin-bottom: 20px;">
                    <!-- Summary will be populated dynamically -->
                </div>
                <table class="results-table" id="results-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Folder</th>
                            <th>Action</th>
                            <th>Protection</th>
                            <th>Category</th>
                            <th>Sender</th>
                            <th>Subject</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody id="results-body">
                        <!-- Results will be populated dynamically -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Confirmation Modal for Live Mode -->
        <div class="confirmation-modal" id="confirmation-modal">
            <div class="modal-content">
                <div class="modal-title">⚠️ Live Processing Confirmation</div>
                <div class="modal-text">
                    <p><strong>WARNING:</strong> You are about to run LIVE processing mode.</p>
                    <p>This will <strong>permanently delete</strong> emails classified as spam.</p>
                    <p>Are you absolutely sure you want to proceed?</p>
                </div>
                <div class="modal-buttons">
                    <button class="btn btn-danger" onclick="confirmLiveProcessing()">
                        🗑️ Yes, Delete Emails
                    </button>
                    <button class="btn btn-secondary" onclick="cancelLiveProcessing()">
                        ❌ Cancel
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            let selectedMode = 'preview';
            let selectedAccount = null;
            let availableFolders = [];
            
            function selectMode(mode) {{
                selectedMode = mode;
                
                // Update visual selection
                document.querySelectorAll('.mode-card').forEach(card => {{
                    card.classList.remove('selected');
                }});
                document.querySelector(`[data-mode="${{mode}}"]`).classList.add('selected');
                
                // Update run button
                const runBtn = document.getElementById('run-btn');
                if (mode === 'preview') {{
                    runBtn.textContent = '🔍 Run Preview';
                    runBtn.className = 'btn btn-primary';
                }} else {{
                    runBtn.textContent = '🚀 Run Live Processing';
                    runBtn.className = 'btn btn-danger';
                }}
            }}
            
            async function loadAccountFolders() {{
                const accountSelect = document.getElementById('account-select');
                const accountId = accountSelect.value;
                
                if (!accountId) {{
                    hideAllSections();
                    return;
                }}
                
                selectedAccount = accountId;
                showProcessingSections();
                
                // Load folders
                const folderLoading = document.getElementById('folder-loading');
                const folderGrid = document.getElementById('folder-grid');
                
                folderLoading.style.display = 'block';
                folderGrid.style.display = 'none';
                
                try {{
                    const response = await fetch(`/api/processing/folders/${{accountId}}`);
                    const result = await response.json();
                    
                    if (result.success) {{
                        availableFolders = result.folders;
                        populateFolderGrid(result.folders);
                        folderLoading.style.display = 'none';
                        folderGrid.style.display = 'grid';
                    }} else {{
                        folderLoading.innerHTML = `❌ Error loading folders: ${{result.message}}`;
                    }}
                }} catch (error) {{
                    folderLoading.innerHTML = `❌ Error: ${{error.message}}`;
                }}
            }}
            
            function populateFolderGrid(folders) {{
                const grid = document.getElementById('folder-grid');
                grid.innerHTML = '';
                
                folders.forEach(folder => {{
                    const folderItem = document.createElement('div');
                    folderItem.className = 'folder-item';
                    
                    // Default select INBOX
                    const isInbox = folder.name === 'INBOX';
                    
                    folderItem.innerHTML = `
                        <input type="checkbox" id="folder-${{folder.name}}" ${{isInbox ? 'checked' : ''}} onchange="updateFolderSelection()">
                        <label for="folder-${{folder.name}}">${{folder.name}}</label>
                        <span class="folder-count" id="count-${{folder.name}}">...</span>
                    `;
                    
                    grid.appendChild(folderItem);
                    
                    // Load message count asynchronously
                    loadFolderCount(folder.name);
                }});
            }}
            
            async function loadFolderCount(folderName) {{
                try {{
                    const response = await fetch(`/api/processing/folder-count/${{selectedAccount}}/${{encodeURIComponent(folderName)}}`);
                    const result = await response.json();
                    
                    const countElement = document.getElementById(`count-${{folderName}}`);
                    if (result.success) {{
                        countElement.textContent = `(${{result.message_count}} messages)`;
                    }} else {{
                        countElement.textContent = '(error)';
                    }}
                }} catch (error) {{
                    const countElement = document.getElementById(`count-${{folderName}}`);
                    countElement.textContent = '(error)';
                }}
            }}
            
            function updateFolderSelection() {{
                // This could be used for folder-specific processing later
            }}
            
            function showProcessingSections() {{
                document.getElementById('mode-section').style.display = 'block';
                document.getElementById('folder-section').style.display = 'block';
                document.getElementById('config-section').style.display = 'block';
                document.getElementById('control-buttons').style.display = 'block';
            }}
            
            function hideAllSections() {{
                document.getElementById('mode-section').style.display = 'none';
                document.getElementById('folder-section').style.display = 'none';
                document.getElementById('config-section').style.display = 'none';
                document.getElementById('control-buttons').style.display = 'none';
                document.getElementById('results-section').style.display = 'none';
            }}
            
            async function runProcessing() {{
                if (!selectedAccount) {{
                    alert('Please select an account first');
                    return;
                }}
                
                if (selectedMode === 'live') {{
                    // Show confirmation modal for live mode
                    document.getElementById('confirmation-modal').style.display = 'flex';
                    return;
                }}
                
                // Run preview mode
                await executeProcessing();
            }}
            
            async function confirmLiveProcessing() {{
                document.getElementById('confirmation-modal').style.display = 'none';
                await executeProcessing();
            }}
            
            function cancelLiveProcessing() {{
                document.getElementById('confirmation-modal').style.display = 'none';
                // Reset to preview mode
                selectMode('preview');
            }}
            
            async function executeProcessing() {{
                const runBtn = document.getElementById('run-btn');
                const originalText = runBtn.textContent;
                const statusIndicator = document.getElementById('status-indicator');
                
                runBtn.disabled = true;
                runBtn.textContent = selectedMode === 'preview' ? '🔄 Analyzing...' : '🗑️ Processing...';
                statusIndicator.textContent = selectedMode === 'preview' ? '🔄 Running Preview' : '🗑️ Live Processing';
                statusIndicator.style.background = '#f7971e';
                
                try {{
                    const endpoint = selectedMode === 'preview' ? 
                        `/api/processing/preview/${{selectedAccount}}` : 
                        `/api/processing/live/${{selectedAccount}}`;
                    
                    const requestData = {{}};
                    if (selectedMode === 'live') {{
                        requestData.confirmation_token = 'CONFIRM_LIVE_PROCESSING';
                    }}
                    
                    const response = await fetch(endpoint, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(requestData)
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        displayResults(result);
                        statusIndicator.textContent = selectedMode === 'preview' ? '✅ Preview Complete' : '✅ Processing Complete';
                        statusIndicator.style.background = '#28a745';
                    }} else {{
                        alert(`❌ Processing failed: ${{result.message}}`);
                        statusIndicator.textContent = '❌ Processing Failed';
                        statusIndicator.style.background = '#dc3545';
                    }}
                }} catch (error) {{
                    alert(`❌ Error: ${{error.message}}`);
                    statusIndicator.textContent = '❌ Error';
                    statusIndicator.style.background = '#dc3545';
                }} finally {{
                    runBtn.disabled = false;
                    runBtn.textContent = originalText;
                }}
            }}
            
            function displayResults(result) {{
                // Store results for flagging operations
                currentResults = result;
                
                const resultsSection = document.getElementById('results-section');
                const resultsTitle = document.getElementById('results-title');
                const resultsSummary = document.getElementById('results-summary');
                const resultsBody = document.getElementById('results-body');
                
                // Update title and summary
                if (result.mode === 'preview') {{
                    resultsTitle.textContent = '🔍 Preview Results';
                    resultsSummary.innerHTML = `
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold; color: #28a745;">${{result.total_emails}}</div>
                                <div>Total Emails</div>
                            </div>
                            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold; color: #dc3545;">${{result.would_delete}}</div>
                                <div>Would Delete</div>
                            </div>
                            <div style="background: #d4edda; padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold; color: #155724;">${{result.would_preserve}}</div>
                                <div>Would Preserve</div>
                            </div>
                        </div>
                    `;
                }} else {{
                    resultsTitle.textContent = '🚀 Live Processing Results';
                    resultsSummary.innerHTML = `
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold; color: #28a745;">${{result.total_emails}}</div>
                                <div>Total Processed</div>
                            </div>
                            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold; color: #dc3545;">${{result.actual_deleted}}</div>
                                <div>Deleted</div>
                            </div>
                            <div style="background: #d4edda; padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold; color: #155724;">${{result.actual_preserved}}</div>
                                <div>Preserved</div>
                            </div>
                        </div>
                    `;
                }}
                
                // Populate results table with flagging functionality
                resultsBody.innerHTML = '';
                result.emails.forEach((email, index) => {{
                    const actionColor = email.action.includes('DELETE') ? '#dc3545' : '#28a745';
                    const actionEmoji = email.action.includes('DELETE') ? '🗑️' : '✅';
                    
                    // Create protection column content
                    let protectionContent = '';
                    if (email.uid && email.folder && email.account_id) {{
                        const isFlagged = email.is_flagged || false;
                        const flagStatus = isFlagged ? 
                            '<span class="flag-status protected">🛡️ Protected</span>' :
                            '<span class="flag-status not-protected">No Protection</span>';
                        
                        const flagButton = isFlagged ?
                            `<button class="flag-btn unflag" onclick="toggleEmailFlag('${{email.uid}}', '${{email.folder}}', ${{email.account_id}}, false, ${{index}})">Remove</button>` :
                            `<button class="flag-btn flag" onclick="toggleEmailFlag('${{email.uid}}', '${{email.folder}}', ${{email.account_id}}, true, ${{index}})">Protect</button>`;
                        
                        protectionContent = `
                            <div class="protection-indicator">
                                ${{flagStatus}}
                                ${{flagButton}}
                            </div>
                        `;
                    }} else {{
                        protectionContent = '<span style="color: #888;">N/A</span>';
                    }}
                    
                    const row = `
                        <tr id="email-row-${{index}}">
                            <td>${{email.date}} ${{email.time}}</td>
                            <td>${{email.folder}}</td>
                            <td style="color: ${{actionColor}}; font-weight: bold;">${{actionEmoji}} ${{email.action}}</td>
                            <td id="protection-cell-${{index}}">${{protectionContent}}</td>
                            <td>${{email.category}}</td>
                            <td style="font-family: monospace; font-size: 0.9em;">${{email.sender_email}}</td>
                            <td>${{email.subject}}</td>
                            <td>${{email.confidence}}</td>
                        </tr>
                    `;
                    resultsBody.innerHTML += row;
                }});
                
                resultsSection.style.display = 'block';
                resultsSection.scrollIntoView({{ behavior: 'smooth' }});
            }}
            
            async function saveConfiguration() {{
                if (!selectedAccount) {{
                    alert('Please select an account first');
                    return;
                }}
                
                const config = {{
                    default_mode: selectedMode,
                    debug_mode: document.getElementById('debug-mode').checked,
                    provider_optimizations: document.getElementById('provider-optimizations').checked,
                    auto_confirm: document.getElementById('auto-confirm').checked,
                    enabled_folders: getSelectedFolders()
                }};
                
                try {{
                    const response = await fetch(`/api/processing/config/${{selectedAccount}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(config)
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert('✅ Configuration saved successfully!');
                    }} else {{
                        alert(`❌ Error saving configuration: ${{result.message}}`);
                    }}
                }} catch (error) {{
                    alert(`❌ Error: ${{error.message}}`);
                }}
            }}
            
            function getSelectedFolders() {{
                const selected = [];
                availableFolders.forEach(folder => {{
                    const checkbox = document.getElementById(`folder-${{folder.name}}`);
                    if (checkbox && checkbox.checked) {{
                        selected.push(folder.name);
                    }}
                }});
                return selected;
            }}
            
            function resetForm() {{
                document.getElementById('account-select').value = '';
                selectedAccount = null;
                selectedMode = 'preview';
                hideAllSections();
                document.getElementById('results-section').style.display = 'none';
                
                // Reset mode selection
                document.querySelectorAll('.mode-card').forEach(card => {{
                    card.classList.remove('selected');
                }});
                
                // Reset status
                const statusIndicator = document.getElementById('status-indicator');
                statusIndicator.textContent = '🟢 Processing Controls Ready';
                statusIndicator.style.background = '#28a745';
            }}
            
            // Email flagging functionality
            async function toggleEmailFlag(emailUid, folderName, accountId, shouldFlag, rowIndex) {{
                const protectionCell = document.getElementById(`protection-cell-${{rowIndex}}`);
                const button = protectionCell.querySelector('.flag-btn');
                
                // Disable button during operation
                if (button) {{
                    button.disabled = true;
                    button.textContent = shouldFlag ? 'Protecting...' : 'Removing...';
                }}
                
                try {{
                    const endpoint = shouldFlag ? '/api/emails/flag' : '/api/emails/unflag';
                    const response = await fetch(endpoint, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            email_uid: emailUid,
                            folder_name: folderName,
                            account_id: accountId,
                            sender_email: currentResults?.emails?.[rowIndex]?.sender_email,
                            subject: currentResults?.emails?.[rowIndex]?.subject,
                            flag_reason: shouldFlag ? 'User protected from web interface' : undefined
                        }})
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        // Update UI to reflect new flag status
                        updateProtectionDisplay(protectionCell, !shouldFlag, emailUid, folderName, accountId, rowIndex);
                        
                        // Show success message
                        const statusIndicator = document.getElementById('status-indicator');
                        const originalText = statusIndicator.textContent;
                        const originalColor = statusIndicator.style.background;
                        
                        statusIndicator.textContent = shouldFlag ? '🛡️ Email Protected' : '✅ Protection Removed';
                        statusIndicator.style.background = '#28a745';
                        
                        setTimeout(() => {{
                            statusIndicator.textContent = originalText;
                            statusIndicator.style.background = originalColor;
                        }}, 3000);
                        
                    }} else {{
                        alert(`❌ ${{shouldFlag ? 'Flagging' : 'Unflagging'}} failed: ${{result.message}}`);
                        // Restore button state
                        if (button) {{
                            button.disabled = false;
                            button.textContent = shouldFlag ? 'Protect' : 'Remove';
                        }}
                    }}
                    
                }} catch (error) {{
                    alert(`❌ Error: ${{error.message}}`);
                    // Restore button state
                    if (button) {{
                        button.disabled = false;
                        button.textContent = shouldFlag ? 'Protect' : 'Remove';
                    }}
                }}
            }}
            
            function updateProtectionDisplay(protectionCell, isFlagged, emailUid, folderName, accountId, rowIndex) {{
                const flagStatus = isFlagged ? 
                    '<span class="flag-status protected">🛡️ Protected</span>' :
                    '<span class="flag-status not-protected">No Protection</span>';
                
                const flagButton = isFlagged ?
                    `<button class="flag-btn unflag" onclick="toggleEmailFlag('${{emailUid}}', '${{folderName}}', ${{accountId}}, false, ${{rowIndex}})">Remove</button>` :
                    `<button class="flag-btn flag" onclick="toggleEmailFlag('${{emailUid}}', '${{folderName}}', ${{accountId}}, true, ${{rowIndex}})">Protect</button>`;
                
                protectionCell.innerHTML = `
                    <div class="protection-indicator">
                        ${{flagStatus}}
                        ${{flagButton}}
                    </div>
                `;
            }}
            
            // Store current results for flagging operations
            let currentResults = null;
            
            // Initialize
            selectMode('preview');
        </script>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    # Test the controller
    controller = ProcessingController()
    print("Processing controller initialized successfully")
