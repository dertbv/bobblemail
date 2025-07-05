#!/usr/bin/env python3
"""Debug why AB classifier is failing"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from atlas_email.ml.ab_classifier_integration import ABClassifierIntegration
    print("✅ AB classifier imported successfully")
    
    # Try to initialize it
    ab_classifier = ABClassifierIntegration()
    print("✅ AB classifier initialized")
    
    # Test classification
    test_cases = [
        ("Trump Infrastructure <noreply@trumpboom.com>", "Trump's infrastructure boom"),
        ("Laser News <alerts@laserstrike.net>", "[Horrifying Laser Strike]"),
        ("peacock® <ohyzvtkdwpc@xgsrksd>", "Payment-Declined-Order")
    ]
    
    for sender, subject in test_cases:
        try:
            # Extract domain from sender
            domain = None
            if '<' in sender and '>' in sender:
                email_part = sender.split('<')[1].split('>')[0]
                if '@' in email_part:
                    domain = email_part.split('@')[1]
            elif '@' in sender:
                domain = sender.split('@')[1]
                
            result = ab_classifier.classify_with_ab_testing(
                sender=sender,
                subject=subject,
                domain=domain,
                headers=""
            )
            print(f"\n📧 {subject[:30]}...")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"\n❌ Failed to classify: {subject[:30]}...")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"❌ Failed to import/initialize AB classifier: {e}")
    import traceback
    traceback.print_exc()