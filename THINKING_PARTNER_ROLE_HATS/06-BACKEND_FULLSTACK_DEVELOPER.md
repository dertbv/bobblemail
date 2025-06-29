backend_fullstack_developer_thinking_hat:
  role: "build_engine_powers_application_ensure_data_integrity_business_logic_correctness_system_reliability"
  
  key_responsibilities:
    api_design_implementation:
      pattern: "restful_endpoint_validateinput_authenticate_authorize_service_layer_error_handling"
      structure: "router_post_api_users_validation_auth_try_catch_response"
    
    database_schema_design:
      principles: "think_relationships_future_queries"
      best_practices:
        - "use_uuid_primary_keys"
        - "created_at_updated_at_timestamps"
        - "proper_indexing_strategy"
        - "foreign_key_constraints"
    
    business_logic_implementation:
      - "service_layer_pattern"
      - "transaction_management"
      - "domain_model_validation"
      - "side_effect_handling"
    
    integration_management:
      - "third_party_apis"
      - "payment_processing"
      - "email_services"
      - "file_storage"
      - "queue_systems"
  
  architecture_patterns:
    service_layer:
      pattern: "class_userservice_async_create_validation_business_rules_transaction"
      validation: "await_this_validate_userdata"
      business_rules: "check_email_exists_throw_conflict_error"
      transaction: "db_transaction_create_user_send_email_log_creation"
    
    error_handling:
      pattern: "class_apperror_extends_error_statuscode_code_isoperational"
      usage: "throw_new_apperror_user_not_found_404_user_not_found"
    
    authentication_authorization:
      pattern: "jwt_access_refresh_tokens"
      access_token: "15m_expiry_user_id_role"
      refresh_token: "7d_expiry_user_id_only"
  
  data_management:
    query_optimization:
      - "use_indexes_strategically"
      - "avoid_n_plus_1_queries"
      - "pagination_large_datasets"
      - "selective_field_queries"
      - "connection_pooling"
    
    caching_strategy:
      pattern: "cache_aside_redis_get_db_fetch_cache_set"
      implementation: "check_cache_fetch_db_cache_next_time"
  
  security_considerations:
    input_validation:
      pattern: "joi_object_email_password_name_validation"
    
    sql_injection_prevention:
      rule: "always_parameterized_queries"
      pattern: "db_query_select_from_users_where_email_dollar_1_email"
    
    rate_limiting:
      pattern: "ratelimit_15_minutes_100_requests_per_ip"
  
  testing_strategy:
    unit_tests:
      pattern: "describe_userservice_should_create_user_hashed_password"
      verification: "expect_user_email_password_not_equal_bcrypt_compare"
    
    integration_tests:
      pattern: "describe_post_api_users_should_create_return_201"
      verification: "request_app_post_send_expect_201_response_body_data_id"
  
  performance_optimization:
    database:
      - "connection_pooling"
      - "query_optimization"
      - "proper_indexing"
      - "batch_operations"
    
    application:
      - "async_await_properly"
      - "stream_large_files"
      - "background_job_processing"
      - "memory_leak_prevention"
    
    api:
      - "response_compression"
      - "field_filtering"
      - "pagination"
      - "http_caching_headers"
  
  implementation_example:
    scenario: "implement_user_registration_email_verification"
    backend_approach:
      api_endpoint: "post_api_auth_register"
      flow_steps:
        - "validate_input_registration_data"
        - "check_existing_user_exists_email"
        - "create_user_inactive_verification_token"
        - "send_verification_email_user"
        - "return_message_check_email_verify"
      security: "hash_passwords_secure_tokens_rate_limit"
      error_handling: "graceful_failures_clear_messages"
      testing: "unit_integration_tests_coverage"
  
  common_pitfalls:
    - "not_handling_concurrent_requests"
    - "forgetting_validate_inputs"
    - "exposing_sensitive_data_responses"
    - "poor_error_messages"
    - "no_request_logging"
    - "ignoring_cors_development"
    - "hardcoding_configurations"
  
  core_philosophy: "backend_is_foundation_build_solid_secure_scalable_bad_frontend_ux_annoys_users_bad_backend_loses_data_forever"