#!/usr/bin/env python3
"""
Train All ML Models for Atlas Email System
==========================================

This script trains all the ML models in the correct order:
1. Four Category Classifier (for A/B testing)
2. Naive Bayes (for ensemble)
3. Random Forest (for ensemble)
4. Category Classifier (for detailed categorization)
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to Python path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / "src"))

def run_training(script_name, description):
    """Run a training script with proper error handling."""
    print(f"\n{'=' * 60}")
    print(f"🎯 {description}")
    print(f"{'=' * 60}\n")
    
    cmd = [
        sys.executable,
        str(REPO_ROOT / "src" / "atlas_email" / "ml" / script_name)
    ]
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(REPO_ROOT / "src")
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Warnings: {result.stderr}")
        if result.returncode != 0:
            print(f"❌ Training failed with exit code: {result.returncode}")
            return False
        print(f"✅ {description} completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    """Train all models in the correct order."""
    print("🚀 Atlas Email ML Model Training Suite")
    print("=" * 60)
    
    # Ensure models directory exists
    models_dir = REPO_ROOT / "data" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Models directory: {models_dir}")
    
    # Training pipeline
    trainings = [
        ("four_category_classifier.py", "Training 4-Category Classifier"),
        ("naive_bayes.py", "Training Naive Bayes Classifier"),
        ("random_forest.py", "Training Random Forest Classifier"),
        # Category classifier has issues, skip for now
        # ("category_classifier.py", "Training Multi-Category Classifier"),
    ]
    
    results = []
    for script, description in trainings:
        success = run_training(script, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Training Summary:")
    print("=" * 60)
    for description, success in results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"{description}: {status}")
    
    # Next steps
    print("\n📋 Next Steps:")
    print("1. Enable A/B testing in settings to use the 4-category classifier")
    print("2. Monitor classification accuracy and adjust as needed")
    print("3. The ensemble classifier will use Naive Bayes + Random Forest")
    print("4. Check webapp.log for any runtime issues")

if __name__ == "__main__":
    main()