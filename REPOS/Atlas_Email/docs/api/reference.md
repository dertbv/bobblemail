api_reference:
  title: "Email Project - Complete API Reference"
  framework: "FastAPI with async/await support"
  base_url: "http://localhost:8000"
  base_url_environment: "development"
  content_type: "application/json for API endpoints"
  
  web_pages:
    description: "HTML Responses"
    main_application_pages:
      - method: "GET"
        endpoint: "/"
        description: "Main Dashboard"
        response: "HTML - Email stats, accounts, recent emails"
      - method: "GET"
        endpoint: "/timer"
        description: "Timer Control Interface"
        response: "HTML - Timer configuration and control"
      - method: "GET"
        endpoint: "/analytics"
        description: "Analytics Dashboard"
        response: "HTML - Email processing analytics"
      - method: "GET"
        endpoint: "/validate"
        description: "Email Validation Interface"
        response: "HTML - Validate email classifications"
      - method: "GET"
        endpoint: "/report"
        description: "Reports Page"
        response: "HTML - Processing reports and summaries"
      - method: "GET"
        endpoint: "/accounts"
        description: "Accounts Management"
        response: "HTML - Account configuration interface"
    
    account_specific_pages:
      - method: "GET"
        endpoint: "/single-account/{account_id}"
        parameters:
          - name: "account_id"
            type: "path"
        description: "Detailed view for specific account"
  
  timer_management_apis:
    description: "Timer Configuration & Control"
    endpoints:
      - method: "POST"
        endpoint: "/api/timer/set"
        request_body:
          minutes: "int"
          repeat_mode: "bool"
        response:
          success: "bool"
          message: "str"
        description: "Configure timer settings"
        example_request:
          minutes: 30
          repeat_mode: true
      - method: "POST"
        endpoint: "/api/timer/start"
        request_body: "None"
        response:
          success: "bool"
          message: "str"
        description: "Start configured timer"
      - method: "POST"
        endpoint: "/api/timer/stop"
        request_body: "None"
        response:
          success: "bool"
          message: "str"
        description: "Stop active timer"
  
  batch_processing_apis:
    description: "Email Processing Operations"
    endpoints:
      - method: "POST"
        endpoint: "/api/batch/run"
        description: "Execute batch email processing"
        response: "JSON - Processing results"
  
  user_feedback_apis:
    description: "Feedback Submission & Statistics"
    endpoints:
      - method: "POST"
        endpoint: "/api/feedback"
        request_body_description: "Feedback object"
        response:
          success: "bool"
        description: "Submit classification feedback"
        request_body:
          email_uid: 
            type: "string"
            required: true
          feedback_type:
            type: "string"
            required: true
          original_classification:
            type: "string"
            required: true
          user_classification:
            type: "string"
            required: false
          sender:
            type: "string"
            required: false
          subject:
            type: "string"
            required: false
          confidence_rating:
            type: "number"
            required: false
          user_comments:
            type: "string"
            required: false
          account_email:
            type: "string"
            required: false
          immediate_action:
            type: "boolean"
            required: false
          folder_name:
            type: "string"
            required: false
            default: "INBOX"
      - method: "GET"
        endpoint: "/api/feedback/stats"
        request_body: "None"
        response: "JSON - Statistics"
        description: "Retrieve feedback statistics"
  
  email_flagging_apis:
    protection_deletion_flags:
      - method: "POST"
        endpoint: "/api/emails/flag"
        parameters: "Flag object"
        description: "Flag email for protection"
      - method: "POST"
        endpoint: "/api/emails/unflag"
        parameters: "Unflag object"
        description: "Remove protection flag"
      - method: "POST"
        endpoint: "/api/emails/flag-for-deletion"
        parameters: "Flag object"
        description: "Flag email for deletion"
      - method: "POST"
        endpoint: "/api/emails/bulk-flag"
        parameters: "Bulk flag object"
        description: "Flag multiple emails"
    
    flag_status_retrieval:
      - method: "GET"
        endpoint: "/api/emails/flagged"
        parameters: "None"
        description: "Get protected emails list"
      - method: "GET"
        endpoint: "/api/emails/deletion-flagged"
        parameters: "None"
        description: "Get deletion-flagged emails"
      - method: "GET"
        endpoint: "/api/emails/flag-status/{account_id}/{folder_name}/{email_uid}"
        parameters: "Path params"
        description: "Get basic flag status"
      - method: "GET"
        endpoint: "/api/emails/flag-status-detailed/{account_id}/{folder_name}/{email_uid}"
        parameters: "Path params"
        description: "Get detailed flag status"
    
    flag_email_request_body:
      email_uid:
        type: "string"
        required: true
      folder_name:
        type: "string"
        required: true
      account_id:
        type: "string"
        required: true
      session_id:
        type: "string"
        required: false
      sender_email:
        type: "string"
        required: false
      subject:
        type: "string"
        required: false
      flag_reason:
        type: "string"
        required: false
        default: "User requested protection"
  
  validation_apis:
    description: "Email Classification Validation"
    endpoints:
      - method: "GET"
        endpoint: "/api/validation/emails/{category}"
        parameters:
          - name: "category"
            type: "path"
          - name: "page"
            type: "query"
        description: "Get emails for validation"
        example: "GET /api/validation/emails/spam?page=1"
      - method: "POST"
        endpoint: "/api/validation/feedback"
        parameters: "Feedback object"
        description: "Submit validation feedback"
      - method: "POST"
        endpoint: "/api/validation/save"
        parameters: "Save object"
        description: "Save validation results"
  
  reclassification_apis:
    description: "ML Model Retraining"
    endpoints:
      - method: "POST"
        endpoint: "/api/reclassify-thumbs-down"
        description: "Reclassify thumbs-down emails"
  
  import_management_apis:
    description: "Import Operations"
    endpoints:
      - method: "GET"
        endpoint: "/api/last-import/info"
        description: "Get last import information"
      - method: "POST"
        endpoint: "/api/last-import/remove"
        description: "Remove/undo last import"
  
  account_management_apis:
    account_information_operations:
      - method: "GET"
        endpoint: "/api/accounts"
        parameters: "None"
        description: "Get all accounts (sanitized)"
        response_format:
          accounts:
            - id: "number"
              email_address: "string"
              provider: "string"
              last_used: "timestamp"
              target_folders: ["array"]
              folder_count: "number"
      - method: "POST"
        endpoint: "/api/single-account/{account_id}/preview"
        parameters:
          - name: "account_id"
            type: "path"
        description: "Preview account processing"
      - method: "POST"
        endpoint: "/api/single-account/{account_id}/process"
        parameters:
          - name: "account_id"
            type: "path"
        description: "Execute account processing"
    
    email_retrieval_by_account:
      - method: "GET"
        endpoint: "/api/single-account/{account_id}/emails/{session_id}"
        parameters:
          - name: "account_id"
            type: "path"
          - name: "session_id"
            type: "path"
        description: "Get emails by account/session"
      - method: "GET"
        endpoint: "/api/single-account/{account_id}/all-emails"
        parameters:
          - name: "account_id"
            type: "path"
        description: "Get all emails for account"
      - method: "GET"
        endpoint: "/api/all-accounts/emails"
        parameters: "None"
        description: "Get emails from all accounts"
  
  user_statistics_apis:
    description: "Analytics & Metrics"
    endpoints:
      - method: "GET"
        endpoint: "/api/user-stats"
        description: "Get user activity statistics"
  
  technical_implementation:
    framework_details:
      framework: "FastAPI - Modern async Python web framework"
      database: "SQLite with processed_emails_bulletproof table"
      authentication: "No explicit auth (development setup)"
      cors: "Configured for web interface integration"
    
    request_response_patterns:
      html_endpoints: "Return rendered templates for web interface"
      api_endpoints: "Return JSON responses with consistent error handling"
      error_format:
        error: "Error message"
        details: "Additional info"
      success_format:
        success: true
        message: "Operation completed"
    
    path_parameters:
      account_id: "Account identifier (string/number)"
      folder_name: "Email folder name (string)"
      email_uid: "Email unique identifier (string)"
      category: "Classification category (string)"
      session_id: "Processing session ID (string)"
    
    query_parameters:
      page: 
        type: "integer"
        default: 1
        description: "Pagination page number"
    
    security_considerations:
      data_sanitization: "Account information filtered before API responses"
      input_validation: "Request body validation on all POST endpoints"
      error_handling: "Try/catch blocks prevent system crashes"
      sql_injection_protection: "Using parameterized queries"
  
  usage_examples:
    flag_email_protection:
      description: "Flag Email for Protection"
      command: |
        curl -X POST "http://localhost:8000/api/emails/flag" \
          -H "Content-Type: application/json" \
          -d '{
            "email_uid": "12345",
            "folder_name": "INBOX", 
            "account_id": "1",
            "flag_reason": "Important business email"
          }'
    
    get_account_information:
      description: "Get Account Information"
      command: 'curl -X GET "http://localhost:8000/api/accounts"'
    
    submit_user_feedback:
      description: "Submit User Feedback"
      command: |
        curl -X POST "http://localhost:8000/api/feedback" \
          -H "Content-Type: application/json" \
          -d '{
            "email_uid": "12345",
            "feedback_type": "classification_error",
            "original_classification": "spam",
            "user_classification": "legitimate",
            "confidence_rating": 9
          }'
  
  metadata:
    built_by: "ATLAS & Bobble - Email Security Through Intelligence & Trust"
    last_updated: "2025-06-23"