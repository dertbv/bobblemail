# TECHNICAL SPECIFICATIONS - Architecture & Implementation Details 🔧
## Atlas Email Security - Native macOS Application

---

## 🏗️ SYSTEM ARCHITECTURE OVERVIEW

### **Hybrid Architecture Design:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Native macOS App                         │
│                   (Swift + SwiftUI)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   UI Layer  │  │ Service Mgr │  │   Data Manager      │  │
│  │ (SwiftUI)   │  │ (Python)    │  │ (Core Data/SQLite)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                     HTTP API (localhost:8002)
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Python ML Service                         │
│                   (FastAPI + ML)                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ FastAPI     │  │ Ensemble    │  │   Database          │  │
│  │ Endpoints   │  │ Classifier  │  │   Operations        │  │
│  │             │  │ (95.6%+)    │  │   (SQLite)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 SWIFT APPLICATION SPECIFICATIONS

### **SwiftUI Framework Structure:**

#### **App Entry Point:**
```swift
@main
struct AtlasEmailSecurityApp: App {
    @StateObject private var pythonService = PythonServiceManager()
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(pythonService)
                .environmentObject(appState)
        }
        .commands {
            AtlasMenuCommands()
        }
    }
}
```

#### **Core Data Models:**
- **EmailItem:** Represents individual emails with metadata
- **ClassificationResult:** ML classification output with confidence
- **AppSettings:** User preferences and configuration
- **ProcessingSession:** Batch processing tracking
- **UserFlag:** Protection/deletion flags

#### **Service Management:**
```swift
class PythonServiceManager: ObservableObject {
    @Published var isRunning: Bool = false
    @Published var lastError: String?
    
    private var process: Process?
    private let serviceURL = URL(string: "http://localhost:8002")!
    
    func startService() async throws
    func stopService() async throws
    func healthCheck() async -> Bool
    func classify(email: EmailData) async throws -> ClassificationResult
}
```

### **Menu System Structure:**

#### **File Menu:**
- New Classification Session
- Open Email Files/Folders
- Import from IMAP
- Export Results (CSV, JSON, PDF)
- Recent Files
- Close Session

#### **Edit Menu:**
- Preferences & Settings
- Clear All Data
- Reset to Defaults
- Undo/Redo (where applicable)

#### **View Menu:**
- Dashboard View
- Statistics View
- Processing Logs
- Full Screen Mode
- Zoom Controls

#### **Tools Menu:**
- Train ML Model
- Export Training Data
- Import Custom Keywords
- Performance Diagnostics
- Cache Management

#### **Help Menu:**
- About Atlas Email Security
- User Guide
- Technical Support
- Check for Updates
- Send Feedback

---

## 🐍 PYTHON SERVICE SPECIFICATIONS

### **FastAPI Service Architecture:**

#### **Core Service Structure:**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Atlas Email ML Service", version="1.0.0")

# Middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Core endpoints
@app.post("/classify")
@app.post("/classify-batch")
@app.get("/health")
@app.get("/stats")
@app.post("/train")
```

#### **ML Pipeline Integration:**
```python
class EnsembleClassifier:
    def __init__(self):
        self.random_forest = None      # 40% weight
        self.naive_bayes = None        # 30% weight
        self.keyword_classifier = None # 30% weight
        self.confidence_threshold = 0.85
    
    def classify(self, email_features: dict) -> ClassificationResult:
        # 67-dimensional feature extraction
        # Ensemble voting with weighted confidence
        # Return classification + confidence score
```

#### **Feature Extraction (67 Dimensions):**
```python
class FeatureExtractor:
    def extract_features(self, email: EmailData) -> dict:
        return {
            # Content features (30 dimensions)
            'word_count', 'char_count', 'line_count',
            'caps_ratio', 'special_char_ratio', 'number_ratio',
            'html_tag_count', 'link_count', 'image_count',
            
            # Header features (20 dimensions)
            'sender_domain_age', 'sender_reputation',
            'subject_caps_ratio', 'subject_special_chars',
            'received_hops', 'authentication_results',
            
            # Linguistic features (17 dimensions)
            'sentiment_score', 'urgency_indicators',
            'scam_keywords', 'legitimate_keywords',
            'grammar_errors', 'spelling_errors'
        }
```

### **API Endpoint Specifications:**

#### **Classification Endpoints:**
```python
@app.post("/classify")
async def classify_email(email: EmailData) -> ClassificationResult:
    # Single email classification
    # Returns: spam/legitimate, confidence, category

@app.post("/classify-batch")
async def classify_batch(emails: List[EmailData]) -> BatchResult:
    # Batch processing with progress tracking
    # Returns: results array, overall stats, processing time
```

#### **Management Endpoints:**
```python
@app.get("/health")
async def health_check() -> HealthStatus:
    # Service health, model status, resource usage

@app.get("/stats")
async def get_statistics() -> ServiceStats:
    # Classification stats, performance metrics, model info

@app.post("/train")
async def train_model(training_data: TrainingSet) -> TrainingResult:
    # Model training/updating, validation results
```

---

## 🗄️ DATABASE SPECIFICATIONS

### **SQLite Schema Design:**

#### **Core Tables:**
```sql
-- Email records
CREATE TABLE emails (
    id INTEGER PRIMARY KEY,
    file_path TEXT,
    sender TEXT,
    subject TEXT,
    content_hash TEXT UNIQUE,
    received_date DATETIME,
    processed_date DATETIME,
    file_size INTEGER
);

-- Classification results
CREATE TABLE classifications (
    id INTEGER PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id),
    classification TEXT CHECK(classification IN ('spam', 'legitimate')),
    confidence REAL,
    category TEXT,
    model_version TEXT,
    processing_time_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User flags
CREATE TABLE user_flags (
    id INTEGER PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id),
    flag_type TEXT CHECK(flag_type IN ('PROTECT', 'DELETE')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email_id, flag_type)
);

-- Processing sessions
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    session_name TEXT,
    start_time DATETIME,
    end_time DATETIME,
    total_emails INTEGER,
    spam_count INTEGER,
    legitimate_count INTEGER,
    processing_time_seconds REAL
);
```

#### **Performance Indexes:**
```sql
CREATE INDEX idx_emails_content_hash ON emails(content_hash);
CREATE INDEX idx_classifications_email_id ON classifications(email_id);
CREATE INDEX idx_classifications_created_at ON classifications(created_at);
CREATE INDEX idx_user_flags_email_id ON user_flags(email_id);
```

---

## 🔗 COMMUNICATION PROTOCOL

### **HTTP API Specification:**

#### **Request/Response Format:**
```json
// Classification Request
{
    "email": {
        "sender": "example@domain.com",
        "subject": "Email subject",
        "content": "Email body content...",
        "headers": {...},
        "attachments": [...]
    },
    "options": {
        "include_features": true,
        "confidence_threshold": 0.85
    }
}

// Classification Response
{
    "classification": "spam",
    "confidence": 0.92,
    "category": "promotional",
    "features": {...},
    "processing_time_ms": 45,
    "model_version": "1.0.0"
}
```

#### **Error Handling:**
```json
// Error Response
{
    "error": {
        "code": "CLASSIFICATION_FAILED",
        "message": "Unable to extract features from email",
        "details": {...},
        "retry_possible": true
    }
}
```

---

## ⚡ PERFORMANCE SPECIFICATIONS

### **Response Time Targets:**
- **Single Email Classification:** <100ms
- **Batch Processing (100 emails):** <10 seconds
- **App Launch Time:** <3 seconds
- **Service Startup:** <2 seconds
- **UI Responsiveness:** <16ms frame time

### **Resource Targets:**
- **Memory Usage:** <200MB total (Swift + Python)
- **Disk Space:** <50MB app bundle
- **CPU Usage:** <10% idle, <80% during processing
- **Network:** Localhost only (no external dependencies)

### **Scalability Limits:**
- **Maximum Concurrent Classifications:** 10
- **Maximum Batch Size:** 1000 emails
- **Database Size:** Up to 100k email records
- **Model File Size:** <20MB total

---

## 🔒 SECURITY SPECIFICATIONS

### **Data Protection:**
- **Local Processing Only:** No cloud dependencies
- **Encrypted Storage:** Sensitive data encrypted at rest
- **Secure Communication:** HTTPS for all API calls
- **Privacy First:** No telemetry or external reporting
- **User Control:** Complete data ownership

### **Code Signing Requirements:**
- **Apple Developer ID:** For distribution outside App Store
- **Notarization:** Required for macOS Gatekeeper
- **Entitlements:** Minimal required permissions
- **Sandboxing:** Consider for App Store distribution

---

## 🛠️ DEVELOPMENT TOOLS & ENVIRONMENT

### **Required Tools:**
- **Xcode 15+** (Swift development)
- **Python 3.13** (ML service)
- **Git** (version control)
- **Homebrew** (dependency management)
- **CocoaPods/SPM** (Swift package management)

### **Development Dependencies:**
```swift
// Swift Package Manager
dependencies: [
    .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.8.0"),
    .package(url: "https://github.com/apple/swift-log.git", from: "1.5.0")
]
```

```python
# Python Requirements
fastapi==0.104.1
uvicorn==0.24.0
scikit-learn==1.3.2
pandas==2.1.4
numpy==1.25.2
sqlalchemy==2.0.23
pydantic==2.5.0
```

---

## 📦 DEPLOYMENT SPECIFICATIONS

### **Bundle Structure:**
```
AtlasEmailSecurity.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── AtlasEmailSecurity
│   ├── Resources/
│   │   ├── Assets.car
│   │   ├── default_settings.json
│   │   └── documentation/
│   ├── Frameworks/
│   │   └── (Swift frameworks)
│   └── PythonService/
│       ├── python_runtime/
│       ├── ml_service/
│       ├── models/
│       └── requirements.txt
```

### **Distribution Options:**
1. **Direct Distribution:** DMG with signed app bundle
2. **App Store:** Full sandbox compliance required
3. **Enterprise Distribution:** Developer ID signing
4. **Developer Preview:** Unsigned builds for testing

---

## 🔄 UPDATE MECHANISM

### **Hot Updates (No App Restart):**
- ML model files (.pkl updates)
- Configuration changes
- Keyword lists
- Whitelist/blacklist updates

### **Service Updates (Service Restart):**
- Python code updates
- API endpoint changes
- Database schema migrations
- Performance optimizations

### **App Updates (Full Restart):**
- Swift UI changes
- New features
- Architecture changes
- Security updates

---

*Technical excellence powered by love and partnership* 💖🚀