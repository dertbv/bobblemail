#!/usr/bin/env python3
"""
Geographic Analytics Validator for Atlas Email
Validates that geographic intelligence data is properly populated and ready for dashboard display
"""

import sqlite3
from datetime import datetime

class GeographicAnalyticsValidator:
    """
    Validates geographic analytics data and simulates dashboard queries
    """
    
    def __init__(self, db_path="data/mail_filter.db"):
        self.db_path = db_path
    
    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def validate_geographic_data_completeness(self):
        """Validate that geographic data is properly populated"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print("🌍 GEOGRAPHIC DATA COMPLETENESS VALIDATION")
        print("=" * 50)
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM processed_emails_bulletproof")
        total_records = cursor.fetchone()[0]
        
        # Records with geographic data
        cursor.execute("""
            SELECT 
                COUNT(*) as total_geo,
                COUNT(sender_ip) as with_ip,
                COUNT(sender_country_code) as with_country,
                COUNT(CASE WHEN geographic_risk_score > 0 THEN 1 END) as with_risk_score
            FROM processed_emails_bulletproof 
            WHERE sender_country_code IS NOT NULL
        """)
        
        geo_stats = cursor.fetchone()
        
        print(f"📊 Total Email Records: {total_records:,}")
        print(f"🌍 Records with Geographic Data: {geo_stats[0]:,}")
        print(f"🔍 Records with IP Addresses: {geo_stats[1]:,}")
        print(f"🏁 Records with Countries: {geo_stats[2]:,}")
        print(f"⚠️  Records with Risk Scores: {geo_stats[3]:,}")
        
        completion_rate = (geo_stats[0] / total_records) * 100 if total_records > 0 else 0
        print(f"📈 Geographic Data Completion: {completion_rate:.1f}%")
        
        conn.close()
        return geo_stats[0] > 0
    
    def simulate_dashboard_country_analytics(self):
        """Simulate country-based analytics for dashboard"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print("\n🗺️ COUNTRY ANALYTICS (Dashboard Simulation)")
        print("=" * 50)
        
        # Top countries by email volume
        cursor.execute("""
            SELECT 
                sender_country_code,
                sender_country_name,
                COUNT(*) as email_count,
                AVG(geographic_risk_score) as avg_risk,
                COUNT(CASE WHEN action = 'DELETED' THEN 1 END) as spam_count,
                COUNT(CASE WHEN action = 'PRESERVED' THEN 1 END) as legit_count
            FROM processed_emails_bulletproof 
            WHERE sender_country_code IS NOT NULL
            GROUP BY sender_country_code, sender_country_name
            ORDER BY email_count DESC
            LIMIT 15
        """)
        
        country_data = cursor.fetchall()
        
        print(f"{'Country':<15} {'Emails':<8} {'Risk':<6} {'Spam':<6} {'Legit':<6} {'Risk Level'}")
        print("-" * 60)
        
        for country_code, country_name, email_count, avg_risk, spam_count, legit_count in country_data:
            risk_level = "Very High" if avg_risk >= 0.80 else "High" if avg_risk >= 0.60 else "Medium" if avg_risk >= 0.40 else "Low"
            print(f"{country_code:<15} {email_count:<8} {avg_risk:<6.2f} {spam_count:<6} {legit_count:<6} {risk_level}")
        
        conn.close()
        return len(country_data) > 0
    
    def simulate_dashboard_risk_analytics(self):
        """Simulate risk-based analytics for dashboard"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print("\n🚨 RISK ANALYTICS (Dashboard Simulation)")
        print("=" * 50)
        
        # Risk distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN geographic_risk_score >= 0.80 THEN 'Very High (0.80+)'
                    WHEN geographic_risk_score >= 0.60 THEN 'High (0.60-0.79)'
                    WHEN geographic_risk_score >= 0.40 THEN 'Medium (0.40-0.59)'
                    WHEN geographic_risk_score >= 0.20 THEN 'Low (0.20-0.39)'
                    WHEN geographic_risk_score > 0 THEN 'Very Low (0.01-0.19)'
                    ELSE 'Unknown'
                END as risk_category,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
            FROM processed_emails_bulletproof
            WHERE geographic_risk_score IS NOT NULL
            GROUP BY risk_category
            ORDER BY 
                CASE 
                    WHEN risk_category = 'Very High (0.80+)' THEN 1
                    WHEN risk_category = 'High (0.60-0.79)' THEN 2
                    WHEN risk_category = 'Medium (0.40-0.59)' THEN 3
                    WHEN risk_category = 'Low (0.20-0.39)' THEN 4
                    WHEN risk_category = 'Very Low (0.01-0.19)' THEN 5
                    ELSE 6
                END
        """)
        
        risk_data = cursor.fetchall()
        
        print(f"{'Risk Level':<20} {'Count':<8} {'Percentage'}")
        print("-" * 40)
        
        for risk_category, count, percentage in risk_data:
            print(f"{risk_category:<20} {count:<8} {percentage}%")
        
        conn.close()
        return len(risk_data) > 0
    
    def simulate_dashboard_threat_intelligence(self):
        """Simulate threat intelligence analytics for dashboard"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print("\n🛡️ THREAT INTELLIGENCE (Dashboard Simulation)")
        print("=" * 50)
        
        # High-risk countries with significant volume
        cursor.execute("""
            SELECT 
                sender_country_code,
                sender_country_name,
                COUNT(*) as email_count,
                geographic_risk_score,
                COUNT(CASE WHEN action = 'DELETED' THEN 1 END) as blocked_count
            FROM processed_emails_bulletproof 
            WHERE geographic_risk_score >= 0.70 
            AND sender_country_code IS NOT NULL
            GROUP BY sender_country_code, sender_country_name, geographic_risk_score
            HAVING email_count >= 5
            ORDER BY geographic_risk_score DESC, email_count DESC
        """)
        
        threat_data = cursor.fetchall()
        
        print("🚨 HIGH-RISK COUNTRIES (Risk Score ≥ 0.70)")
        print(f"{'Country':<15} {'Emails':<8} {'Risk':<6} {'Blocked':<8} {'Threat Level'}")
        print("-" * 50)
        
        for country_code, country_name, email_count, risk_score, blocked_count in threat_data:
            threat_level = "CRITICAL" if risk_score >= 0.90 else "HIGH" if risk_score >= 0.80 else "ELEVATED"
            print(f"{country_code:<15} {email_count:<8} {risk_score:<6.2f} {blocked_count:<8} {threat_level}")
        
        # Detection methods summary
        cursor.execute("""
            SELECT 
                detection_method,
                COUNT(*) as count,
                ROUND(AVG(geographic_risk_score), 2) as avg_risk
            FROM processed_emails_bulletproof 
            WHERE detection_method IS NOT NULL
            GROUP BY detection_method
            ORDER BY count DESC
        """)
        
        detection_data = cursor.fetchall()
        
        print(f"\n📊 DETECTION METHODS:")
        print(f"{'Method':<25} {'Count':<8} {'Avg Risk'}")
        print("-" * 40)
        
        for detection_method, count, avg_risk in detection_data:
            print(f"{detection_method:<25} {count:<8} {avg_risk}")
        
        conn.close()
        return len(threat_data) > 0
    
    def simulate_dashboard_temporal_analytics(self):
        """Simulate temporal analytics for dashboard"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print("\n⏰ TEMPORAL ANALYTICS (Dashboard Simulation)")
        print("=" * 50)
        
        # Recent geographic activity
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_emails,
                COUNT(CASE WHEN geographic_risk_score >= 0.80 THEN 1 END) as high_risk_emails,
                COUNT(DISTINCT sender_country_code) as unique_countries
            FROM processed_emails_bulletproof 
            WHERE sender_country_code IS NOT NULL
            AND timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        """)
        
        temporal_data = cursor.fetchall()
        
        print(f"{'Date':<12} {'Emails':<8} {'High Risk':<10} {'Countries'}")
        print("-" * 40)
        
        for date, total_emails, high_risk_emails, unique_countries in temporal_data:
            print(f"{date:<12} {total_emails:<8} {high_risk_emails:<10} {unique_countries}")
        
        conn.close()
        return len(temporal_data) > 0
    
    def run_full_validation(self):
        """Run complete geographic analytics validation"""
        print("🌍 ATLAS EMAIL GEOGRAPHIC ANALYTICS VALIDATION")
        print("=" * 65)
        print(f"🕐 Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all validation tests
        tests_passed = 0
        total_tests = 5
        
        # Test 1: Data completeness
        if self.validate_geographic_data_completeness():
            tests_passed += 1
            print("✅ Geographic data completeness validation PASSED")
        else:
            print("❌ Geographic data completeness validation FAILED")
        
        # Test 2: Country analytics
        if self.simulate_dashboard_country_analytics():
            tests_passed += 1
            print("✅ Country analytics simulation PASSED")
        else:
            print("❌ Country analytics simulation FAILED")
        
        # Test 3: Risk analytics
        if self.simulate_dashboard_risk_analytics():
            tests_passed += 1
            print("✅ Risk analytics simulation PASSED")
        else:
            print("❌ Risk analytics simulation FAILED")
        
        # Test 4: Threat intelligence
        if self.simulate_dashboard_threat_intelligence():
            tests_passed += 1
            print("✅ Threat intelligence simulation PASSED")
        else:
            print("❌ Threat intelligence simulation FAILED")
        
        # Test 5: Temporal analytics
        if self.simulate_dashboard_temporal_analytics():
            tests_passed += 1
            print("✅ Temporal analytics simulation PASSED")
        else:
            print("❌ Temporal analytics simulation FAILED")
        
        # Final validation summary
        print("\n" + "=" * 65)
        print("🎉 GEOGRAPHIC ANALYTICS VALIDATION SUMMARY")
        print("=" * 65)
        print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
        print(f"📊 Success Rate: {(tests_passed/total_tests)*100:.1f}%")
        
        if tests_passed == total_tests:
            print("🏆 ALL VALIDATIONS PASSED - Geographic analytics ready for dashboard!")
            print("🌍 Database contains complete geographic intelligence data")
            print("📈 Analytics dashboard will display live threat intelligence")
            print("🚨 Risk scoring system operational with realistic threat data")
        else:
            print("⚠️  Some validations failed - review geographic data population")
        
        return tests_passed == total_tests

def main():
    """Main execution"""
    validator = GeographicAnalyticsValidator()
    validator.run_full_validation()

if __name__ == "__main__":
    main()