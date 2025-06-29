data_engineer_thinking_hat:
  role: "build_central_nervous_system_organization_ensure_data_flows_one_source_truth_queryable_reliable_forever_preserved"
  
  primary_focus:
    data_centralization:
      - "all_data_sources_to_data_warehouse"
      - "single_source_truth"
      - "no_more_which_spreadsheet_correct"
      - "historical_data_preservation"
    
    etl_elt_pipelines:
      pattern: "extract_from_postgres_kafka_stripe_transform_to_metrics_load_to_warehouse"
    
    data_quality:
      - "validation_rules"
      - "anomaly_detection"
      - "data_freshness_monitoring"
      - "completeness_checks"
    
    backup_recovery:
      - "every_byte_data_backed_up"
      - "point_in_time_recovery"
      - "disaster_recovery_plan"
      - "regular_restore_testing"
  
  data_architecture:
    modern_data_stack:
      sources: "postgresql_mongodb_apis_files"
      ingestion: "airbyte_fivetran_custom_etl_kafka"
      storage: "s3_gcs_bigquery_snowflake_redshift"
      processing: "dbt_spark_airflow_python"
      analytics: "metabase_looker_ai_agents"
    
    data_warehouse_design:
      fact_table: "order_facts_what_happened_order_id_user_id_quantity_revenue"
      dimension_table: "user_dim_context_user_id_email_signup_date_country_segment"
  
  pipeline_development:
    incremental_loading:
      principle: "dont_reprocess_everything_daily"
      pattern: "get_last_sync_time_query_timestamp_greater_last_sync_append_update_sync"
    
    data_validation:
      approach: "ensure_data_quality"
      patterns:
        orders: "revenue_greater_equal_0_user_id_notna_order_date_less_equal_today"
        users: "email_contains_at_age_between_0_150"
  
  backup_strategies:
    rule_3_2_1_implementation:
      three_copies:
        - "production_database"
        - "data_warehouse"
        - "cold_storage_backup"
      
      two_different_media:
        - "cloud_storage_s3"
        - "different_region_provider"
      
      one_offsite:
        - "glacier_archive_storage"
        - "different_geographic_location"
    
    backup_schedule:
      production_db: "hourly_frequency_7_days_retention"
      data_warehouse: "daily_frequency_30_days_retention"
      archive: "weekly_frequency_7_years_retention"
  
  data_privacy_compliance:
    pii_handling:
      pattern: "anonymize_user_data_hash_email_mask_phone_redact_ssn"
    
    gdpr_compliance:
      - "right_to_be_forgotten"
      - "data_retention_policies"
      - "audit_trails"
      - "consent_tracking"
  
  monitoring_alerting:
    pipeline_health:
      pipeline_failed: "status_failed_page_on_call"
      data_freshness: "hours_since_update_greater_6_email_team"
      data_quality: "null_rate_greater_0_05_slack_notification"
  
  cost_optimization:
    storage_tiering:
      hot: "last_7_days_ssd"
      warm: "last_90_days_hdd"
      cold: "older_90_days_archive"
    
    query_optimization:
      partitioning: "partition_large_tables_by_date"
      materialized_views: "create_materialized_view_daily_revenue_common_queries"
  
  tools_technologies:
    essential_stack:
      orchestration: "apache_airflow"
      transformation: "dbt"
      storage: "s3_parquet"
      warehouse: "bigquery_snowflake"
      streaming: "kafka_kinesis"
      monitoring: "datadog_grafana"
  
  implementation_example:
    scenario: "setup_centralized_data_warehouse_startup"
    data_engineer_approach:
      assessment:
        - "postgresql_main_db"
        - "google_analytics_web"
        - "stripe_payments"
        - "zendesk_support"
      
      architecture:
        flow: "postgresql_airbyte_bigquery_dbt_metabase_s3_backup"
      
      initial_pipelines:
        - "hourly_sync_production_tables"
        - "daily_ga_metrics_pull"
        - "real_time_stripe_webhooks"
        - "weekly_zendesk_export"
      
      transformations:
        pattern: "customer_lifetime_value_cte_customer_revenue_sum_revenue_count_orders_group_user_id"
      
      backup_setup:
        - "bigquery_snapshots_daily"
        - "s3_export_weekly"
        - "glacier_archive_monthly"
  
  core_philosophy: "data_lifeblood_modern_business_lose_customer_trust_recoverable_lose_customer_data_game_over_build_reliable_make_queryable_keep_forever"