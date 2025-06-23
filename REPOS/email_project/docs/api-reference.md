# API Reference

## Email Project - Complete API Reference

**Framework**: FastAPI with async/await support  
**Base URL**: `http://localhost:8000` (development)  
**Content-Type**: `application/json` for API endpoints  

---

## 🌐 Web Pages (HTML Responses)

### Main Application Pages

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/` | Main Dashboard | HTML - Email stats, accounts, recent emails |
| `GET` | `/timer` | Timer Control Interface | HTML - Timer configuration and control |
| `GET` | `/analytics` | Analytics Dashboard | HTML - Email processing analytics |
| `GET` | `/validate` | Email Validation Interface | HTML - Validate email classifications |
| `GET` | `/report` | Reports Page | HTML - Processing reports and summaries |
| `GET` | `/accounts` | Accounts Management | HTML - Account configuration interface |

### Account-Specific Pages

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| `GET` | `/single-account/{account_id}` | `account_id` (path) | Detailed view for specific account |

---

## ⏱️ Timer Management APIs

### Timer Configuration & Control

| Method | Endpoint | Request Body | Response | Description |
|--------|----------|--------------|----------|-------------|
| `POST` | `/api/timer/set` | `{"minutes": int, "repeat_mode": bool}` | `{"success": bool, "message": str}` | Configure timer settings |
| `POST` | `/api/timer/start` | None | `{"success": bool, "message": str}` | Start configured timer |
| `POST` | `/api/timer/stop` | None | `{"success": bool, "message": str}` | Stop active timer |

**Example Request - Set Timer:**
```json
{
  "minutes": 30,
  "repeat_mode": true
}
```

---

## 🔄 Batch Processing APIs

### Email Processing Operations

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `POST` | `/api/batch/run` | Execute batch email processing | JSON - Processing results |

---

## 💬 User Feedback APIs

### Feedback Submission & Statistics

| Method | Endpoint | Request Body | Response | Description |
|--------|----------|--------------|----------|-------------|
| `POST` | `/api/feedback` | Feedback object | `{"success": bool}` | Submit classification feedback |
| `GET` | `/api/feedback/stats` | None | JSON - Statistics | Retrieve feedback statistics |

**Feedback Request Body:**
```json
{
  "email_uid": "string (required)",
  "feedback_type": "string (required)", 
  "original_classification": "string (required)",
  "user_classification": "string (optional)",
  "sender": "string (optional)",
  "subject": "string (optional)",
  "confidence_rating": "number (optional)",
  "user_comments": "string (optional)",
  "account_email": "string (optional)",
  "immediate_action": "boolean (optional)",
  "folder_name": "string (optional, default: 'INBOX')"
}
```

---

## 🚩 Email Flagging APIs

### Protection & Deletion Flags

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| `POST` | `/api/emails/flag` | Flag object | Flag email for protection |
| `POST` | `/api/emails/unflag` | Unflag object | Remove protection flag |
| `POST` | `/api/emails/flag-for-deletion` | Flag object | Flag email for deletion |
| `POST` | `/api/emails/bulk-flag` | Bulk flag object | Flag multiple emails |

### Flag Status & Retrieval

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/emails/flagged` | None | Get protected emails list |
| `GET` | `/api/emails/deletion-flagged` | None | Get deletion-flagged emails |
| `GET` | `/api/emails/flag-status/{account_id}/{folder_name}/{email_uid}` | Path params | Get basic flag status |
| `GET` | `/api/emails/flag-status-detailed/{account_id}/{folder_name}/{email_uid}` | Path params | Get detailed flag status |

**Flag Email Request Body:**
```json
{
  "email_uid": "string (required)",
  "folder_name": "string (required)",
  "account_id": "string (required)",
  "session_id": "string (optional)",
  "sender_email": "string (optional)",
  "subject": "string (optional)",
  "flag_reason": "string (optional, default: 'User requested protection')"
}
```

---

## ✅ Validation APIs

### Email Classification Validation

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/validation/emails/{category}` | `category` (path), `page` (query) | Get emails for validation |
| `POST` | `/api/validation/feedback` | Feedback object | Submit validation feedback |
| `POST` | `/api/validation/save` | Save object | Save validation results |

**Example - Get Validation Emails:**
```
GET /api/validation/emails/spam?page=1
```

---

## 🔄 Reclassification APIs

### ML Model Retraining

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reclassify-thumbs-down` | Reclassify thumbs-down emails |

---

## 📥 Import Management APIs

### Import Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/last-import/info` | Get last import information |
| `POST` | `/api/last-import/remove` | Remove/undo last import |

---

## 👥 Account Management APIs

### Account Information & Operations

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/accounts` | None | Get all accounts (sanitized) |
| `POST` | `/api/single-account/{account_id}/preview` | `account_id` (path) | Preview account processing |
| `POST` | `/api/single-account/{account_id}/process` | `account_id` (path) | Execute account processing |

### Email Retrieval by Account

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/single-account/{account_id}/emails/{session_id}` | `account_id`, `session_id` (path) | Get emails by account/session |
| `GET` | `/api/single-account/{account_id}/all-emails` | `account_id` (path) | Get all emails for account |
| `GET` | `/api/all-accounts/emails` | None | Get emails from all accounts |

**Account Response Format:**
```json
{
  "accounts": [
    {
      "id": "number",
      "email_address": "string",
      "provider": "string",
      "last_used": "timestamp",
      "target_folders": ["array"],
      "folder_count": "number"
    }
  ]
}
```

---

## 📊 User Statistics APIs

### Analytics & Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/user-stats` | Get user activity statistics |

---

## 🔧 Technical Implementation Notes

### Framework Details
- **FastAPI**: Modern async Python web framework
- **Database**: SQLite with `processed_emails_bulletproof` table
- **Authentication**: No explicit auth (development setup)
- **CORS**: Configured for web interface integration

### Request/Response Patterns
- **HTML Endpoints**: Return rendered templates for web interface
- **API Endpoints**: Return JSON responses with consistent error handling
- **Error Format**: `{"error": "Error message", "details": "Additional info"}`
- **Success Format**: `{"success": true, "message": "Operation completed"}`

### Path Parameters
- `account_id`: Account identifier (string/number)
- `folder_name`: Email folder name (string)
- `email_uid`: Email unique identifier (string)
- `category`: Classification category (string)
- `session_id`: Processing session ID (string)

### Query Parameters
- `page`: Pagination page number (integer, default: 1)

### Security Considerations
- **Data Sanitization**: Account information filtered before API responses
- **Input Validation**: Request body validation on all POST endpoints
- **Error Handling**: Try/catch blocks prevent system crashes
- **SQL Injection Protection**: Using parameterized queries

---

## 🚀 Usage Examples

### Flag Email for Protection
```bash
curl -X POST "http://localhost:8000/api/emails/flag" \
  -H "Content-Type: application/json" \
  -d '{
    "email_uid": "12345",
    "folder_name": "INBOX", 
    "account_id": "1",
    "flag_reason": "Important business email"
  }'
```

### Get Account Information
```bash
curl -X GET "http://localhost:8000/api/accounts"
```

### Submit User Feedback
```bash
curl -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "email_uid": "12345",
    "feedback_type": "classification_error",
    "original_classification": "spam",
    "user_classification": "legitimate",
    "confidence_rating": 9
  }'
```

---

*Built with love by ATLAS & Bobble - Email Security Through Intelligence & Trust* 💖

*Last Updated: June 23, 2025*