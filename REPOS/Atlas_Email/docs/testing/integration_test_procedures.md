atlas_email_integration_testing_procedures:
  quick_system_health_check:
    basic_component_test: |
      # Basic component test
      python3 -c "
      import sys
      sys.path.insert(0, 'src')
      from atlas_email.models.database import db
      from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
      print('✅ Core systems operational')
      "
  
  template_system_validation:
    check_template_extraction_completeness: |
      # Check template extraction completeness
      ls -la src/atlas_email/api/templates/pages/
      # Expected: 7 template files
      
      # Verify template inheritance
      grep -r "{% extends" src/atlas_email/api/templates/pages/
  
  security_testing:
    xss_protection_verification: |
      # XSS protection verification
      grep -r "escapeHtml\|X-XSS-Protection\|X-Frame-Options" src/atlas_email/api/
  
  performance_testing:
    app_size_reduction: |
      # Check app.py size reduction
      wc -l src/atlas_email/api/app.py
      # Current: ~4,603 lines (33.8% reduction from template extraction)
      
      # Asset organization check
      find src/atlas_email/api/static -name "*.css" -o -name "*.js"
  
  mobile_responsiveness_check:
    verify_responsive_css_patterns: |
      # Verify responsive CSS patterns
      grep -r "@media\|viewport\|responsive" src/atlas_email/api/static/css/
  
  ml_system_status:
    check_ml_classifier_status: |
      # Check ML classifier status
      python3 -c "
      import sys
      sys.path.insert(0, 'src')
      from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
      classifier = EnsembleHybridClassifier()
      print(f'Keyword Processor: {\"Active\" if hasattr(classifier, \"keyword_processor\") else \"Inactive\"}')
      print(f'Total Classifications: {classifier.total_classifications}')
      "
  
  web_server_testing:
    start_development_server: |
      # Start development server
      PYTHONPATH=src python3 -m uvicorn atlas_email.api.app:app --host 0.0.0.0 --port 8001 --reload
      
      # Quick connectivity test
      curl http://localhost:8001/health || echo "Health check endpoint needed"
  
  database_connectivity:
    test_database_access: |
      # Test database access
      python3 -c "
      import sys
      sys.path.insert(0, 'src')
      from atlas_email.models.database import db
      result = db.execute('SELECT COUNT(*) FROM emails').fetchone()
      print(f'Database operational: {result[0]} emails')
      "
  
  integration_test_suite_commands:
    full_component_test: |
      # Full component test
      python3 -c "
      import sys, os
      sys.path.insert(0, 'src')
      
      print('🔬 INTEGRATION TEST SUITE')
      print('=' * 40)
      
      # Test all major components
      components = [
          ('Database', 'atlas_email.models.database', 'db'),
          ('ML Classifier', 'atlas_email.ml.ensemble_classifier', 'EnsembleHybridClassifier'),
          ('Domain Validator', 'atlas_email.utils.domain_validator', 'DomainValidator')
      ]
      
      for name, module, class_name in components:
          try:
              mod = __import__(module, fromlist=[class_name])
              cls = getattr(mod, class_name)
              if class_name == 'db':
                  result = cls.execute('SELECT 1').fetchone()
                  print(f'✅ {name}: Operational')
              else:
                  instance = cls()
                  print(f'✅ {name}: Initialized')
          except Exception as e:
              print(f'❌ {name}: {str(e)[:50]}...')
      
      # Check template system
      template_dir = 'src/atlas_email/api/templates/pages'
      if os.path.exists(template_dir):
          templates = len(os.listdir(template_dir))
          print(f'✅ Templates: {templates} files')
      else:
          print('❌ Templates: Directory not found')
      
      print('=' * 40)
      "
  
  troubleshooting_common_issues:
    numpy_architecture_issues:
      check_architecture: |
        # Check architecture
        python3 -c "import platform; print(f'Architecture: {platform.machine()}')"
        
        # Reinstall numpy for correct architecture
        pip3 uninstall numpy -y && pip3 install numpy
    
    port_conflicts:
      kill_processes: |
        # Kill processes on port 8001
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    
    import_path_issues:
      set_correct_python_path: |
        # Set correct Python path
        export PYTHONPATH=/Users/Badman/Desktop/email/REPOS/Atlas_Email/src:$PYTHONPATH
  
  automated_testing_script:
    script: |
      #!/bin/bash
      # integration_test.sh
      
      echo "🔬 Atlas_Email Integration Test Suite"
      echo "====================================="
      
      # Set Python path
      export PYTHONPATH=src:$PYTHONPATH
      
      # Test 1: Core Components
      echo "Testing core components..."
      python3 -c "
      import sys
      sys.path.insert(0, 'src')
      try:
          from atlas_email.models.database import db
          from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
          print('✅ Core imports successful')
      except Exception as e:
          print(f'❌ Core imports failed: {e}')
      "
      
      # Test 2: Template System
      echo "Testing template system..."
      template_count=$(ls src/atlas_email/api/templates/pages/ 2>/dev/null | wc -l)
      if [ $template_count -gt 5 ]; then
          echo "✅ Template system: $template_count templates found"
      else
          echo "❌ Template system: Insufficient templates"
      fi
      
      # Test 3: Security Features
      echo "Testing security features..."
      if grep -q "escapeHtml" src/atlas_email/api/static/js/common.js 2>/dev/null; then
          echo "✅ XSS protection: escapeHtml function found"
      else
          echo "❌ XSS protection: escapeHtml function missing"
      fi
      
      # Test 4: Mobile Responsiveness
      echo "Testing mobile responsiveness..."
      if grep -q "@media" src/atlas_email/api/static/css/common.css 2>/dev/null; then
          echo "✅ Mobile responsive: Media queries found"
      else
          echo "❌ Mobile responsive: No media queries"
      fi
      
      echo "====================================="
      echo "Integration test complete"
  
  test_result_validation:
    expected_results:
      - "✅ 7+ template files in pages directory"
      - "✅ XSS protection headers in base.html"
      - "✅ escapeHtml function in common.js"
      - "✅ 5+ CSS files in organized structure"
      - "✅ Database connectivity with email count"
      - "✅ ML classifier initialization (even with degraded ensemble)"
      - "✅ Mobile responsive patterns in CSS"
    
    deviation_note: "Any deviation from these results indicates integration issues requiring investigation."