#!/usr/bin/env python3
"""
ATLAS Strategic Intelligence Framework Test Harness
==================================================

MISSION: Validate 812-line Adaptive Spam Logic Framework against research flagged emails
TARGET: Improve accuracy from 95.6% → 99.5% through precision testing

This test harness focuses on the 4 key problem domains:
1. Nextdoor emails (ss.email.nextdoor.com) misclassified as "Real Estate Spam"
2. Macy's emails (emails.macys.com) misclassified as "Payment Scam" 
3. Warfarersuk.com phishing preserved as legitimate (should be PHISHING)
4. Medical/service emails with inconsistent classifications

Author: ATLAS Intelligence Testing Agent
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import tempfile

# Import the Strategic Intelligence Framework
sys.path.append('/Users/Badman/Desktop/playground/email-intelligence-tester-work/REPOS/Atlas_Email/src')
from atlas_email.core.logical_classifier import LogicalEmailClassifier

class StrategicIntelligenceTestHarness:
    """
    Comprehensive test harness for validating the Strategic Intelligence Framework
    against known problem cases and research flagged emails.
    """
    
    def __init__(self):
        self.test_db_path = None
        self.classifier = LogicalEmailClassifier()
        self.test_results = []
        self.accuracy_metrics = {
            'before': {'correct': 0, 'total': 0, 'accuracy': 0.0},
            'after': {'correct': 0, 'total': 0, 'accuracy': 0.0}
        }
        
    def create_test_database(self):
        """Create test database with key problem domain emails"""
        
        # Create temporary test database
        temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(temp_dir, 'intelligence_test.db')
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create minimal required tables
        cursor.execute('''
            CREATE TABLE processed_emails_bulletproof (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                uid TEXT,
                sender_email TEXT NOT NULL,
                sender_domain TEXT,
                subject TEXT NOT NULL,
                action TEXT NOT NULL CHECK (action IN ('DELETED', 'PRESERVED')),
                reason TEXT,
                category TEXT,
                confidence_score REAL,
                raw_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE email_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_uid TEXT NOT NULL,
                folder_name TEXT NOT NULL DEFAULT 'INBOX',
                account_id INTEGER NOT NULL DEFAULT 1,
                flag_type TEXT DEFAULT 'RESEARCH',
                flag_reason TEXT,
                sender_email TEXT,
                subject TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test emails based on the 4 key problem domains
        test_emails = self.get_test_email_dataset()
        
        for email in test_emails:
            # Insert email record
            cursor.execute('''
                INSERT INTO processed_emails_bulletproof 
                (uid, sender_email, sender_domain, subject, action, reason, category, confidence_score, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email['uid'],
                email['sender_email'], 
                email['sender_domain'],
                email['subject'],
                email['current_action'],
                email['current_reason'],
                email['current_category'],
                email['current_confidence'],
                json.dumps(email.get('raw_data', {}))
            ))
            
            # Flag for research
            cursor.execute('''
                INSERT INTO email_flags 
                (email_uid, sender_email, subject, flag_type, flag_reason)
                VALUES (?, ?, ?, 'RESEARCH', ?)
            ''', (
                email['uid'],
                email['sender_email'],
                email['subject'], 
                email['problem_description']
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Created test database with {len(test_emails)} research flagged emails")
        print(f"📍 Database location: {self.test_db_path}")
        
    def get_test_email_dataset(self) -> List[Dict[str, Any]]:
        """
        Generate comprehensive test dataset focusing on the 4 key problem domains
        """
        
        test_emails = []
        
        # PROBLEM DOMAIN 1: Nextdoor emails misclassified as "Real Estate Spam"
        nextdoor_emails = [
            {
                'uid': 'NEXTDOOR_001',
                'sender_email': 'notify@ss.email.nextdoor.com',
                'sender_domain': 'ss.email.nextdoor.com',
                'subject': 'New neighbor recommendations and local updates',
                'current_action': 'DELETED',
                'current_reason': 'Real estate investment spam',
                'current_category': 'Real Estate Spam',
                'current_confidence': 0.70,
                'expected_action': 'PRESERVED',
                'expected_category': 'Promotional Email',
                'problem_description': 'Legitimate neighborhood social network misclassified as real estate spam',
                'raw_data': {
                    'body': 'Your neighbors have shared new recommendations in Castro Valley. See local events and community updates.',
                    'headers': {'From': 'notify@ss.email.nextdoor.com'}
                }
            },
            {
                'uid': 'NEXTDOOR_002', 
                'sender_email': 'updates@email.nextdoor.com',
                'sender_domain': 'email.nextdoor.com',
                'subject': 'Crime alert in your neighborhood - Castro Valley',
                'current_action': 'DELETED',
                'current_reason': 'Real estate investment spam',
                'current_category': 'Real Estate Spam', 
                'current_confidence': 0.75,
                'expected_action': 'PRESERVED',
                'expected_category': 'Promotional Email',
                'problem_description': 'Legitimate safety alert misclassified due to neighborhood keywords',
                'raw_data': {
                    'body': 'Alert: Package theft reported on Main Street. Stay vigilant and report suspicious activity.',
                    'headers': {'From': 'updates@email.nextdoor.com'}
                }
            }
        ]
        
        # PROBLEM DOMAIN 2: Macy's emails misclassified as "Payment Scam"
        macys_emails = [
            {
                'uid': 'MACYS_001',
                'sender_email': 'orders@emails.macys.com',
                'sender_domain': 'emails.macys.com',
                'subject': 'Your payment method needs updating',
                'current_action': 'DELETED',
                'current_reason': 'Payment scam via brand impersonation',
                'current_category': 'Payment Scam',
                'current_confidence': 0.90,
                'expected_action': 'PRESERVED', 
                'expected_category': 'Promotional Email',
                'problem_description': 'Legitimate retailer payment notification misclassified as scam',
                'raw_data': {
                    'body': 'Update your payment method to continue enjoying Macy\'s benefits and rewards.',
                    'headers': {'From': 'orders@emails.macys.com'}
                }
            },
            {
                'uid': 'MACYS_002',
                'sender_email': 'billing@macys.com', 
                'sender_domain': 'macys.com',
                'subject': 'Account billing update required',
                'current_action': 'DELETED',
                'current_reason': 'Payment scam content detected',
                'current_category': 'Payment Scam',
                'current_confidence': 0.85,
                'expected_action': 'PRESERVED',
                'expected_category': 'Promotional Email', 
                'problem_description': 'Legitimate billing communication misclassified',
                'raw_data': {
                    'body': 'Hi customer, please update your billing information to avoid service interruption.',
                    'headers': {'From': 'billing@macys.com'}
                }
            }
        ]
        
        # PROBLEM DOMAIN 3: Warfarersuk.com phishing preserved as legitimate
        phishing_emails = [
            {
                'uid': 'PHISHING_001',
                'sender_email': 'admin@warfarersuk.com',
                'sender_domain': 'warfarersuk.com', 
                'subject': 'Urgent: Verify your account to avoid suspension',
                'current_action': 'PRESERVED',
                'current_reason': 'Legitimate business communication',
                'current_category': 'Promotional Email',
                'current_confidence': 0.60,
                'expected_action': 'DELETED',
                'expected_category': 'Phishing',
                'problem_description': 'Clear phishing attempt with urgency tactics preserved as legitimate',
                'raw_data': {
                    'body': 'URGENT: Your account will be suspended in 24 hours. Click here to verify now: http://warfarersuk.com/verify-account-urgent',
                    'headers': {'From': 'admin@warfarersuk.com'}
                }
            },
            {
                'uid': 'PHISHING_002',
                'sender_email': 'security@warfarersuk.com',
                'sender_domain': 'warfarersuk.com',
                'subject': 'Account security verification required immediately',
                'current_action': 'PRESERVED', 
                'current_reason': 'Security notification from known domain',
                'current_category': 'Promotional Email',
                'current_confidence': 0.55,
                'expected_action': 'DELETED',
                'expected_category': 'Phishing',
                'problem_description': 'Phishing with security pretext misclassified as legitimate',
                'raw_data': {
                    'body': 'Security Alert: Suspicious activity detected. Verify identity immediately or account will be locked.',
                    'headers': {'From': 'security@warfarersuk.com'}
                }
            }
        ]
        
        # PROBLEM DOMAIN 4: Medical/service emails with inconsistent classifications
        medical_service_emails = [
            {
                'uid': 'MEDICAL_001',
                'sender_email': 'appointments@healthcenter.com',
                'sender_domain': 'healthcenter.com',
                'subject': 'Appointment reminder - Dr. Smith tomorrow',
                'current_action': 'DELETED',
                'current_reason': 'Health spam with exaggerated claims',
                'current_category': 'Health & Medical Spam', 
                'current_confidence': 0.80,
                'expected_action': 'PRESERVED',
                'expected_category': 'Promotional Email',
                'problem_description': 'Legitimate medical appointment reminder misclassified as health spam',
                'raw_data': {
                    'body': 'Reminder: You have an appointment with Dr. Smith tomorrow at 2 PM. Please arrive 15 minutes early.',
                    'headers': {'From': 'appointments@healthcenter.com'}
                }
            },
            {
                'uid': 'MEDICAL_002',
                'sender_email': 'results@labcorp.com',
                'sender_domain': 'labcorp.com', 
                'subject': 'Your lab results are ready for pickup',
                'current_action': 'DELETED',
                'current_reason': 'Health spam content detected',
                'current_category': 'Health & Medical Spam',
                'current_confidence': 0.75,
                'expected_action': 'PRESERVED',
                'expected_category': 'Promotional Email',
                'problem_description': 'Legitimate lab results notification misclassified',
                'raw_data': {
                    'body': 'Your recent lab work is complete. Results are available for secure pickup at our office.',
                    'headers': {'From': 'results@labcorp.com'}
                }
            },
            {
                'uid': 'SERVICE_001',
                'sender_email': 'support@xfinity.com',
                'sender_domain': 'xfinity.com',
                'subject': 'Service maintenance scheduled in your area',
                'current_action': 'DELETED',
                'current_reason': 'Promotional marketing content',
                'current_category': 'Marketing Spam',
                'current_confidence': 0.65,
                'expected_action': 'PRESERVED',
                'expected_category': 'Promotional Email',
                'problem_description': 'ISP service notification misclassified as marketing spam',
                'raw_data': {
                    'body': 'Scheduled maintenance on Monday 9 AM - 11 AM may cause brief service interruptions in your area.',
                    'headers': {'From': 'support@xfinity.com'}
                }
            }
        ]
        
        # Add control cases - emails that should remain correctly classified
        control_emails = [
            {
                'uid': 'CONTROL_SPAM_001',
                'sender_email': 'winner@mvppnzrnrlmkqk.tk',
                'sender_domain': 'mvppnzrnrlmkqk.tk',
                'subject': 'CONGRATULATIONS! You won $50,000!!!',
                'current_action': 'DELETED',
                'current_reason': 'Prize scam with suspicious domain',
                'current_category': 'Phishing',
                'current_confidence': 0.95,
                'expected_action': 'DELETED',
                'expected_category': 'Phishing',
                'problem_description': 'Control case - legitimate spam detection (should remain classified as spam)',
                'raw_data': {
                    'body': 'WINNER ALERT: Claim your prize now! Click here before it expires!',
                    'headers': {'From': 'winner@mvppnzrnrlmkqk.tk'}
                }
            },
            {
                'uid': 'CONTROL_LEGIT_001',
                'sender_email': 'receipts@amazon.com',
                'sender_domain': 'amazon.com',
                'subject': 'Your Amazon.com order has shipped',
                'current_action': 'PRESERVED',
                'current_reason': 'Legitimate promotional email from verified retailer', 
                'current_category': 'Promotional Email',
                'current_confidence': 0.85,
                'expected_action': 'PRESERVED',
                'expected_category': 'Promotional Email',
                'problem_description': 'Control case - legitimate email (should remain preserved)',
                'raw_data': {
                    'body': 'Your order #123-456789 has shipped and will arrive Tuesday.',
                    'headers': {'From': 'receipts@amazon.com'}
                }
            }
        ]
        
        # Combine all test cases
        test_emails.extend(nextdoor_emails)
        test_emails.extend(macys_emails) 
        test_emails.extend(phishing_emails)
        test_emails.extend(medical_service_emails)
        test_emails.extend(control_emails)
        
        return test_emails
    
    def run_strategic_intelligence_tests(self):
        """
        Run the Strategic Intelligence Framework against test emails and compare results
        """
        
        print(f"\n🧪 ATLAS Strategic Intelligence Framework Validation")
        print(f"=" * 70)
        print(f"🎯 TARGET: Validate accuracy improvement 95.6% → 99.5%")
        print(f"📧 Testing {len(self.get_test_email_dataset())} research flagged emails")
        print(f"🔍 Focus: 4 key problem domains + control cases")
        print()
        
        # Load test emails from database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pe.*, ef.flag_reason, ef.flag_type
            FROM processed_emails_bulletproof pe
            JOIN email_flags ef ON pe.uid = ef.email_uid
            WHERE ef.flag_type = 'RESEARCH' AND ef.is_active = 1
            ORDER BY pe.uid
        ''')
        
        test_cases = cursor.fetchall()
        conn.close()
        
        # Process each test case
        for i, test_case in enumerate(test_cases, 1):
            uid, timestamp, sender_email, sender_domain, subject = test_case[0], test_case[1], test_case[2], test_case[3], test_case[4]
            current_action, current_reason, current_category, current_confidence = test_case[5], test_case[6], test_case[7], test_case[8]
            raw_data, flag_reason = test_case[9], test_case[10]
            
            print(f"📧 Test Case #{i}: {uid}")
            print(f"   From: {sender_email}")
            print(f"   Subject: {subject}")
            print(f"   Problem: {flag_reason}")
            
            # Current classification (before Strategic Intelligence Framework)
            print(f"   ❌ BEFORE: {current_category} (confidence: {current_confidence:.2f}) → {current_action}")
            print(f"      Reason: {current_reason}")
            
            # New classification with Strategic Intelligence Framework
            new_category, new_confidence, new_reason = self.classifier.classify_email(
                sender_email, subject, ""
            )
            
            # Determine new action based on category
            spam_categories = [
                'Adult & Dating Spam', 'Phishing', 'Payment Scam', 'Financial & Investment Spam',
                'Health & Medical Spam', 'Gambling Spam', 'Real Estate Spam', 
                'Legal & Compensation Scams', 'Marketing Spam', 'Brand Impersonation'
            ]
            new_action = 'DELETED' if new_category in spam_categories else 'PRESERVED'
            
            print(f"   ✨ AFTER:  {new_category} (confidence: {new_confidence:.2f}) → {new_action}")
            print(f"      Reason: {new_reason}")
            
            # Determine expected result from test dataset
            test_data = self.get_test_email_dataset()
            expected_result = next((email for email in test_data if email['uid'] == uid), None)
            
            if expected_result:
                expected_action = expected_result['expected_action']
                expected_category = expected_result['expected_category']
                
                # Calculate accuracy
                was_correct_before = (current_action == expected_action)
                is_correct_after = (new_action == expected_action) 
                
                # Update metrics
                self.accuracy_metrics['before']['total'] += 1
                self.accuracy_metrics['after']['total'] += 1
                
                if was_correct_before:
                    self.accuracy_metrics['before']['correct'] += 1
                if is_correct_after:
                    self.accuracy_metrics['after']['correct'] += 1
                
                # Result analysis
                if not was_correct_before and is_correct_after:
                    print(f"   🎯 IMPROVEMENT: Fixed misclassification!")
                    improvement = "FIXED"
                elif was_correct_before and not is_correct_after:
                    print(f"   ⚠️  REGRESSION: Broke correct classification")
                    improvement = "BROKEN"
                elif was_correct_before and is_correct_after:
                    print(f"   ✅ MAINTAINED: Kept correct classification")
                    improvement = "MAINTAINED"
                else:
                    print(f"   ❌ UNCHANGED: Still misclassified")
                    improvement = "UNCHANGED"
                
                # Store detailed result
                self.test_results.append({
                    'uid': uid,
                    'sender_email': sender_email,
                    'subject': subject,
                    'problem_domain': flag_reason,
                    'before_classification': {
                        'category': current_category,
                        'confidence': current_confidence,
                        'action': current_action,
                        'reason': current_reason
                    },
                    'after_classification': {
                        'category': new_category,
                        'confidence': new_confidence,
                        'action': new_action,
                        'reason': new_reason
                    },
                    'expected': {
                        'category': expected_category,
                        'action': expected_action
                    },
                    'improvement': improvement,
                    'was_correct_before': was_correct_before,
                    'is_correct_after': is_correct_after
                })
            
            print()
        
        # Calculate final accuracy metrics
        if self.accuracy_metrics['before']['total'] > 0:
            self.accuracy_metrics['before']['accuracy'] = (
                self.accuracy_metrics['before']['correct'] / 
                self.accuracy_metrics['before']['total'] * 100
            )
        
        if self.accuracy_metrics['after']['total'] > 0:
            self.accuracy_metrics['after']['accuracy'] = (
                self.accuracy_metrics['after']['correct'] / 
                self.accuracy_metrics['after']['total'] * 100
            )
    
    def generate_intelligence_report(self):
        """
        Generate comprehensive test report with before/after metrics and analysis
        """
        
        report = []
        report.append("🔬 ATLAS STRATEGIC INTELLIGENCE FRAMEWORK VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"🎯 Mission: Validate accuracy improvement 95.6% → 99.5%")
        report.append(f"📊 Test Cases: {len(self.test_results)}")
        report.append("")
        
        # Overall Accuracy Metrics
        report.append("📈 OVERALL ACCURACY METRICS")
        report.append("-" * 40)
        report.append(f"BEFORE Strategic Intelligence Framework:")
        report.append(f"  Correct: {self.accuracy_metrics['before']['correct']}/{self.accuracy_metrics['before']['total']}")
        report.append(f"  Accuracy: {self.accuracy_metrics['before']['accuracy']:.1f}%")
        report.append("")
        report.append(f"AFTER Strategic Intelligence Framework:")
        report.append(f"  Correct: {self.accuracy_metrics['after']['correct']}/{self.accuracy_metrics['after']['total']}")
        report.append(f"  Accuracy: {self.accuracy_metrics['after']['accuracy']:.1f}%")
        report.append("")
        
        accuracy_improvement = (
            self.accuracy_metrics['after']['accuracy'] - 
            self.accuracy_metrics['before']['accuracy']
        )
        
        if accuracy_improvement > 0:
            report.append(f"🎯 ACCURACY IMPROVEMENT: +{accuracy_improvement:.1f} percentage points")
        elif accuracy_improvement < 0:
            report.append(f"⚠️  ACCURACY REGRESSION: {accuracy_improvement:.1f} percentage points")
        else:
            report.append(f"📊 ACCURACY UNCHANGED: {accuracy_improvement:.1f} percentage points")
        
        report.append("")
        
        # Improvement Analysis
        improvements = [r for r in self.test_results if r['improvement'] == 'FIXED']
        regressions = [r for r in self.test_results if r['improvement'] == 'BROKEN'] 
        maintained = [r for r in self.test_results if r['improvement'] == 'MAINTAINED']
        unchanged = [r for r in self.test_results if r['improvement'] == 'UNCHANGED']
        
        report.append("🔍 CLASSIFICATION CHANGES ANALYSIS")
        report.append("-" * 40)
        report.append(f"✅ Fixed misclassifications: {len(improvements)}")
        report.append(f"⚠️  Broke correct classifications: {len(regressions)}")
        report.append(f"✨ Maintained correct classifications: {len(maintained)}")
        report.append(f"❌ Unchanged misclassifications: {len(unchanged)}")
        report.append("")
        
        # Problem Domain Analysis
        report.append("🎯 KEY PROBLEM DOMAIN RESULTS")
        report.append("-" * 40)
        
        problem_domains = {}
        for result in self.test_results:
            domain = result['problem_domain'].split('-')[0].strip()
            if domain not in problem_domains:
                problem_domains[domain] = {'total': 0, 'fixed': 0, 'broken': 0}
            problem_domains[domain]['total'] += 1
            if result['improvement'] == 'FIXED':
                problem_domains[domain]['fixed'] += 1
            elif result['improvement'] == 'BROKEN':
                problem_domains[domain]['broken'] += 1
        
        for domain, stats in problem_domains.items():
            fix_rate = (stats['fixed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report.append(f"{domain}:")
            report.append(f"  Fixed: {stats['fixed']}/{stats['total']} ({fix_rate:.1f}%)")
            if stats['broken'] > 0:
                report.append(f"  Broken: {stats['broken']}")
        
        report.append("")
        
        # Detailed Test Case Results
        report.append("📋 DETAILED TEST CASE RESULTS")
        report.append("-" * 40)
        
        for result in self.test_results:
            report.append(f"🔸 {result['uid']}: {result['improvement']}")
            report.append(f"   From: {result['sender_email']}")
            report.append(f"   Subject: {result['subject'][:60]}...")
            report.append(f"   Problem: {result['problem_domain']}")
            
            before = result['before_classification']
            after = result['after_classification']
            expected = result['expected']
            
            report.append(f"   BEFORE: {before['category']} → {before['action']}")
            report.append(f"   AFTER:  {after['category']} → {after['action']}")
            report.append(f"   EXPECTED: {expected['category']} → {expected['action']}")
            report.append("")
        
        # Strategic Recommendations
        report.append("🎯 STRATEGIC RECOMMENDATIONS")
        report.append("-" * 40)
        
        if accuracy_improvement >= 2.0:
            report.append("✅ Framework shows significant improvement - RECOMMEND DEPLOYMENT")
        elif accuracy_improvement >= 0.5:
            report.append("✨ Framework shows modest improvement - CONSIDER DEPLOYMENT") 
        elif accuracy_improvement >= 0:
            report.append("📊 Framework maintains accuracy - NEUTRAL RECOMMENDATION")
        else:
            report.append("⚠️  Framework shows regression - NEEDS REFINEMENT")
        
        if len(improvements) > 0:
            report.append(f"🎯 Successfully fixed {len(improvements)} key misclassifications")
        
        if len(regressions) > 0:
            report.append(f"⚠️  Review {len(regressions)} classification regressions")
        
        if len(unchanged) > 0:
            report.append(f"🔧 {len(unchanged)} cases still need framework improvements")
        
        report.append("")
        report.append("📊 MISSION STATUS: Test validation completed")
        report.append(f"🎯 TARGET ACCURACY 99.5%: {'✅ ACHIEVED' if self.accuracy_metrics['after']['accuracy'] >= 99.5 else '❌ NOT ACHIEVED'}")
        report.append("")
        report.append("Generated by ATLAS Intelligence Testing Agent 🤖")
        
        return "\n".join(report)
    
    def save_results_to_repository(self):
        """
        Save test results to main repository following CRITICAL_RESULTS_PRESERVATION
        """
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate detailed report
        report_content = self.generate_intelligence_report()
        
        # Save to main repository
        results_dir = "/Users/Badman/Desktop/playground/email-intelligence-tester-work"
        report_path = os.path.join(results_dir, f"STRATEGIC_INTELLIGENCE_TEST_REPORT_{timestamp}.md")
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        # Save raw test data as JSON
        data_path = os.path.join(results_dir, f"STRATEGIC_INTELLIGENCE_TEST_DATA_{timestamp}.json")
        test_data = {
            'metadata': {
                'test_date': datetime.now().isoformat(),
                'framework_version': '812-line Adaptive Spam Logic Framework',
                'target_accuracy': 99.5,
                'test_cases_count': len(self.test_results)
            },
            'accuracy_metrics': self.accuracy_metrics,
            'test_results': self.test_results
        }
        
        with open(data_path, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print(f"💾 Test results saved to repository:")
        print(f"   📄 Report: {report_path}")
        print(f"   📊 Data: {data_path}")
        
        return report_path, data_path
    
    def run_complete_validation(self):
        """
        Execute complete Strategic Intelligence Framework validation
        """
        
        print("🚀 ATLAS Strategic Intelligence Framework Validation Starting...")
        print()
        
        # Step 1: Create test database with problem domain emails
        print("📊 Step 1: Creating test database with key problem domain emails...")
        self.create_test_database()
        print()
        
        # Step 2: Run Strategic Intelligence tests
        print("🧪 Step 2: Running Strategic Intelligence Framework tests...")
        self.run_strategic_intelligence_tests()
        print()
        
        # Step 3: Generate comprehensive report
        print("📋 Step 3: Generating intelligence validation report...")
        report_content = self.generate_intelligence_report()
        print(report_content)
        print()
        
        # Step 4: Save results to repository
        print("💾 Step 4: Saving results to main repository...")
        report_path, data_path = self.save_results_to_repository()
        print()
        
        print("✅ ATLAS Strategic Intelligence Framework validation completed!")
        print(f"🎯 Final Accuracy: {self.accuracy_metrics['after']['accuracy']:.1f}%")
        print(f"📈 Improvement: {self.accuracy_metrics['after']['accuracy'] - self.accuracy_metrics['before']['accuracy']:+.1f} percentage points")
        
        return report_path, data_path


def main():
    """Main execution function"""
    
    print("🤖 ATLAS Intelligence Testing Agent Deployed")
    print("🎯 Mission: Validate Strategic Intelligence Framework")
    print("📊 Target: Accuracy improvement 95.6% → 99.5%")
    print()
    
    # Create and run test harness
    harness = StrategicIntelligenceTestHarness()
    report_path, data_path = harness.run_complete_validation()
    
    print(f"\n🏁 Mission completed. Results preserved at:")
    print(f"   {report_path}")
    print(f"   {data_path}")


if __name__ == "__main__":
    main()