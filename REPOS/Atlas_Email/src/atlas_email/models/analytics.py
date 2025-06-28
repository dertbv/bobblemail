#!/usr/bin/env python3
"""
Database Analytics Module
Advanced analytics and reporting using database queries instead of log file parsing
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
from .database import db
from ..utils.general import get_user_choice, format_number, format_percentage
from .db_logger import logger, LogCategory

class DatabaseAnalytics:
    """Advanced analytics engine using database queries"""
    
    def __init__(self):
        self.summary_stats = {}
        self.data_loaded = True  # Always true since we're using database
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics from database"""
        try:
            stats = {}
            
            # Basic session counts
            session_data = db.execute_query("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(total_deleted) as total_deletions,
                    SUM(total_preserved) as total_preservations,
                    SUM(total_validated) as total_validations,
                    MIN(start_time) as first_activity,
                    MAX(start_time) as last_activity
                FROM sessions
            """)[0]
            
            stats.update(dict(session_data))
            
            # Handle NULL values
            for key in ['total_deletions', 'total_preservations', 'total_validations']:
                stats[key] = stats[key] or 0
            
            # Domain statistics
            domain_stats = db.execute_query("""
                SELECT COUNT(*) as total_domains FROM domains
            """)[0]
            stats['total_domains_analyzed'] = domain_stats['total_domains']
            
            suspicious_domains = db.execute_query("""
                SELECT COUNT(*) as count FROM domains WHERE action_taken = 'DELETED'
            """)[0]
            stats['suspicious_domains'] = suspicious_domains['count']
            
            # Category statistics
            category_stats = db.execute_query("""
                SELECT COUNT(*) as total_categories FROM spam_categories WHERE is_active = TRUE
            """)[0]
            stats['total_categories'] = category_stats['total_categories']
            
            # Most common category
            top_category = db.execute_query("""
                SELECT category FROM spam_categories 
                WHERE is_active = TRUE 
                ORDER BY total_count DESC 
                LIMIT 1
            """)
            stats['most_common_category'] = top_category[0]['category'] if top_category else "None"
            
            # Calculate rates and averages
            total_processed = stats['total_deletions'] + stats['total_preservations']
            if total_processed > 0:
                stats['deletion_rate'] = (stats['total_deletions'] / total_processed) * 100
                stats['preservation_rate'] = (stats['total_preservations'] / total_processed) * 100
            else:
                stats['deletion_rate'] = 0
                stats['preservation_rate'] = 0
            
            if stats['total_sessions'] > 0:
                stats['avg_deletions_per_session'] = stats['total_deletions'] / stats['total_sessions']
                stats['avg_preservations_per_session'] = stats['total_preservations'] / stats['total_sessions']
            else:
                stats['avg_deletions_per_session'] = 0
                stats['avg_preservations_per_session'] = 0
            
            # Time calculations
            if stats['first_activity'] and stats['last_activity']:
                first = datetime.fromisoformat(stats['first_activity'])
                last = datetime.fromisoformat(stats['last_activity'])
                duration = (last - first).total_seconds()
                stats['total_duration_hours'] = duration / 3600
            else:
                stats['total_duration_hours'] = 0
            
            self.summary_stats = stats
            return stats
            
        except Exception as e:
            logger.error(e, "get_summary_stats")
            return {}
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get detailed processing statistics"""
        try:
            stats = self.get_summary_stats()
            
            # Recent activity (last 7 days)
            recent_stats = db.execute_query("""
                SELECT 
                    SUM(total_deleted) as recent_deletions,
                    SUM(total_preserved) as recent_preservations,
                    COUNT(*) as recent_sessions
                FROM sessions
                WHERE start_time > datetime('now', '-7 days')
            """)[0]
            
            stats['recent_deletions'] = recent_stats['recent_deletions'] or 0
            stats['recent_preservations'] = recent_stats['recent_preservations'] or 0
            stats['recent_sessions'] = recent_stats['recent_sessions'] or 0
            
            # Processing efficiency by time period
            daily_stats = db.execute_query("""
                SELECT 
                    DATE(start_time) as date,
                    SUM(total_deleted) as deleted,
                    SUM(total_preserved) as preserved,
                    COUNT(*) as sessions
                FROM sessions
                WHERE start_time > datetime('now', '-30 days')
                GROUP BY DATE(start_time)
                ORDER BY date DESC
            """)
            
            stats['daily_statistics'] = [dict(row) for row in daily_stats]
            
            return stats
            
        except Exception as e:
            logger.error(e, "get_processing_statistics")
            return {}
    
    def get_filter_effectiveness(self) -> Dict[str, Any]:
        """Analyze filter effectiveness by category"""
        try:
            # Get category statistics with deletion rates
            categories = db.execute_query("""
                SELECT 
                    sc.category,
                    sc.total_count,
                    sc.deletion_rate,
                    sc.first_seen,
                    sc.last_seen,
                    COUNT(DISTINCT pe.sender_domain) as unique_domains
                FROM spam_categories sc
                LEFT JOIN processed_emails_bulletproof pe ON pe.category = sc.category
                WHERE sc.is_active = TRUE
                GROUP BY sc.category
                ORDER BY sc.total_count DESC
            """)
            
            category_data = [dict(row) for row in categories]
            
            # Calculate total for percentages
            total_count = sum(cat['total_count'] for cat in category_data)
            
            # Add percentage calculations
            for category in category_data:
                if total_count > 0:
                    category['percentage'] = (category['total_count'] / total_count) * 100
                else:
                    category['percentage'] = 0
            
            # Get recent category trends (last 30 days)
            recent_categories = db.execute_query("""
                SELECT 
                    category,
                    COUNT(*) as recent_count
                FROM processed_emails_bulletproof
                WHERE timestamp > datetime('now', '-30 days')
                    AND category IS NOT NULL
                GROUP BY category
                ORDER BY recent_count DESC
            """)
            
            recent_data = {row['category']: row['recent_count'] for row in recent_categories}
            
            return {
                'categories': category_data,
                'total_count': total_count,
                'recent_activity': recent_data
            }
            
        except Exception as e:
            logger.error(e, "get_filter_effectiveness")
            return {'categories': [], 'total_count': 0, 'recent_activity': {}}
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account processing summary"""
        try:
            # Account activity summary
            account_stats = db.execute_query("""
                SELECT 
                    a.email_address,
                    a.provider,
                    COUNT(s.id) as session_count,
                    SUM(s.total_deleted) as total_deleted,
                    SUM(s.total_preserved) as total_preserved,
                    MAX(s.start_time) as last_session,
                    MIN(s.start_time) as first_session
                FROM accounts a
                LEFT JOIN sessions s ON a.id = s.account_id
                WHERE a.is_active = TRUE
                GROUP BY a.id, a.email_address, a.provider
                ORDER BY session_count DESC
            """)
            
            accounts = []
            for row in account_stats:
                account_data = dict(row)
                account_data['total_deleted'] = account_data['total_deleted'] or 0
                account_data['total_preserved'] = account_data['total_preserved'] or 0
                account_data['session_count'] = account_data['session_count'] or 0
                accounts.append(account_data)
            
            # Provider statistics
            provider_stats = db.execute_query("""
                SELECT 
                    a.provider,
                    COUNT(DISTINCT a.id) as account_count,
                    COUNT(s.id) as session_count,
                    SUM(s.total_deleted) as total_deleted
                FROM accounts a
                LEFT JOIN sessions s ON a.id = s.account_id
                WHERE a.is_active = TRUE
                GROUP BY a.provider
                ORDER BY account_count DESC
            """)
            
            providers = [dict(row) for row in provider_stats]
            
            return {
                'accounts': accounts,
                'providers': providers,
                'total_accounts': len(accounts)
            }
            
        except Exception as e:
            logger.error(e, "get_account_summary")
            return {'accounts': [], 'providers': [], 'total_accounts': 0}
    
    def get_domain_analysis(self) -> Dict[str, Any]:
        """Analyze domain statistics and suspicious patterns"""
        try:
            # Top suspicious domains
            suspicious_domains = db.execute_query("""
                SELECT 
                    domain,
                    total_occurrences,
                    risk_score,
                    action_taken,
                    first_seen,
                    last_seen,
                    ml_confidence_scores
                FROM domains
                WHERE action_taken = 'DELETED'
                ORDER BY total_occurrences DESC
                LIMIT 20
            """)
            
            suspicious_data = []
            for row in suspicious_domains:
                domain_data = dict(row)
                # Parse confidence scores
                if domain_data['ml_confidence_scores']:
                    scores = json.loads(domain_data['ml_confidence_scores'])
                    domain_data['avg_confidence'] = sum(scores) / len(scores) if scores else 0
                else:
                    domain_data['avg_confidence'] = 0
                suspicious_data.append(domain_data)
            
            # Domain statistics
            domain_summary = db.execute_query("""
                SELECT 
                    COUNT(*) as total_domains,
                    SUM(CASE WHEN action_taken = 'DELETED' THEN 1 ELSE 0 END) as flagged_domains,
                    SUM(CASE WHEN action_taken = 'PRESERVED' THEN 1 ELSE 0 END) as preserved_domains,
                    AVG(total_occurrences) as avg_occurrences,
                    AVG(risk_score) as avg_risk_score
                FROM domains
            """)[0]
            
            # Recent domain activity
            recent_domains = db.execute_query("""
                SELECT 
                    sender_domain,
                    COUNT(*) as count,
                    SUM(CASE WHEN action = 'DELETED' THEN 1 ELSE 0 END) as deleted
                FROM processed_emails_bulletproof
                WHERE timestamp > datetime('now', '-7 days')
                    AND sender_domain IS NOT NULL
                GROUP BY sender_domain
                ORDER BY count DESC
                LIMIT 10
            """)
            
            recent_data = [dict(row) for row in recent_domains]
            for domain in recent_data:
                if domain['count'] > 0:
                    domain['deletion_rate'] = (domain['deleted'] / domain['count']) * 100
                else:
                    domain['deletion_rate'] = 0
            
            return {
                'suspicious_domains': suspicious_data,
                'domain_summary': dict(domain_summary),
                'recent_activity': recent_data
            }
            
        except Exception as e:
            logger.error(e, "get_domain_analysis")
            return {'suspicious_domains': [], 'domain_summary': {}, 'recent_activity': []}
    
    def get_historical_trends(self) -> Dict[str, Any]:
        """Get historical trends and patterns"""
        try:
            # Daily activity for last 30 days
            daily_activity = db.execute_query("""
                SELECT 
                    DATE(start_time) as date,
                    COUNT(*) as sessions,
                    SUM(total_deleted) as deletions,
                    SUM(total_preserved) as preservations
                FROM sessions
                WHERE start_time > datetime('now', '-30 days')
                GROUP BY DATE(start_time)
                ORDER BY date DESC
            """)
            
            daily_data = []
            for row in daily_activity:
                day_data = dict(row)
                day_data['deletions'] = day_data['deletions'] or 0
                day_data['preservations'] = day_data['preservations'] or 0
                day_data['total_processed'] = day_data['deletions'] + day_data['preservations']
                daily_data.append(day_data)
            
            # Weekly trends
            weekly_trends = []
            if len(daily_data) >= 14:
                # Compare last 7 days to previous 7 days
                recent_week = daily_data[:7]
                previous_week = daily_data[7:14]
                
                recent_deletions = sum(d['deletions'] for d in recent_week)
                previous_deletions = sum(d['deletions'] for d in previous_week)
                
                if previous_deletions > 0:
                    change_percent = ((recent_deletions - previous_deletions) / previous_deletions) * 100
                    
                    if change_percent > 10:
                        trend = "⬆️ Increasing"
                    elif change_percent < -10:
                        trend = "⬇️ Decreasing"
                    else:
                        trend = "➡️ Stable"
                    
                    weekly_trends = {
                        'recent_week_deletions': recent_deletions,
                        'previous_week_deletions': previous_deletions,
                        'change_percent': change_percent,
                        'trend': trend
                    }
            
            # Peak activity analysis
            peak_analysis = db.execute_query("""
                SELECT 
                    strftime('%H', start_time) as hour,
                    COUNT(*) as session_count,
                    AVG(total_deleted) as avg_deleted
                FROM sessions
                WHERE start_time > datetime('now', '-30 days')
                GROUP BY strftime('%H', start_time)
                ORDER BY session_count DESC
            """)
            
            peak_hours = [dict(row) for row in peak_analysis]
            
            return {
                'daily_activity': daily_data,
                'weekly_trends': weekly_trends,
                'peak_hours': peak_hours
            }
            
        except Exception as e:
            logger.error(e, "get_historical_trends")
            return {'daily_activity': [], 'weekly_trends': {}, 'peak_hours': []}
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Analyze system performance metrics"""
        try:
            # Performance metrics summary
            perf_summary = db.execute_query("""
                SELECT 
                    operation_type,
                    COUNT(*) as operation_count,
                    AVG(duration_seconds) as avg_duration,
                    MIN(duration_seconds) as min_duration,
                    MAX(duration_seconds) as max_duration,
                    SUM(items_processed) as total_items,
                    AVG(items_processed / duration_seconds) as avg_throughput
                FROM performance_metrics
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY operation_type
                ORDER BY operation_count DESC
            """)
            
            performance_data = [dict(row) for row in perf_summary]
            
            # Session performance trends
            session_performance = db.execute_query("""
                SELECT 
                    s.id,
                    s.start_time,
                    s.end_time,
                    s.total_deleted + s.total_preserved as total_processed,
                    (julianday(s.end_time) - julianday(s.start_time)) * 24 * 3600 as duration_seconds
                FROM sessions s
                WHERE s.start_time > datetime('now', '-7 days')
                    AND s.end_time IS NOT NULL
                ORDER BY s.start_time DESC
            """)
            
            session_data = []
            for row in session_performance:
                session_perf = dict(row)
                if session_perf['duration_seconds'] and session_perf['duration_seconds'] > 0:
                    session_perf['emails_per_second'] = session_perf['total_processed'] / session_perf['duration_seconds']
                else:
                    session_perf['emails_per_second'] = 0
                session_data.append(session_perf)
            
            return {
                'operation_performance': performance_data,
                'session_performance': session_data[:20]  # Last 20 sessions
            }
            
        except Exception as e:
            logger.error(e, "get_performance_analysis")
            return {'operation_performance': [], 'session_performance': []}

class DatabaseAnalyticsMenu:
    """Interactive analytics menu using database queries"""
    
    def __init__(self):
        self.analytics = DatabaseAnalytics()
    
    def run(self):
        """Run interactive analytics menu"""
        print("\n📊 DATABASE ANALYTICS & REPORTING")
        print("=" * 50)
        print("✅ Database analytics engine loaded")
        
        while True:
            self._show_main_menu()
            choice = get_user_choice("Press a key (1-6, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '6', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._show_processing_statistics()
            elif choice == '2':
                self._show_filter_effectiveness()
            elif choice == '3':
                self._show_account_summary()
            elif choice == '4':
                self._show_domain_analysis()
            elif choice == '5':
                self._show_historical_trends()
            elif choice == '6':
                self._show_performance_analysis()
    
    def _show_main_menu(self):
        """Display main analytics menu"""
        stats = self.analytics.get_summary_stats()
        
        print("\n" + "=" * 60)
        print("📊 DATABASE ANALYTICS & REPORTING")
        print("=" * 60)
        
        if stats:
            first_activity = stats.get('first_activity')
            last_activity = stats.get('last_activity')
            
            if first_activity and last_activity:
                first_date = datetime.fromisoformat(first_activity).strftime('%Y-%m-%d')
                last_date = datetime.fromisoformat(last_activity).strftime('%Y-%m-%d')
                print(f"📅 Data Period: {first_date} to {last_date}")
            
            print(f"📈 Total Sessions: {format_number(stats.get('total_sessions', 0))}")
            print(f"🗑️ Total Deleted: {format_number(stats.get('total_deletions', 0))}")
            print(f"🛡️ Total Preserved: {format_number(stats.get('total_preservations', 0))}")
        
        print()
        print("1. 📈 Processing Statistics")
        print("2. 🎯 Filter Effectiveness Analysis")
        print("3. 📋 Account Summary")
        print("4. 📊 Domain Analysis")
        print("5. 📈 Historical Trends")
        print("6. ⚡ Performance Analysis")
        print("9. ⬅️  Back to Main Menu")
        print("=" * 60)
    
    def _show_processing_statistics(self):
        """Show processing statistics"""
        print("\n📈 PROCESSING STATISTICS")
        print("-" * 50)
        
        stats = self.analytics.get_processing_statistics()
        
        print(f"📊 Overall Statistics:")
        print(f"  • Total Sessions: {format_number(stats.get('total_sessions', 0))}")
        print(f"  • Emails Deleted: {format_number(stats.get('total_deletions', 0))}")
        print(f"  • Emails Preserved: {format_number(stats.get('total_preservations', 0))}")
        print(f"  • Domains Analyzed: {format_number(stats.get('total_domains_analyzed', 0))}")
        print(f"  • Spam Categories: {format_number(stats.get('total_categories', 0))}")
        
        deletion_rate = stats.get('deletion_rate', 0)
        preservation_rate = stats.get('preservation_rate', 0)
        print(f"\n📊 Processing Rates:")
        print(f"  • Deletion Rate: {deletion_rate:.1f}%")
        print(f"  • Preservation Rate: {preservation_rate:.1f}%")
        print(f"  • Avg Deletions/Session: {stats.get('avg_deletions_per_session', 0):.1f}")
        
        print(f"\n📅 Recent Activity (Last 7 Days):")
        print(f"  • Sessions: {format_number(stats.get('recent_sessions', 0))}")
        print(f"  • Deletions: {format_number(stats.get('recent_deletions', 0))}")
        print(f"  • Preservations: {format_number(stats.get('recent_preservations', 0))}")
        
        # Show daily trends if available
        daily_stats = stats.get('daily_statistics', [])[:7]  # Last 7 days
        if daily_stats:
            print(f"\n📈 Daily Trends:")
            print(f"{'Date':<12} {'Sessions':<10} {'Deleted':<10} {'Preserved':<10}")
            print("-" * 45)
            for day in daily_stats:
                date = day['date']
                sessions = day['sessions'] or 0
                deleted = day['deleted'] or 0
                preserved = day['preserved'] or 0
                print(f"{date:<12} {sessions:<10} {deleted:<10} {preserved:<10}")
        
        input("\nPress Enter to continue...")
    
    def _show_filter_effectiveness(self):
        """Show filter effectiveness analysis"""
        print("\n🎯 FILTER EFFECTIVENESS ANALYSIS")
        print("-" * 50)
        
        effectiveness = self.analytics.get_filter_effectiveness()
        categories = effectiveness.get('categories', [])
        total_count = effectiveness.get('total_count', 0)
        
        if not categories:
            print("No category data found in database")
            input("\nPress Enter to continue...")
            return
        
        print(f"📊 Category Performance (Total: {format_number(total_count)}):")
        print(f"{'Category':<25} {'Count':<10} {'%':<8} {'Del Rate':<10} {'Domains':<8}")
        print("-" * 70)
        
        for category in categories[:15]:  # Top 15 categories
            name = category['category'][:24]
            count = category['total_count']
            percentage = category['percentage']
            del_rate = (category['deletion_rate'] or 0) * 100
            domains = category['unique_domains'] or 0
            
            print(f"{name:<25} {count:<10,} {percentage:<7.1f}% {del_rate:<9.1f}% {domains:<8}")
        
        # Show recent activity
        recent_activity = effectiveness.get('recent_activity', {})
        if recent_activity:
            print(f"\n📅 Recent Activity (Last 30 Days):")
            sorted_recent = sorted(recent_activity.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_recent[:10]:
                print(f"  • {category}: {format_number(count)}")
        
        input("\nPress Enter to continue...")
    
    def _show_account_summary(self):
        """Show account summary"""
        print("\n📋 ACCOUNT SUMMARY")
        print("-" * 40)
        
        summary = self.analytics.get_account_summary()
        accounts = summary.get('accounts', [])
        providers = summary.get('providers', [])
        
        print(f"📊 Overview: {summary.get('total_accounts', 0)} active accounts")
        
        if providers:
            print(f"\n📈 By Provider:")
            for provider in providers:
                prov_name = provider['provider']
                account_count = provider['account_count'] or 0
                session_count = provider['session_count'] or 0
                total_deleted = provider['total_deleted'] or 0
                
                print(f"  • {prov_name}: {account_count} accounts, {session_count} sessions, {format_number(total_deleted)} deleted")
        
        if accounts:
            print(f"\n📋 Account Activity:")
            print(f"{'Email':<30} {'Provider':<10} {'Sessions':<10} {'Deleted':<10} {'Last Session':<12}")
            print("-" * 85)
            
            for account in accounts[:20]:  # Top 20 most active
                email = account['email_address'][:29]
                provider = account['provider'][:9]
                sessions = account['session_count']
                deleted = account['total_deleted']
                
                last_session = ""
                if account['last_session']:
                    last_session = datetime.fromisoformat(account['last_session']).strftime('%Y-%m-%d')
                
                print(f"{email:<30} {provider:<10} {sessions:<10} {deleted:<10,} {last_session:<12}")
        
        input("\nPress Enter to continue...")
    
    def _show_domain_analysis(self):
        """Show domain analysis"""
        print("\n📊 DOMAIN ANALYSIS")
        print("-" * 40)
        
        analysis = self.analytics.get_domain_analysis()
        summary = analysis.get('domain_summary', {})
        suspicious = analysis.get('suspicious_domains', [])
        recent = analysis.get('recent_activity', [])
        
        # Summary statistics
        total_domains = summary.get('total_domains', 0)
        flagged_domains = summary.get('flagged_domains', 0)
        preserved_domains = summary.get('preserved_domains', 0)
        
        print(f"📊 Domain Statistics:")
        print(f"  • Total Domains Analyzed: {format_number(total_domains)}")
        print(f"  • Flagged for Deletion: {format_number(flagged_domains)}")
        print(f"  • Preserved: {format_number(preserved_domains)}")
        print(f"  • Average Risk Score: {summary.get('avg_risk_score', 0):.2f}")
        
        # Top suspicious domains
        if suspicious:
            print(f"\n🚨 Top Suspicious Domains:")
            print(f"{'Domain':<30} {'Count':<8} {'Risk':<6} {'Confidence':<11}")
            print("-" * 60)
            
            for domain in suspicious[:15]:
                domain_name = domain['domain'][:29]
                count = domain['total_occurrences']
                risk = domain['risk_score'] or 0
                confidence = domain['avg_confidence']
                
                print(f"{domain_name:<30} {count:<8} {risk:<5.1f} {confidence:<10.1f}%")
        
        # Recent domain activity
        if recent:
            print(f"\n📅 Recent Domain Activity (Last 7 Days):")
            print(f"{'Domain':<30} {'Total':<8} {'Deleted':<8} {'Rate':<8}")
            print("-" * 55)
            
            for domain in recent[:10]:
                domain_name = domain['sender_domain'][:29]
                total = domain['count']
                deleted = domain['deleted']
                rate = domain['deletion_rate']
                
                print(f"{domain_name:<30} {total:<8} {deleted:<8} {rate:<7.1f}%")
        
        input("\nPress Enter to continue...")
    
    def _show_historical_trends(self):
        """Show historical trends"""
        print("\n📈 HISTORICAL TRENDS")
        print("-" * 40)
        
        trends = self.analytics.get_historical_trends()
        daily_activity = trends.get('daily_activity', [])
        weekly_trends = trends.get('weekly_trends', {})
        peak_hours = trends.get('peak_hours', [])
        
        # Recent daily activity
        if daily_activity:
            print(f"📅 Daily Activity (Last 14 Days):")
            print(f"{'Date':<12} {'Sessions':<10} {'Deleted':<10} {'Preserved':<10}")
            print("-" * 45)
            
            for day in daily_activity[:14]:
                date = day['date']
                sessions = day['sessions']
                deleted = day['deletions']
                preserved = day['preservations']
                
                print(f"{date:<12} {sessions:<10} {deleted:<10} {preserved:<10}")
        
        # Weekly trend analysis
        if weekly_trends:
            print(f"\n📊 Trend Analysis:")
            print(f"  • Last 7 days: {format_number(weekly_trends['recent_week_deletions'])} deletions")
            print(f"  • Previous 7 days: {format_number(weekly_trends['previous_week_deletions'])} deletions")
            print(f"  • Change: {weekly_trends['change_percent']:+.1f}%")
            print(f"  • Trend: {weekly_trends['trend']}")
        
        # Peak activity hours
        if peak_hours:
            print(f"\n⏰ Peak Activity Hours:")
            print(f"{'Hour':<6} {'Sessions':<10} {'Avg Deleted':<12}")
            print("-" * 30)
            
            for hour_data in peak_hours[:10]:
                hour = f"{hour_data['hour']}:00"
                sessions = hour_data['session_count']
                avg_deleted = hour_data['avg_deleted'] or 0
                
                print(f"{hour:<6} {sessions:<10} {avg_deleted:<11.1f}")
        
        input("\nPress Enter to continue...")
    
    def _show_performance_analysis(self):
        """Show performance analysis"""
        print("\n⚡ PERFORMANCE ANALYSIS")
        print("-" * 40)
        
        performance = self.analytics.get_performance_analysis()
        operation_perf = performance.get('operation_performance', [])
        session_perf = performance.get('session_performance', [])
        
        # Operation performance
        if operation_perf:
            print(f"🔧 Operation Performance (Last 7 Days):")
            print(f"{'Operation':<20} {'Count':<8} {'Avg Time':<10} {'Throughput':<12}")
            print("-" * 55)
            
            for op in operation_perf:
                operation = op['operation_type'][:19]
                count = op['operation_count']
                avg_time = op['avg_duration'] or 0
                throughput = op['avg_throughput'] or 0
                
                print(f"{operation:<20} {count:<8} {avg_time:<9.2f}s {throughput:<11.1f}/s")
        
        # Session performance
        if session_perf:
            print(f"\n📈 Session Performance (Recent Sessions):")
            print(f"{'Session ID':<12} {'Date':<12} {'Processed':<10} {'Duration':<10} {'Rate':<10}")
            print("-" * 65)
            
            for session in session_perf[:10]:
                session_id = session['id']
                start_date = datetime.fromisoformat(session['start_time']).strftime('%m-%d %H:%M')
                processed = session['total_processed']
                duration = session['duration_seconds'] or 0
                rate = session['emails_per_second']
                
                print(f"{session_id:<12} {start_date:<12} {processed:<10} {duration:<9.1f}s {rate:<9.1f}/s")
        
        input("\nPress Enter to continue...")

# User Analytics Functions for Web Interface

def get_user_contribution_stats() -> Dict[str, Any]:
    """Get overall user contribution statistics for web interface"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total emails user has seen/analyzed (from sessions with feedback)
            cursor.execute("""
                SELECT COUNT(DISTINCT peb.id) 
                FROM processed_emails_bulletproof peb
                JOIN sessions s ON peb.session_id = s.id
                WHERE s.id IN (
                    SELECT DISTINCT session_id FROM user_feedback WHERE session_id IS NOT NULL
                )
            """)
            emails_analyzed = cursor.fetchone()[0] or 0
            
            # Total feedback given
            cursor.execute("SELECT COUNT(*) FROM user_feedback")
            feedback_given = cursor.fetchone()[0] or 0
            
            # Total immediate deletions
            cursor.execute("SELECT COUNT(*) FROM immediate_deletions WHERE success = TRUE")
            emails_deleted = cursor.fetchone()[0] or 0
            
            # Calculate accuracy (correct feedback vs total feedback)
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN feedback_type = 'correct' THEN 1 ELSE 0 END) as correct,
                    COUNT(*) as total
                FROM user_feedback
            """)
            result = cursor.fetchone()
            correct, total = result[0] or 0, result[1] or 0
            accuracy = round((correct / total * 100), 1) if total > 0 else 100.0
            
            # Get recent activity (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM user_feedback 
                WHERE timestamp > datetime('now', '-7 days')
            """)
            recent_feedback = cursor.fetchone()[0] or 0
            
            return {
                "emails_analyzed": emails_analyzed,
                "feedback_given": feedback_given, 
                "emails_deleted": emails_deleted,
                "accuracy": accuracy,
                "recent_activity": recent_feedback
            }
            
    except Exception as e:
        logger.error(e, "get_user_contribution_stats")
        return {
            "emails_analyzed": 0,
            "feedback_given": 0,
            "emails_deleted": 0,
            "accuracy": 100.0,
            "recent_activity": 0
        }

def get_user_achievement_badges(stats: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate achievement badges based on user statistics"""
    badges = []
    
    # Email analysis badges
    if stats["emails_analyzed"] >= 1000:
        badges.append({"icon": "👑", "name": "Email Master", "desc": "Analyzed 1000+ emails"})
    elif stats["emails_analyzed"] >= 500:
        badges.append({"icon": "🏆", "name": "Email Expert", "desc": "Analyzed 500+ emails"})
    elif stats["emails_analyzed"] >= 100:
        badges.append({"icon": "🎯", "name": "Email Analyst", "desc": "Analyzed 100+ emails"})
    
    # Feedback badges
    if stats["feedback_given"] >= 100:
        badges.append({"icon": "💬", "name": "Feedback Champion", "desc": "Provided 100+ feedback"})
    elif stats["feedback_given"] >= 50:
        badges.append({"icon": "💭", "name": "Feedback Hero", "desc": "Provided 50+ feedback"})
    elif stats["feedback_given"] >= 10:
        badges.append({"icon": "💡", "name": "Feedback Helper", "desc": "Provided 10+ feedback"})
    
    # Accuracy badges
    if stats["accuracy"] >= 98 and stats["feedback_given"] >= 20:
        badges.append({"icon": "🎯", "name": "Accuracy Master", "desc": "98%+ accuracy with 20+ feedback"})
    elif stats["accuracy"] >= 95 and stats["feedback_given"] >= 10:
        badges.append({"icon": "🎪", "name": "Accuracy Pro", "desc": "95%+ accuracy with 10+ feedback"})
    
    # Action badges
    if stats["emails_deleted"] >= 100:
        badges.append({"icon": "🗑️", "name": "Cleanup Champion", "desc": "Deleted 100+ spam emails"})
    elif stats["emails_deleted"] >= 50:
        badges.append({"icon": "🧹", "name": "Spam Fighter", "desc": "Deleted 50+ spam emails"})
    elif stats["emails_deleted"] >= 10:
        badges.append({"icon": "⚡", "name": "Quick Cleaner", "desc": "Deleted 10+ spam emails"})
    
    # Recent activity badge
    if stats["recent_activity"] >= 5:
        badges.append({"icon": "🔥", "name": "Active User", "desc": "5+ feedback this week"})
    
    return badges

def get_user_milestones(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate next milestones for user progress"""
    
    # Email analysis milestones
    email_milestones = [100, 500, 1000, 2500, 5000]
    next_email_milestone = next((m for m in email_milestones if m > stats["emails_analyzed"]), 10000)
    
    # Feedback milestones  
    feedback_milestones = [10, 25, 50, 100, 250]
    next_feedback_milestone = next((m for m in feedback_milestones if m > stats["feedback_given"]), 500)
    
    # Deletion milestones
    deletion_milestones = [10, 50, 100, 250, 500]
    next_deletion_milestone = next((m for m in deletion_milestones if m > stats["emails_deleted"]), 1000)
    
    return {
        "next_email_milestone": next_email_milestone,
        "next_feedback_milestone": next_feedback_milestone,
        "next_deletion_milestone": next_deletion_milestone,
        "email_progress": (stats["emails_analyzed"] / next_email_milestone * 100),
        "feedback_progress": (stats["feedback_given"] / next_feedback_milestone * 100),
        "deletion_progress": (stats["emails_deleted"] / next_deletion_milestone * 100)
    }

def increment_analytics_counter(metric: str, amount: int = 1, session_date: str = None):
    """Increment specific analytics counter"""
    try:
        if session_date is None:
            session_date = datetime.now().strftime('%Y-%m-%d')
            
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get or create analytics record for today
            cursor.execute("""
                SELECT id FROM user_analytics WHERE session_date = ?
            """, (session_date,))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing record - separate queries for each metric (SQL injection safe)
                analytics_id = result[0]
                if metric == 'emails_analyzed':
                    cursor.execute("""
                        UPDATE user_analytics 
                        SET emails_analyzed = emails_analyzed + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (amount, analytics_id))
                elif metric == 'feedback_given':
                    cursor.execute("""
                        UPDATE user_analytics 
                        SET feedback_given = feedback_given + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (amount, analytics_id))
                elif metric == 'emails_deleted':
                    cursor.execute("""
                        UPDATE user_analytics 
                        SET emails_deleted = emails_deleted + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (amount, analytics_id))
                else:
                    raise ValueError(f"Invalid metric: {metric}. Valid metrics: emails_analyzed, feedback_given, emails_deleted")
            else:
                # Create new record - separate queries for each metric (SQL injection safe)
                if metric == 'emails_analyzed':
                    cursor.execute("""
                        INSERT INTO user_analytics (session_date, emails_analyzed, feedback_given, emails_deleted, updated_at)
                        VALUES (?, ?, 0, 0, CURRENT_TIMESTAMP)
                    """, (session_date, amount))
                elif metric == 'feedback_given':
                    cursor.execute("""
                        INSERT INTO user_analytics (session_date, emails_analyzed, feedback_given, emails_deleted, updated_at)
                        VALUES (?, 0, ?, 0, CURRENT_TIMESTAMP)
                    """, (session_date, amount))
                elif metric == 'emails_deleted':
                    cursor.execute("""
                        INSERT INTO user_analytics (session_date, emails_analyzed, feedback_given, emails_deleted, updated_at)
                        VALUES (?, 0, 0, ?, CURRENT_TIMESTAMP)
                    """, (session_date, amount))
                else:
                    raise ValueError(f"Invalid metric: {metric}. Valid metrics: emails_analyzed, feedback_given, emails_deleted")
            
            conn.commit()
            
    except Exception as e:
        logger.error(e, f"increment_analytics_counter({metric})")

def log_immediate_deletion(account_name: str, email_uid: str, success: bool = True, 
                          error_message: str = None, user_feedback_id: int = None,
                          provider: str = None, folder_name: str = None):
    """Log an immediate email deletion action"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO immediate_deletions 
                (account_name, email_uid, success, error_message, user_feedback_id, provider, folder_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (account_name, email_uid, success, error_message, user_feedback_id, provider, folder_name))
            
            conn.commit()
            
            # Increment counter if successful
            if success:
                increment_analytics_counter('emails_deleted')
                
    except Exception as e:
        logger.error(e, "log_immediate_deletion")

# Export main classes and functions
__all__ = [
    'DatabaseAnalytics',
    'DatabaseAnalyticsMenu',
    'get_user_contribution_stats',
    'get_user_achievement_badges', 
    'get_user_milestones',
    'increment_analytics_counter',
    'log_immediate_deletion'
]