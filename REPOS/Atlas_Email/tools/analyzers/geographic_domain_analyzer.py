#!/usr/bin/env python3
"""
Geographic Domain Analyzer for Atlas Email
Investigates geographical registration patterns of spam domains
"""

import json
import sqlite3
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import time

class GeographicDomainAnalyzer:
    """Analyzes domain geographic patterns for spam classification enhancement"""
    
    def __init__(self, db_path: str = "data/mail_filter.db"):
        self.db_path = db_path
        self.geographic_patterns = {}
        self.spam_domains = set()
        self.legitimate_domains = set()
        
    def extract_domains_from_database(self) -> Dict[str, List[str]]:
        """Extract domains from Atlas_Email database by classification"""
        domain_classifications = {
            'spam': [],
            'legitimate': [],
            'phishing': [],
            'transactional': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract domains from sessions table with classifications
            cursor.execute("""
                SELECT sender, classification, COUNT(*) as frequency
                FROM sessions 
                WHERE sender IS NOT NULL AND sender != ''
                GROUP BY sender, classification
                ORDER BY frequency DESC
            """)
            
            for sender, classification, frequency in cursor.fetchall():
                domain = self._extract_domain_from_sender(sender)
                if domain:
                    if classification in ['SPAM', 'Financial Spam', 'Subscription Spam']:
                        domain_classifications['spam'].append(domain)
                        self.spam_domains.add(domain)
                    elif classification in ['LEGIT', 'Whitelisted']:
                        domain_classifications['legitimate'].append(domain)
                        self.legitimate_domains.add(domain)
                    elif classification == 'PHISHING':
                        domain_classifications['phishing'].append(domain)
                    elif classification == 'TRANSACTIONAL':
                        domain_classifications['transactional'].append(domain)
                        
            conn.close()
            return domain_classifications
            
        except Exception as e:
            print(f"❌ Database extraction error: {e}")
            return domain_classifications
    
    def _extract_domain_from_sender(self, sender: str) -> Optional[str]:
        """Extract domain from email sender"""
        if '@' in sender:
            return sender.split('@')[-1].strip('<>')
        return None
    
    def analyze_domain_geography(self, domain: str) -> Dict[str, str]:
        """Analyze geographic information for a domain using whois"""
        try:
            # Use whois command for domain information
            result = subprocess.run(['whois', domain], 
                                  capture_output=True, text=True, timeout=10)
            
            whois_data = result.stdout.lower()
            
            # Extract country information
            country_patterns = [
                r'country:\s*([a-z]{2})',
                r'registrant country:\s*([a-z]{2})',
                r'country code:\s*([a-z]{2})',
                r'country name:\s*([^\\n]+)',
            ]
            
            country = "Unknown"
            for pattern in country_patterns:
                match = re.search(pattern, whois_data)
                if match:
                    country = match.group(1).upper()
                    break
            
            # Extract registrar information
            registrar_patterns = [
                r'registrar:\s*([^\\n]+)',
                r'sponsoring registrar:\s*([^\\n]+)',
            ]
            
            registrar = "Unknown"
            for pattern in registrar_patterns:
                match = re.search(pattern, whois_data)
                if match:
                    registrar = match.group(1).strip()
                    break
            
            # Extract creation date
            date_patterns = [
                r'creation date:\s*([^\\n]+)',
                r'created:\s*([^\\n]+)',
                r'registered:\s*([^\\n]+)',
            ]
            
            creation_date = "Unknown"
            for pattern in date_patterns:
                match = re.search(pattern, whois_data)
                if match:
                    creation_date = match.group(1).strip()
                    break
            
            return {
                'domain': domain,
                'country': country,
                'registrar': registrar,
                'creation_date': creation_date,
                'analysis_date': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {'domain': domain, 'error': 'Whois timeout'}
        except Exception as e:
            return {'domain': domain, 'error': str(e)}
    
    def build_geographic_intelligence(self, sample_size: int = 50) -> Dict:
        """Build comprehensive geographic intelligence report"""
        print("🌍 Building Geographic Domain Intelligence...")
        
        # Extract domains from database
        domain_classifications = self.extract_domains_from_database()
        
        intelligence_report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_domains_analyzed': 0,
            'geographic_patterns': {
                'spam_countries': {},
                'legitimate_countries': {},
                'registrar_patterns': {},
                'age_patterns': {}
            },
            'domain_details': [],
            'insights': []
        }
        
        # Analyze spam domains
        spam_sample = list(set(domain_classifications['spam']))[:sample_size]
        legit_sample = list(set(domain_classifications['legitimate']))[:sample_size//2]
        
        print(f"🔍 Analyzing {len(spam_sample)} spam domains and {len(legit_sample)} legitimate domains...")
        
        all_domains = spam_sample + legit_sample
        
        for i, domain in enumerate(all_domains):
            if i % 5 == 0:
                print(f"⏳ Progress: {i}/{len(all_domains)} domains analyzed")
            
            geo_info = self.analyze_domain_geography(domain)
            geo_info['classification'] = 'spam' if domain in spam_sample else 'legitimate'
            
            intelligence_report['domain_details'].append(geo_info)
            
            # Update geographic patterns
            country = geo_info.get('country', 'Unknown')
            classification = geo_info['classification']
            
            if classification == 'spam':
                intelligence_report['geographic_patterns']['spam_countries'][country] = \
                    intelligence_report['geographic_patterns']['spam_countries'].get(country, 0) + 1
            else:
                intelligence_report['geographic_patterns']['legitimate_countries'][country] = \
                    intelligence_report['geographic_patterns']['legitimate_countries'].get(country, 0) + 1
            
            # Update registrar patterns
            registrar = geo_info.get('registrar', 'Unknown')
            if registrar not in intelligence_report['geographic_patterns']['registrar_patterns']:
                intelligence_report['geographic_patterns']['registrar_patterns'][registrar] = {'spam': 0, 'legitimate': 0}
            intelligence_report['geographic_patterns']['registrar_patterns'][registrar][classification] += 1
            
            # Rate limiting
            time.sleep(0.1)
        
        intelligence_report['total_domains_analyzed'] = len(all_domains)
        
        # Generate insights
        intelligence_report['insights'] = self._generate_geographic_insights(intelligence_report)
        
        return intelligence_report
    
    def _generate_geographic_insights(self, report: Dict) -> List[str]:
        """Generate actionable insights from geographic analysis"""
        insights = []
        
        spam_countries = report['geographic_patterns']['spam_countries']
        legit_countries = report['geographic_patterns']['legitimate_countries']
        
        # Top spam countries
        if spam_countries:
            top_spam_country = max(spam_countries.items(), key=lambda x: x[1])
            insights.append(f"🚨 Highest spam volume from: {top_spam_country[0]} ({top_spam_country[1]} domains)")
        
        # Country risk analysis
        for country in spam_countries:
            spam_count = spam_countries[country]
            legit_count = legit_countries.get(country, 0)
            total = spam_count + legit_count
            
            if total >= 3:  # Minimum sample size
                spam_ratio = spam_count / total
                if spam_ratio > 0.7:
                    insights.append(f"⚠️ High-risk country: {country} ({spam_ratio:.1%} spam ratio)")
                elif spam_ratio < 0.3:
                    insights.append(f"✅ Low-risk country: {country} ({spam_ratio:.1%} spam ratio)")
        
        # Registrar analysis
        registrar_patterns = report['geographic_patterns']['registrar_patterns']
        risky_registrars = []
        
        for registrar, counts in registrar_patterns.items():
            total = counts['spam'] + counts['legitimate']
            if total >= 3:
                spam_ratio = counts['spam'] / total
                if spam_ratio > 0.6:
                    risky_registrars.append((registrar, spam_ratio))
        
        if risky_registrars:
            insights.append(f"🎯 High-risk registrars identified: {len(risky_registrars)} registrars with >60% spam ratio")
        
        return insights
    
    def save_intelligence_report(self, report: Dict, filename: str = None) -> str:
        """Save geographic intelligence report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"geographic_intelligence_report_{timestamp}.json"
        
        filepath = f"tools/analyzers/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filepath


def main():
    """Main execution for geographic domain analysis"""
    print("🌍 ATLAS Email Geographic Domain Intelligence System")
    print("=" * 60)
    
    analyzer = GeographicDomainAnalyzer()
    
    # Build comprehensive intelligence
    intelligence_report = analyzer.build_geographic_intelligence(sample_size=30)
    
    # Save report
    report_path = analyzer.save_intelligence_report(intelligence_report)
    
    print("\\n📊 Geographic Intelligence Summary:")
    print(f"Total domains analyzed: {intelligence_report['total_domains_analyzed']}")
    print(f"Spam countries identified: {len(intelligence_report['geographic_patterns']['spam_countries'])}")
    print(f"Insights generated: {len(intelligence_report['insights'])}")
    
    print("\\n🧠 Key Insights:")
    for insight in intelligence_report['insights']:
        print(f"  {insight}")
    
    print(f"\\n💾 Full report saved to: {report_path}")
    
    return intelligence_report


if __name__ == "__main__":
    main()