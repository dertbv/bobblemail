#!/usr/bin/env python3
"""
Learning Analytics Module
Analyzes classification failures, user feedback patterns, and system learning opportunities
"""

import sqlite3
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
from atlas_email.models.database import db


class LearningAnalytics:
    """
    Analyzes classification failures and learning patterns to improve system accuracy
    """
    
    def __init__(self):
        self.db = db
    
    def get_classification_failure_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze classification failures based on user feedback
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            Comprehensive analysis of classification failures
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get incorrect classifications (where user corrected the system)
            cursor.execute("""
                SELECT 
                    original_classification,
                    user_classification,
                    feedback_type,
                    sender,
                    subject,
                    timestamp,
                    confidence_rating,
                    user_comments
                FROM user_feedback 
                WHERE feedback_type IN ('incorrect', 'false_positive')
                AND timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff_date.isoformat(),))
            
            failures = cursor.fetchall()
            
            # Analyze failure patterns
            analysis = {
                'total_failures': len(failures),
                'failure_patterns': self._analyze_failure_patterns(failures),
                'misclassification_matrix': self._build_misclassification_matrix(failures),
                'common_failure_triggers': self._identify_failure_triggers(failures),
                'temporal_patterns': self._analyze_temporal_patterns(failures),
                'confidence_correlation': self._analyze_confidence_patterns(failures),
                'improvement_recommendations': []
            }
            
            # Generate improvement recommendations
            analysis['improvement_recommendations'] = self._generate_recommendations(analysis)
            
            return analysis
    
    def _analyze_failure_patterns(self, failures: List[sqlite3.Row]) -> Dict[str, Any]:
        """Analyze patterns in classification failures"""
        patterns = {
            'by_original_category': Counter(),
            'by_corrected_category': Counter(),
            'most_confused_pairs': Counter(),
            'sender_patterns': Counter(),
            'subject_patterns': []
        }
        
        for failure in failures:
            orig = failure['original_classification']
            corrected = failure['user_classification']
            
            patterns['by_original_category'][orig] += 1
            if corrected:
                patterns['by_corrected_category'][corrected] += 1
                patterns['most_confused_pairs'][(orig, corrected)] += 1
            
            # Extract sender domain patterns
            sender = failure['sender'] or ''
            if '@' in sender:
                domain = sender.split('@')[-1].lower()
                patterns['sender_patterns'][domain] += 1
            
            # Common subject patterns
            subject = failure['subject'] or ''
            if len(subject) > 10:
                patterns['subject_patterns'].append(subject[:50])
        
        # Convert Counters to dicts for JSON serialization
        patterns['by_original_category'] = dict(patterns['by_original_category'])
        patterns['by_corrected_category'] = dict(patterns['by_corrected_category'])
        patterns['most_confused_pairs'] = {f"{pair[0]} → {pair[1]}": count 
                                         for pair, count in patterns['most_confused_pairs'].items()}
        patterns['sender_patterns'] = dict(patterns['sender_patterns'].most_common(10))
        
        return patterns
    
    def _build_misclassification_matrix(self, failures: List[sqlite3.Row]) -> Dict[str, Dict[str, int]]:
        """Build confusion matrix for misclassifications"""
        matrix = defaultdict(lambda: defaultdict(int))
        
        for failure in failures:
            orig = failure['original_classification']
            corrected = failure['user_classification']
            
            if corrected:  # Only count when user provided a correction
                matrix[orig][corrected] += 1
        
        # Convert to regular dict for JSON serialization
        return {orig: dict(corrections) for orig, corrections in matrix.items()}
    
    def _identify_failure_triggers(self, failures: List[sqlite3.Row]) -> Dict[str, List[str]]:
        """Identify common triggers that lead to misclassification"""
        triggers = {
            'subject_keywords': [],
            'sender_patterns': [],
            'content_indicators': [],
            'domain_issues': []
        }
        
        for failure in failures:
            subject = (failure['subject'] or '').lower()
            sender = (failure['sender'] or '').lower()
            comments = (failure['user_comments'] or '').lower()
            
            # Extract potential trigger keywords from subjects
            subject_words = [word for word in subject.split() if len(word) > 3]
            triggers['subject_keywords'].extend(subject_words[:3])  # Top 3 words
            
            # Extract sender domain patterns
            if '@' in sender:
                domain = sender.split('@')[-1]
                triggers['domain_issues'].append(domain)
            
            # Extract insights from user comments
            if 'keyword' in comments or 'word' in comments:
                triggers['content_indicators'].append(comments[:100])
        
        # Remove duplicates and limit results
        for key in triggers:
            if key in ['subject_keywords', 'domain_issues']:
                triggers[key] = list(set(triggers[key]))[:10]
            else:
                triggers[key] = triggers[key][:5]
        
        return triggers
    
    def _analyze_temporal_patterns(self, failures: List[sqlite3.Row]) -> Dict[str, Any]:
        """Analyze when failures occur most frequently"""
        temporal = {
            'by_hour': defaultdict(int),
            'by_day_of_week': defaultdict(int),
            'by_date': defaultdict(int),
            'trends': {}
        }
        
        for failure in failures:
            timestamp = datetime.fromisoformat(failure['timestamp'].replace('Z', ''))
            
            temporal['by_hour'][timestamp.hour] += 1
            temporal['by_day_of_week'][timestamp.strftime('%A')] += 1
            temporal['by_date'][timestamp.strftime('%Y-%m-%d')] += 1
        
        # Convert to regular dicts
        temporal['by_hour'] = dict(temporal['by_hour'])
        temporal['by_day_of_week'] = dict(temporal['by_day_of_week'])
        temporal['by_date'] = dict(temporal['by_date'])
        
        # Identify trends
        if len(temporal['by_date']) > 7:
            dates = sorted(temporal['by_date'].keys())
            recent_avg = sum(temporal['by_date'][d] for d in dates[-7:]) / 7
            older_avg = sum(temporal['by_date'][d] for d in dates[:-7]) / len(dates[:-7]) if len(dates) > 7 else 0
            
            temporal['trends']['recent_vs_older'] = {
                'recent_7d_avg': recent_avg,
                'older_avg': older_avg,
                'trend': 'increasing' if recent_avg > older_avg else 'decreasing'
            }
        
        return temporal
    
    def _analyze_confidence_patterns(self, failures: List[sqlite3.Row]) -> Dict[str, Any]:
        """Analyze relationship between confidence ratings and failures"""
        confidence_data = {
            'distribution': defaultdict(int),
            'by_category': defaultdict(list),
            'average_confidence': 0,
            'insights': []
        }
        
        ratings = []
        for failure in failures:
            rating = failure['confidence_rating']
            if rating:
                ratings.append(rating)
                confidence_data['distribution'][rating] += 1
                confidence_data['by_category'][failure['original_classification']].append(rating)
        
        if ratings:
            confidence_data['average_confidence'] = sum(ratings) / len(ratings)
            
            # Generate insights
            if confidence_data['average_confidence'] < 3:
                confidence_data['insights'].append("Users have low confidence in failed classifications")
            
            low_confidence_failures = sum(1 for r in ratings if r <= 2)
            if low_confidence_failures > len(ratings) * 0.4:
                confidence_data['insights'].append("40%+ of failures involve low user confidence")
        
        # Convert defaultdict to dict
        confidence_data['distribution'] = dict(confidence_data['distribution'])
        confidence_data['by_category'] = {cat: sum(ratings)/len(ratings) if ratings else 0 
                                        for cat, ratings in confidence_data['by_category'].items()}
        
        return confidence_data
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Check for high-failure categories
        failure_patterns = analysis['failure_patterns']
        most_failed = failure_patterns['by_original_category']
        
        if most_failed:
            top_failed_category = max(most_failed, key=most_failed.get)
            failure_count = most_failed[top_failed_category]
            
            if failure_count > 5:
                recommendations.append(
                    f"Review '{top_failed_category}' classification rules - {failure_count} failures detected"
                )
        
        # Check confusion pairs
        confused_pairs = failure_patterns['most_confused_pairs']
        if confused_pairs:
            top_confusion = max(confused_pairs, key=confused_pairs.get)
            recommendations.append(
                f"Improve distinction between {top_confusion} - most common confusion pair"
            )
        
        # Check sender patterns
        sender_patterns = failure_patterns['sender_patterns']
        if sender_patterns:
            top_domain = max(sender_patterns, key=sender_patterns.get)
            recommendations.append(
                f"Review domain handling for '{top_domain}' - frequent in failures"
            )
        
        # Check confidence correlation
        confidence = analysis['confidence_correlation']
        if confidence['average_confidence'] < 2.5:
            recommendations.append(
                "Low user confidence detected - review classification clarity and accuracy"
            )
        
        # Check temporal patterns
        temporal = analysis['temporal_patterns']
        if 'trends' in temporal and temporal['trends']:
            trend_info = temporal['trends'].get('recent_vs_older', {})
            if trend_info.get('trend') == 'increasing':
                recommendations.append(
                    "Failure rate increasing - system may need retraining or rule updates"
                )
        
        return recommendations
    
    def get_learning_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Identify specific learning opportunities from user feedback
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of learning opportunities with context
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get unprocessed feedback with rich context
            cursor.execute("""
                SELECT 
                    id,
                    email_uid,
                    sender,
                    subject,
                    original_classification,
                    user_classification,
                    feedback_type,
                    confidence_rating,
                    user_comments,
                    timestamp
                FROM user_feedback 
                WHERE processed = FALSE
                AND feedback_type IN ('incorrect', 'false_positive')
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            opportunities = []
            
            for row in cursor.fetchall():
                opportunity = {
                    'id': row['id'],
                    'email_uid': row['email_uid'],
                    'sender': row['sender'],
                    'subject': row['subject'],
                    'original_classification': row['original_classification'],
                    'user_classification': row['user_classification'],
                    'feedback_type': row['feedback_type'],
                    'confidence_rating': row['confidence_rating'],
                    'user_comments': row['user_comments'],
                    'timestamp': row['timestamp'],
                    'learning_potential': self._assess_learning_potential(row),
                    'suggested_actions': self._suggest_learning_actions(row)
                }
                
                opportunities.append(opportunity)
            
            return opportunities
    
    def _assess_learning_potential(self, feedback: sqlite3.Row) -> str:
        """Assess the learning potential of a feedback item"""
        # High potential: Clear correction with high confidence
        if (feedback['user_classification'] and 
            feedback['confidence_rating'] and 
            feedback['confidence_rating'] >= 4):
            return "HIGH"
        
        # Medium potential: Has correction or detailed comments
        if feedback['user_classification'] or (feedback['user_comments'] and len(feedback['user_comments']) > 20):
            return "MEDIUM"
        
        # Low potential: Minimal information
        return "LOW"
    
    def _suggest_learning_actions(self, feedback: sqlite3.Row) -> List[str]:
        """Suggest specific learning actions for a feedback item"""
        actions = []
        
        original = feedback['original_classification']
        corrected = feedback['user_classification']
        comments = feedback['user_comments'] or ''
        
        # Keyword extraction suggestions
        if 'keyword' in comments.lower() or 'word' in comments.lower():
            actions.append("Extract and analyze mentioned keywords")
        
        # Rule refinement suggestions
        if corrected and corrected != original:
            actions.append(f"Refine rules to better distinguish {original} from {corrected}")
        
        # Domain analysis suggestions
        sender = feedback['sender'] or ''
        if '@' in sender:
            domain = sender.split('@')[-1]
            actions.append(f"Analyze domain '{domain}' classification patterns")
        
        # Subject pattern analysis
        subject = feedback['subject'] or ''
        if len(subject) > 10:
            actions.append("Analyze subject line patterns for similar emails")
        
        # False positive handling
        if feedback['feedback_type'] == 'false_positive':
            actions.append("Add protection patterns to prevent similar false positives")
        
        return actions
    
    def generate_learning_report(self, days: int = 30) -> str:
        """
        Generate a comprehensive learning analytics report
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Formatted report string
        """
        analysis = self.get_classification_failure_analysis(days)
        opportunities = self.get_learning_opportunities(10)
        
        report_lines = [
            f"🧠 LEARNING ANALYTICS REPORT ({days} days)",
            "=" * 50,
            "",
            f"📊 FAILURE SUMMARY:",
            f"   Total Classification Failures: {analysis['total_failures']}",
            f"   Average User Confidence: {analysis['confidence_correlation']['average_confidence']:.1f}/5",
            "",
            "🎯 TOP PROBLEM CATEGORIES:",
        ]
        
        # Add top failing categories
        top_failures = analysis['failure_patterns']['by_original_category']
        for category, count in sorted(top_failures.items(), key=lambda x: x[1], reverse=True)[:5]:
            report_lines.append(f"   • {category}: {count} failures")
        
        report_lines.extend([
            "",
            "🔄 MOST CONFUSED CLASSIFICATION PAIRS:",
        ])
        
        # Add confusion pairs
        confused_pairs = analysis['failure_patterns']['most_confused_pairs']
        for pair, count in sorted(confused_pairs.items(), key=lambda x: x[1], reverse=True)[:3]:
            report_lines.append(f"   • {pair}: {count} times")
        
        report_lines.extend([
            "",
            "💡 RECOMMENDATIONS:",
        ])
        
        # Add recommendations
        for i, rec in enumerate(analysis['improvement_recommendations'], 1):
            report_lines.append(f"   {i}. {rec}")
        
        report_lines.extend([
            "",
            f"🎓 LEARNING OPPORTUNITIES ({len(opportunities)} unprocessed):",
        ])
        
        # Add top learning opportunities
        for opp in opportunities[:5]:
            potential = opp['learning_potential']
            emoji = "🔥" if potential == "HIGH" else "📈" if potential == "MEDIUM" else "📊"
            report_lines.append(f"   {emoji} {opp['original_classification']} → {opp['user_classification'] or 'Corrected'}")
            if opp['suggested_actions']:
                report_lines.append(f"      Action: {opp['suggested_actions'][0]}")
        
        return "\n".join(report_lines)
    
    def export_learning_data(self, filepath: str, days: int = 30):
        """
        Export learning analytics data to JSON file
        
        Args:
            filepath: Output filepath
            days: Number of days to analyze
        """
        data = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period_days': days,
            'failure_analysis': self.get_classification_failure_analysis(days),
            'learning_opportunities': self.get_learning_opportunities(50)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"📊 Learning analytics data exported to {filepath}")


def main():
    """CLI interface for learning analytics"""
    analytics = LearningAnalytics()
    
    print("🧠 Email Filter Learning Analytics")
    print("=" * 40)
    
    # Generate and display report
    report = analytics.generate_learning_report(30)
    print(report)
    
    # Offer to export data
    export_choice = input("\n📤 Export detailed data to JSON? (y/n): ").strip().lower()
    if export_choice == 'y':
        filename = f"learning_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analytics.export_learning_data(filename, 30)


if __name__ == "__main__":
    main()