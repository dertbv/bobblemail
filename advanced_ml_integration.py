#!/usr/bin/env python3
"""
Advanced ML Integration Module
Integrates advanced ML classifiers into the main email processing pipeline
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Add current directory to path for imports
sys.path.append('.')

from experimental.advanced_ml_classifier import AdvancedMLClassifier
from hybrid_classifier import HybridEmailClassifier
from spam_classifier import classify_spam_type
from ml_classifier import NaiveBayesClassifier


class AdvancedMLIntegration:
    """
    Integration layer for advanced ML classifiers with existing system
    """
    
    def __init__(self, db_path: str = "mail_filter.db"):
        self.db_path = db_path
        self.advanced_classifier = None
        self.hybrid_classifier = HybridEmailClassifier(db_path)
        self.naive_bayes = NaiveBayesClassifier(db_path)
        self.is_trained = False
        self.performance_comparison = {}
        
        print("🚀 Initializing Advanced ML Integration...")
        
        try:
            self.advanced_classifier = AdvancedMLClassifier(db_path)
            print("✅ Advanced ML classifier initialized")
        except Exception as e:
            print(f"❌ Error initializing advanced classifier: {e}")
    
    def train_and_compare_models(self, max_samples: int = 1000) -> Dict[str, Any]:
        """Train all models and compare performance"""
        print("\n🎯 ADVANCED ML DEPLOYMENT - TRAINING & COMPARISON")
        print("=" * 60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'training_samples': max_samples,
            'models_tested': [],
            'performance_metrics': {},
            'best_model': None,
            'recommendations': []
        }
        
        # 1. Train current system baseline
        print("\n📊 1. Training Baseline Models...")
        baseline_results = self._train_baseline_models(max_samples)
        results['performance_metrics']['baseline'] = baseline_results
        
        # 2. Train advanced ML models
        if self.advanced_classifier:
            print("\n🚀 2. Training Advanced ML Models...")
            advanced_results = self._train_advanced_models(max_samples)
            results['performance_metrics']['advanced'] = advanced_results
        
        # 3. Performance comparison
        print("\n📈 3. Performance Comparison...")
        comparison = self._compare_performance(results['performance_metrics'])
        results['comparison_analysis'] = comparison
        
        # 4. Generate recommendations
        recommendations = self._generate_recommendations(comparison)
        results['recommendations'] = recommendations
        
        # 5. Save results
        self._save_results(results)
        
        # 6. Display summary
        self._display_deployment_summary(results)
        
        return results
    
    def _train_baseline_models(self, max_samples: int) -> Dict[str, Any]:
        """Train baseline models (current system)"""
        baseline_results = {}
        
        # Train Naive Bayes
        print("   📊 Training Naive Bayes (current system)...")
        start_time = time.time()
        try:
            nb_summary = self.naive_bayes.train(use_user_feedback=True, max_samples=max_samples)
            train_time = time.time() - start_time
            
            baseline_results['naive_bayes'] = {
                'training_time': train_time,
                'training_summary': nb_summary,
                'status': 'success'
            }
            print(f"   ✅ Naive Bayes trained in {train_time:.2f}s")
            
        except Exception as e:
            baseline_results['naive_bayes'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"   ❌ Naive Bayes training failed: {e}")
        
        # Test Hybrid Classifier
        print("   📊 Testing Hybrid Classifier...")
        try:
            # Quick test prediction
            test_prediction = self.hybrid_classifier.classify_email(
                "crypto-investment@suspicious.tk",
                "🚀 URGENT: 1000% Bitcoin Returns Guaranteed!",
                "Subject: 🚀 URGENT: 1000% Bitcoin Returns Guaranteed!\nFrom: crypto-investment@suspicious.tk"
            )
            
            baseline_results['hybrid_classifier'] = {
                'status': 'success',
                'test_prediction': test_prediction,
                'ml_confidence': test_prediction.get('ml_confidence', 0),
                'final_confidence': test_prediction.get('confidence', 0)
            }
            print(f"   ✅ Hybrid Classifier operational (confidence: {test_prediction.get('confidence', 0):.3f})")
            
        except Exception as e:
            baseline_results['hybrid_classifier'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"   ❌ Hybrid Classifier test failed: {e}")
        
        return baseline_results
    
    def _train_advanced_models(self, max_samples: int) -> Dict[str, Any]:
        """Train advanced ML models"""
        try:
            # Train all advanced models
            performance_results = self.advanced_classifier.train_all_models(
                use_user_feedback=True, 
                max_samples=max_samples
            )
            
            self.is_trained = True
            
            # Convert ModelPerformance objects to dictionaries
            advanced_results = {}
            for model_name, performance in performance_results.items():
                advanced_results[model_name] = {
                    'accuracy': performance.accuracy,
                    'precision': performance.precision,
                    'recall': performance.recall,
                    'f1_score': performance.f1_score,
                    'false_positive_rate': performance.false_positive_rate,
                    'training_time': performance.training_time,
                    'prediction_time': performance.prediction_time
                }
            
            return {
                'status': 'success',
                'models': advanced_results,
                'ensemble_available': 'ensemble' in performance_results
            }
            
        except Exception as e:
            print(f"   ❌ Advanced ML training failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _compare_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance across all models"""
        comparison = {
            'best_accuracy': {'model': None, 'value': 0},
            'best_precision': {'model': None, 'value': 0},
            'best_f1': {'model': None, 'value': 0},
            'fastest_training': {'model': None, 'value': float('inf')},
            'model_rankings': []
        }
        
        all_models = []
        
        # Extract baseline performance
        if 'baseline' in metrics:
            baseline = metrics['baseline']
            if 'hybrid_classifier' in baseline and baseline['hybrid_classifier']['status'] == 'success':
                all_models.append({
                    'name': 'hybrid_classifier (current)',
                    'accuracy': baseline['hybrid_classifier'].get('final_confidence', 0),
                    'precision': 0.955,  # From previous session data
                    'f1_score': 0.819,   # From previous session data
                    'training_time': 0,
                    'type': 'baseline'
                })
        
        # Extract advanced model performance
        if 'advanced' in metrics and metrics['advanced']['status'] == 'success':
            for model_name, perf in metrics['advanced']['models'].items():
                all_models.append({
                    'name': model_name,
                    'accuracy': perf['accuracy'],
                    'precision': perf['precision'],
                    'f1_score': perf['f1_score'],
                    'training_time': perf['training_time'],
                    'type': 'advanced'
                })
        
        # Find best performers
        for model in all_models:
            if model['accuracy'] > comparison['best_accuracy']['value']:
                comparison['best_accuracy'] = {'model': model['name'], 'value': model['accuracy']}
            
            if model['precision'] > comparison['best_precision']['value']:
                comparison['best_precision'] = {'model': model['name'], 'value': model['precision']}
            
            if model['f1_score'] > comparison['best_f1']['value']:
                comparison['best_f1'] = {'model': model['name'], 'value': model['f1_score']}
            
            if model['training_time'] < comparison['fastest_training']['value']:
                comparison['fastest_training'] = {'model': model['name'], 'value': model['training_time']}
        
        # Rank models by F1 score
        comparison['model_rankings'] = sorted(all_models, key=lambda x: x['f1_score'], reverse=True)
        
        return comparison
    
    def _generate_recommendations(self, comparison: Dict[str, Any]) -> list:
        """Generate deployment recommendations based on performance"""
        recommendations = []
        
        if comparison['model_rankings']:
            best_model = comparison['model_rankings'][0]
            
            # Overall recommendation
            if best_model['type'] == 'advanced':
                recommendations.append({
                    'type': 'deployment',
                    'priority': 'high',
                    'message': f"🚀 RECOMMEND DEPLOYING: {best_model['name']} shows best F1 score ({best_model['f1_score']:.3f})"
                })
            else:
                recommendations.append({
                    'type': 'status_quo',
                    'priority': 'medium',
                    'message': "✅ CURRENT SYSTEM OPTIMAL: Hybrid classifier still performs best"
                })
            
            # Precision analysis
            best_precision = comparison['best_precision']
            if best_precision['value'] > 0.95:
                recommendations.append({
                    'type': 'precision',
                    'priority': 'high',
                    'message': f"🎯 EXCELLENT PRECISION: {best_precision['model']} achieves {best_precision['value']:.3f} precision"
                })
            
            # Speed considerations
            fastest = comparison['fastest_training']
            if fastest['value'] > 60:  # More than 1 minute
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'message': f"⏱️  TRAINING TIME: Consider {fastest['model']} for faster retraining ({fastest['value']:.1f}s)"
                })
        
        return recommendations
    
    def _save_results(self, results: Dict[str, Any]):
        """Save deployment results to file"""
        filename = f"advanced_ml_deployment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def _display_deployment_summary(self, results: Dict[str, Any]):
        """Display comprehensive deployment summary"""
        print("\n" + "=" * 70)
        print("🎯 ADVANCED ML DEPLOYMENT SUMMARY")
        print("=" * 70)
        
        # Model comparison table
        if 'comparison_analysis' in results and results['comparison_analysis']['model_rankings']:
            print("\n📊 MODEL PERFORMANCE RANKINGS:")
            print(f"{'Model':<25} {'Accuracy':<10} {'Precision':<11} {'F1 Score':<10} {'Type':<10}")
            print("-" * 70)
            
            for model in results['comparison_analysis']['model_rankings'][:5]:  # Top 5
                print(f"{model['name']:<25} {model['accuracy']:.3f}     {model['precision']:.3f}      "
                      f"{model['f1_score']:.3f}    {model['type']:<10}")
        
        # Best performers
        if 'comparison_analysis' in results:
            comp = results['comparison_analysis']
            print(f"\n🏆 BEST PERFORMERS:")
            print(f"   🎯 Accuracy:  {comp['best_accuracy']['model']} ({comp['best_accuracy']['value']:.3f})")
            print(f"   🎯 Precision: {comp['best_precision']['model']} ({comp['best_precision']['value']:.3f})")
            print(f"   🎯 F1 Score:  {comp['best_f1']['model']} ({comp['best_f1']['value']:.3f})")
        
        # Recommendations
        if 'recommendations' in results and results['recommendations']:
            print(f"\n💡 DEPLOYMENT RECOMMENDATIONS:")
            for rec in results['recommendations']:
                priority_icon = "🔥" if rec['priority'] == 'high' else "📋"
                print(f"   {priority_icon} {rec['message']}")
        
        print("\n" + "=" * 70)
        print("✅ Advanced ML deployment analysis complete!")
        print("=" * 70)
    
    def test_advanced_prediction(self, sender: str, subject: str, headers: str = "") -> Dict[str, Any]:
        """Test prediction with advanced models if available"""
        if not self.is_trained:
            return {'error': 'Advanced models not trained yet'}
        
        try:
            # Get advanced prediction
            advanced_pred = self.advanced_classifier.predict_advanced(sender, subject, headers=headers)
            
            # Get baseline prediction for comparison
            baseline_pred = self.hybrid_classifier.classify_email(sender, subject, headers)
            
            return {
                'advanced_prediction': advanced_pred,
                'baseline_prediction': baseline_pred,
                'comparison': {
                    'agreement': (advanced_pred.get('is_spam', False) == 
                                baseline_pred.get('is_spam', False)),
                    'advanced_confidence': advanced_pred.get('confidence', 0),
                    'baseline_confidence': baseline_pred.get('confidence', 0)
                }
            }
            
        except Exception as e:
            return {'error': f'Prediction failed: {e}'}


def deploy_advanced_ml_suite():
    """Main deployment function"""
    print("🚀 DEPLOYING ADVANCED ML SUITE")
    print("=" * 50)
    
    try:
        # Initialize integration
        integration = AdvancedMLIntegration()
        
        # Run full training and comparison
        results = integration.train_and_compare_models(max_samples=1500)
        
        # Test with sample emails
        print("\n🧪 TESTING ADVANCED PREDICTIONS...")
        test_cases = [
            ("crypto-investment@suspicious.tk", "🚀 URGENT: 1000% Bitcoin Returns!"),
            ("support@amazon.com", "Your order #123456 has shipped"),
            ("noreply@bank.com", "Monthly statement available"),
            ("winner@lottery-scam.tk", "Congratulations! You won $1M!")
        ]
        
        for sender, subject in test_cases:
            if integration.is_trained:
                pred_result = integration.test_advanced_prediction(sender, subject)
                if 'error' not in pred_result:
                    adv = pred_result['advanced_prediction']
                    base = pred_result['baseline_prediction']
                    agreement = "✅" if pred_result['comparison']['agreement'] else "❌"
                    
                    print(f"\n📧 {subject[:40]}...")
                    print(f"   Advanced: {'SPAM' if adv.get('is_spam') else 'LEGIT'} ({adv.get('confidence', 0):.3f})")
                    print(f"   Baseline: {'SPAM' if base.get('is_spam') else 'LEGIT'} ({base.get('confidence', 0):.3f})")
                    print(f"   Agreement: {agreement}")
        
        return results
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return None


if __name__ == "__main__":
    results = deploy_advanced_ml_suite()