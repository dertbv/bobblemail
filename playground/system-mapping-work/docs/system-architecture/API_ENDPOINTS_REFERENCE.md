# ATLAS EMAIL API ENDPOINTS REFERENCE

## EXECUTIVE SUMMARY

**Atlas_Email** provides a comprehensive **FastAPI-based REST API** with 25+ endpoints for email management, analytics, feedback collection, and system control. The API supports both web interface integration and external system integration with JSON responses and comprehensive error handling.

**API CHARACTERISTICS**:
- **FastAPI Framework**: Modern async Python web framework
- **RESTful Design**: Standard HTTP methods and response codes
- **JSON Responses**: Structured data format for all API responses
- **Error Handling**: Comprehensive exception management
- **Authentication**: Session-based authentication for web interface

## API ARCHITECTURE

### Base Configuration
```python
# FastAPI Application
app = FastAPI(
    title="Atlas Email API",
    description="Production-grade email filtering system API",
    version="1.0.0"
)

# Template Engine
templates = Jinja2Templates(directory="templates")

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Response Format Standards
```python
# Success Response Format
{
    "success": true,
    "data": { ... },
    "message": "Operation completed successfully"
}

# Error Response Format  
{
    "success": false,
    "error": "Error description",
    "details": { ... }
}
```

## WEB INTERFACE ENDPOINTS

### Dashboard and Home
```http
GET /
Content-Type: text/html
Description: Main dashboard with recent email activity and controls
Response: HTML dashboard page with real-time statistics
```

### Analytics Dashboard
```http
GET /analytics
Content-Type: text/html
Description: Comprehensive analytics dashboard with geographic intelligence
Response: Analytics page with charts and geographic data

Data Provided:
- Processing effectiveness (30-day metrics)
- Category breakdown with percentages
- Daily activity charts (14-day history)
- Top spam domains list
- Account performance by provider
- Geographic intelligence with risk scores
- Session statistics
```

### Timer Control Interface
```http
GET /timer
Content-Type: text/html
Description: Automated processing timer management interface
Response: Timer configuration page with current status
```

## TIMER AND BATCH PROCESSING API

### Timer Management
```http
POST /api/timer/set
Content-Type: application/json
Body: {
    "minutes": integer (1-10080),
    "repeat": boolean
}
Response: {
    "success": boolean,
    "message": string,
    "timer_config": {
        "minutes": integer,
        "repeat": boolean,
        "next_run": timestamp
    }
}
Description: Configure automated batch processing timer
```

```http
POST /api/timer/start
Content-Type: application/json
Response: {
    "success": boolean,
    "message": string,
    "status": "RUNNING" | "STOPPED" | "ERROR"
}
Description: Start the automated processing timer
```

```http
POST /api/timer/stop
Content-Type: application/json
Response: {
    "success": boolean, 
    "message": string,
    "status": "STOPPED"
}
Description: Stop the automated processing timer
```

### Batch Processing
```http
POST /api/batch/run
Content-Type: application/json
Body: {
    "account_index": integer (optional),
    "preview_mode": boolean (optional, default: false)
}
Response: {
    "success": boolean,
    "message": string,
    "output": string,
    "processing_stats": {
        "emails_processed": integer,
        "emails_deleted": integer,
        "emails_preserved": integer,
        "duration_seconds": float
    }
}
Description: Execute immediate batch processing for specified account or all accounts
```

## EMAIL MANAGEMENT API

### Email Flagging System
```http
POST /api/emails/flag
Content-Type: application/json
Body: {
    "email_uid": string,
    "folder_name": string,
    "account_id": integer,
    "flag_reason": string (optional)
}
Response: {
    "success": boolean,
    "message": string,
    "flag_id": integer
}
Description: Flag individual email for protection from deletion
```

```http
POST /api/emails/unflag
Content-Type: application/json
Body: {
    "email_uid": string,
    "folder_name": string, 
    "account_id": integer
}
Response: {
    "success": boolean,
    "message": string
}
Description: Remove protection flag from email
```

```http
POST /api/emails/bulk-flag
Content-Type: application/json
Body: {
    "email_uids": array[string],
    "folder_name": string,
    "account_id": integer,
    "flag_reason": string (optional)
}
Response: {
    "success": boolean,
    "message": string,
    "flagged_count": integer,
    "failed_count": integer,
    "details": array[object]
}
Description: Flag multiple emails for protection in bulk operation
```

### Email Status Queries
```http
GET /api/emails/flagged
Content-Type: application/json
Response: {
    "success": boolean,
    "flagged_emails": array[{
        "email_uid": string,
        "folder_name": string,
        "account_id": integer,
        "sender_email": string,
        "subject": string,
        "created_at": timestamp,
        "flag_reason": string
    }]
}
Description: Retrieve all currently flagged emails
```

```http
GET /api/emails/flag-status/{account_id}/{folder_name}/{email_uid}
Content-Type: application/json
Response: {
    "is_flagged": boolean,
    "flag_details": {
        "created_at": timestamp,
        "flag_reason": string,
        "created_by": string
    } | null
}
Description: Check flag status for specific email
```

```http
GET /api/emails/flag-status-detailed/{account_id}/{folder_name}/{email_uid}
Content-Type: application/json  
Response: {
    "success": boolean,
    "is_flagged": boolean,
    "flag_details": object | null,
    "email_exists": boolean,
    "classification_info": {
        "category": string,
        "confidence_score": float,
        "action": string,
        "timestamp": timestamp
    } | null
}
Description: Detailed flag status with classification information
```

### Research Flagging
```http
POST /api/flag-for-research
Content-Type: application/json
Body: {
    "email_uid": string,
    "folder_name": string,
    "account_id": integer,
    "research_reason": string (optional)
}
Response: {
    "success": boolean,
    "message": string
}
Description: Flag email for research and analysis purposes
```

```http
GET /api/emails/deletion-flagged  
Content-Type: application/json
Response: {
    "success": boolean,
    "flagged_emails": array[{
        "email_uid": string,
        "folder_name": string,
        "account_id": integer,
        "sender_email": string,
        "subject": string,
        "flag_type": string,
        "created_at": timestamp
    }]
}
Description: Retrieve emails flagged for deletion
```

## FEEDBACK AND LEARNING API

### User Feedback Collection
```http
POST /api/feedback
Content-Type: application/json
Body: {
    "email_uid": string,
    "session_id": integer (optional),
    "sender": string,
    "subject": string,
    "original_classification": string,
    "user_classification": string (optional),
    "feedback_type": "correct" | "incorrect" | "false_positive",
    "confidence_rating": integer (1-5, optional),
    "user_comments": string (optional)
}
Response: {
    "success": boolean,
    "message": string,
    "feedback_id": integer,
    "ml_training_triggered": boolean
}
Description: Submit user feedback for machine learning improvement
```

### Feedback Statistics
```http
GET /api/feedback/stats
Content-Type: application/json
Response: {
    "total_feedback": integer,
    "feedback_by_type": {
        "correct": integer,
        "incorrect": integer, 
        "false_positive": integer
    },
    "average_confidence": float,
    "recent_feedback_count": integer,
    "accuracy_improvement": float
}
Description: Retrieve feedback statistics and ML performance metrics
```

### User Analytics
```http
GET /api/user-stats
Content-Type: application/json
Response: {
    "total_sessions": integer,
    "emails_processed": integer,
    "feedback_contributions": integer,
    "accuracy_contributions": integer,
    "last_activity": timestamp,
    "engagement_score": float
}
Description: Get user engagement and contribution statistics
```

## GEOGRAPHIC INTELLIGENCE API

### Country Classification Data
```http
GET /api/country-classifications/{country_code}
Content-Type: application/json
Path Parameters:
    country_code: string (2-letter ISO code, e.g., "US", "RU", "CN")
Response: {
    "success": boolean,
    "country_data": {
        "country_code": string,
        "country_name": string,
        "total_emails": integer,
        "spam_emails": integer,
        "spam_percentage": float,
        "risk_score": float,
        "risk_level": "very_low" | "low" | "medium" | "high" | "very_high",
        "top_categories": array[{
            "category": string,
            "count": integer,
            "percentage": float
        }]
    }
}
Description: Retrieve detailed geographic intelligence for specific country
```

## MACHINE LEARNING API

### Email Reclassification
```http
POST /api/reclassify-thumbs-down
Content-Type: application/json
Response: {
    "success": boolean,
    "summary": {
        "total_processed": integer,
        "reclassified": integer,
        "category_breakdown": {
            "category_name": count,
            ...
        },
        "message": string
    }
}
Description: Reclassify all emails marked with negative feedback using current ML models
```

## ERROR HANDLING AND STATUS CODES

### Standard HTTP Status Codes
- **200 OK**: Successful operation
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error

### API Error Response Format
```json
{
    "success": false,
    "error": "Error category",
    "message": "Detailed error description",
    "details": {
        "field_errors": {},
        "validation_errors": [],
        "system_info": {}
    },
    "timestamp": "2025-07-03T10:30:00Z"
}
```

### Common Error Types
- **ValidationError**: Invalid input parameters
- **DatabaseError**: Database operation failures
- **ProcessingError**: Email processing failures
- **AuthenticationError**: Authentication/authorization issues
- **SystemError**: Internal system failures

## PERFORMANCE CHARACTERISTICS

### Response Times
- **Simple Queries**: < 50ms average
- **Analytics Endpoints**: < 200ms average
- **Batch Processing**: Variable (depends on email volume)
- **ML Operations**: < 500ms average

### Rate Limiting
- **Web Interface**: No explicit limits (session-based)
- **API Endpoints**: 1000 requests/hour per session
- **Batch Operations**: Limited to prevent system overload

### Caching Strategy
- **Analytics Data**: 5-minute cache for dashboard
- **Geographic Data**: 1-hour cache for country classifications
- **User Statistics**: 15-minute cache for stats endpoints

## INTEGRATION EXAMPLES

### JavaScript Frontend Integration
```javascript
// Batch processing trigger
async function runBatchProcessing() {
    const response = await fetch('/api/batch/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preview_mode: false })
    });
    
    const result = await response.json();
    console.log('Batch result:', result);
}

// User feedback submission
async function submitFeedback(emailData, feedbackType) {
    const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email_uid: emailData.uid,
            sender: emailData.sender,
            subject: emailData.subject,
            original_classification: emailData.category,
            feedback_type: feedbackType
        })
    });
    
    return await response.json();
}
```

### Python Client Integration
```python
import requests

class AtlasEmailClient:
    def __init__(self, base_url):
        self.base_url = base_url
        
    def get_analytics_data(self):
        response = requests.get(f"{self.base_url}/analytics")
        return response.json()
    
    def submit_feedback(self, email_uid, feedback_type):
        payload = {
            "email_uid": email_uid,
            "feedback_type": feedback_type
        }
        response = requests.post(f"{self.base_url}/api/feedback", json=payload)
        return response.json()
    
    def run_batch_processing(self, preview_mode=False):
        payload = {"preview_mode": preview_mode}
        response = requests.post(f"{self.base_url}/api/batch/run", json=payload)
        return response.json()
```

This API provides comprehensive access to all Atlas_Email functionality with consistent interfaces, proper error handling, and production-ready performance characteristics.

---
*API Endpoints Reference - Version 1.0*  
*Generated: 2025-07-03*  
*Status: Production Ready*