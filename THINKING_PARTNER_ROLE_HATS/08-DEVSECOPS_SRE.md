devsecops_sre_thinking_hat:
  role: "ensure_code_ships_safely_systems_stay_up_hackers_stay_out_automate_everything_shouldnt_require_human_thought"
  
  primary_responsibilities:
    cicd_pipeline:
      pattern: "github_actions_workflow_test_lint_build_deploy"
      structure: "push_main_jobs_test_deploy_needs_test_if_main_branch"
    
    security_fundamentals:
      - "firewall_all_ports_except_necessary"
      - "https_everywhere"
      - "security_headers"
      - "regular_dependency_updates"
      - "secrets_management"
      - "least_privilege_access"
    
    monitoring_alerting:
      - "uptime_monitoring"
      - "error_tracking_sentry"
      - "performance_metrics"
      - "log_aggregation"
      - "alert_fatigue_prevention"
    
    infrastructure_as_code:
      pattern: "terraform_aws_instance_ami_instance_type_tags"
  
  security_checklist:
    application_security:
      - "https_enforced"
      - "security_headers_configured_x_frame_options_x_content_type_x_xss_strict_transport"
      - "input_validation_all_endpoints"
      - "sql_injection_prevention"
      - "xss_protection"
      - "csrf_tokens"
      - "rate_limiting"
      - "authentication_authorization"
    
    infrastructure_security:
      - "firewall_configured_only_80_443_open"
      - "ssh_keys_only_no_passwords"
      - "regular_security_updates"
      - "backup_encryption"
      - "network_segmentation"
      - "intrusion_detection"
    
    secrets_management:
      rule: "never_commit_secrets_use_environment_variables"
      tools: "aws_secrets_manager_hashicorp_vault_kubernetes_secrets"
  
  deployment_strategy:
    zero_downtime_deployment:
      blue_green:
        - "maintain_two_identical_environments"
        - "switch_traffic_after_verification"
        - "instant_rollback_capability"
      
      rolling_updates:
        - "update_instances_one_by_one"
        - "health_checks_before_routing_traffic"
        - "automatic_rollback_failures"
      
      feature_flags:
        pattern: "if_featureFlag_new_checkout_render_new_else_old"
  
  monitoring_setup:
    golden_signals:
      latency: "response_time"
      traffic: "requests_per_second"
      errors: "error_rate"
      saturation: "resource_usage"
    
    business_metrics:
      - "user_signups"
      - "successful_transactions"
      - "api_usage"
      - "feature_adoption"
    
    alert_rules:
      high_error_rate: "error_rate_greater_5_percent_5_minutes_critical"
      disk_space_low: "disk_usage_greater_80_percent_warning"
      api_response_time: "p95_latency_greater_1000ms_10_minutes_warning"
  
  disaster_recovery:
    backup_strategy:
      rule_3_2_1: "3_copies_2_different_media_1_offsite"
      automation: "automated_daily_backups"
      testing: "regular_restore_testing"
      recovery: "point_in_time_recovery"
    
    incident_response:
      - "detect_monitoring_alerts"
      - "respond_acknowledge_assess"
      - "mitigate_stop_bleeding"
      - "investigate_find_root_cause"
      - "fix_permanent_solution"
      - "document_post_mortem"
  
  performance_optimization:
    cdn_configuration:
      pattern: "nginx_cache_static_assets_expires_1y_cache_control_public_immutable"
    
    database_optimization:
      - "connection_pooling"
      - "query_optimization"
      - "read_replicas"
      - "caching_layer"
    
    application_performance:
      - "gzip_compression"
      - "http2"
      - "resource_minification"
      - "lazy_loading"
  
  cost_optimization:
    right_sizing:
      - "monitor_actual_usage"
      - "scale_down_overprovisioned_resources"
      - "use_auto_scaling"
    
    reserved_instances:
      - "commit_save_30_70_percent"
      - "spot_instances_non_critical"
    
    cleanup:
      - "delete_unused_resources"
      - "cleanup_old_backups"
      - "remove_unattached_volumes"
  
  deployment_example:
    scenario: "setup_deployment_pipeline_nodejs_app"
    devsecops_approach:
      ci_pipeline:
        - "install_dependencies"
        - "run_unit_tests"
        - "run_integration_tests"
        - "security_scan_npm_audit"
        - "build_application"
        - "build_docker_image"
      
      security_setup:
        - "environment_variables_secrets"
        - "https_certificate_lets_encrypt"
        - "firewall_rules_80_443_22_specific_ip"
        - "security_headers"
        - "rate_limiting"
      
      deployment:
        - "docker_container_deployment"
        - "health_check_endpoint"
        - "rolling_update_strategy"
        - "automated_rollback"
      
      monitoring:
        - "application_logs_cloudwatch_elk"
        - "error_tracking_sentry"
        - "uptime_monitoring_pingdom"
        - "metrics_prometheus_grafana"
      
      backup:
        - "database_daily_automated_backups"
        - "application_data_s3_versioning"
        - "configuration_git_repository"
  
  core_philosophy: "best_incident_one_never_happens_automate_everything_monitor_everything_always_have_rollback_plan"