#!/usr/bin/env python3
"""
Log Analyzer for AI Catch-up Scraping
Analyzes log files to provide insights and statistics
"""

import re
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict, Counter

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))


class LogAnalyzer:
    """Analyzes log files for insights and statistics."""
    
    def __init__(self, log_file: str = "scraping.log"):
        """Initialize log analyzer."""
        self.log_file = Path(log_file)
        self.entries = []
        self.parsed = False
    
    def parse_logs(self) -> bool:
        """Parse log file and extract entries."""
        if not self.log_file.exists():
            print(f"Log file not found: {self.log_file}")
            return False
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                entry = self._parse_log_line(line.strip())
                if entry:
                    self.entries.append(entry)
            
            self.parsed = True
            print(f"Parsed {len(self.entries)} log entries")
            return True
            
        except Exception as e:
            print(f"Error parsing log file: {e}")
            return False
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """Parse a single log line."""
        # Pattern: YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (\w+) - (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp_str, level, message = match.groups()
            
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                return {
                    'timestamp': timestamp,
                    'level': level,
                    'message': message,
                    'raw_line': line
                }
            except ValueError:
                pass
        
        return None
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics from logs."""
        if not self.parsed:
            return {}
        
        if not self.entries:
            return {'total_entries': 0}
        
        # Basic counts
        level_counts = Counter(entry['level'] for entry in self.entries)
        
        # Time range
        timestamps = [entry['timestamp'] for entry in self.entries]
        min_time = min(timestamps)
        max_time = max(timestamps)
        duration = max_time - min_time
        
        # URL processing stats
        processing_entries = [e for e in self.entries if 'Processing URL:' in e['message']]
        success_entries = [e for e in self.entries if 'SUCCESS:' in e['message']]
        error_entries = [e for e in self.entries if 'ERROR:' in e['message']]
        
        return {
            'total_entries': len(self.entries),
            'level_counts': dict(level_counts),
            'time_range': {
                'start': min_time,
                'end': max_time,
                'duration': str(duration)
            },
            'processing_stats': {
                'total_processed': len(processing_entries),
                'successful': len(success_entries),
                'errors': len(error_entries),
                'success_rate': len(success_entries) / len(processing_entries) if processing_entries else 0
            }
        }
    
    def get_error_analysis(self) -> Dict:
        """Analyze error patterns in logs."""
        if not self.parsed:
            return {}
        
        error_entries = [e for e in self.entries if e['level'] in ['ERROR', 'WARNING']]
        
        if not error_entries:
            return {'total_errors': 0}
        
        # Categorize errors
        error_categories = defaultdict(list)
        
        for entry in error_entries:
            message = entry['message']
            
            if 'HTTP' in message or 'connection' in message.lower():
                error_categories['Network'].append(entry)
            elif 'timeout' in message.lower():
                error_categories['Timeout'].append(entry)
            elif 'parse' in message.lower() or 'format' in message.lower():
                error_categories['Parsing'].append(entry)
            elif 'auth' in message.lower() or 'permission' in message.lower():
                error_categories['Authentication'].append(entry)
            elif 'validation' in message.lower():
                error_categories['Validation'].append(entry)
            else:
                error_categories['Other'].append(entry)
        
        # Count by category
        category_counts = {cat: len(entries) for cat, entries in error_categories.items()}
        
        # Recent errors (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = [e for e in error_entries if e['timestamp'] > one_hour_ago]
        
        return {
            'total_errors': len(error_entries),
            'error_categories': category_counts,
            'recent_errors': len(recent_errors),
            'error_rate_last_hour': len(recent_errors) / 60 if recent_errors else 0  # errors per minute
        }
    
    def get_url_performance(self) -> Dict:
        """Analyze URL processing performance."""
        if not self.parsed:
            return {}
        
        # Extract URL processing times
        url_stats = defaultdict(list)
        
        processing_pattern = r'Processing URL: (.+)'
        success_pattern = r'SUCCESS: (\d+) characters'
        
        current_url = None
        current_start_time = None
        
        for entry in self.entries:
            message = entry['message']
            
            # Start of URL processing
            proc_match = re.search(processing_pattern, message)
            if proc_match:
                current_url = proc_match.group(1)
                current_start_time = entry['timestamp']
                continue
            
            # End of URL processing (success)
            if current_url and 'SUCCESS:' in message:
                processing_time = (entry['timestamp'] - current_start_time).total_seconds()
                url_stats[current_url].append({
                    'timestamp': entry['timestamp'],
                    'processing_time': processing_time,
                    'success': True
                })
                current_url = None
                current_start_time = None
            
            # End of URL processing (error)
            elif current_url and entry['level'] == 'ERROR':
                processing_time = (entry['timestamp'] - current_start_time).total_seconds()
                url_stats[current_url].append({
                    'timestamp': entry['timestamp'],
                    'processing_time': processing_time,
                    'success': False
                })
                current_url = None
                current_start_time = None
        
        # Calculate averages
        if not url_stats:
            return {'no_data': True}
        
        all_times = []
        successful_times = []
        failed_times = []
        
        for url, attempts in url_stats.items():
            for attempt in attempts:
                all_times.append(attempt['processing_time'])
                if attempt['success']:
                    successful_times.append(attempt['processing_time'])
                else:
                    failed_times.append(attempt['processing_time'])
        
        return {
            'unique_urls': len(url_stats),
            'total_attempts': len(all_times),
            'average_processing_time': sum(all_times) / len(all_times) if all_times else 0,
            'average_success_time': sum(successful_times) / len(successful_times) if successful_times else 0,
            'average_failure_time': sum(failed_times) / len(failed_times) if failed_times else 0,
            'fastest_processing': min(all_times) if all_times else 0,
            'slowest_processing': max(all_times) if all_times else 0
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        if not self.parse_logs():
            return "Failed to parse log file"
        
        summary = self.get_summary_stats()
        errors = self.get_error_analysis()
        performance = self.get_url_performance()
        
        report = []
        report.append("=" * 60)
        report.append("LOG ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Log file: {self.log_file}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary Statistics
        report.append("📊 SUMMARY STATISTICS")
        report.append("-" * 30)
        report.append(f"Total log entries: {summary.get('total_entries', 0)}")
        
        if 'level_counts' in summary:
            for level, count in summary['level_counts'].items():
                report.append(f"{level}: {count}")
        
        if 'time_range' in summary:
            time_range = summary['time_range']
            report.append(f"Time range: {time_range['start']} to {time_range['end']}")
            report.append(f"Duration: {time_range['duration']}")
        
        if 'processing_stats' in summary:
            stats = summary['processing_stats']
            report.append(f"URLs processed: {stats['total_processed']}")
            report.append(f"Successful: {stats['successful']}")
            report.append(f"Errors: {stats['errors']}")
            report.append(f"Success rate: {stats['success_rate']:.1%}")
        
        report.append("")
        
        # Error Analysis
        report.append("❌ ERROR ANALYSIS")
        report.append("-" * 30)
        
        if errors.get('total_errors', 0) > 0:
            report.append(f"Total errors: {errors['total_errors']}")
            report.append(f"Recent errors (last hour): {errors['recent_errors']}")
            
            if 'error_categories' in errors:
                report.append("\nError categories:")
                for category, count in errors['error_categories'].items():
                    report.append(f"  {category}: {count}")
        else:
            report.append("No errors found")
        
        report.append("")
        
        # Performance Analysis
        report.append("⚡ PERFORMANCE ANALYSIS")
        report.append("-" * 30)
        
        if performance.get('no_data'):
            report.append("No performance data available")
        else:
            report.append(f"Unique URLs: {performance.get('unique_urls', 0)}")
            report.append(f"Total attempts: {performance.get('total_attempts', 0)}")
            report.append(f"Average processing time: {performance.get('average_processing_time', 0):.2f}s")
            report.append(f"Average success time: {performance.get('average_success_time', 0):.2f}s")
            report.append(f"Fastest processing: {performance.get('fastest_processing', 0):.2f}s")
            report.append(f"Slowest processing: {performance.get('slowest_processing', 0):.2f}s")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze AI Catch-up Scraping logs")
    parser.add_argument("--log-file", default="scraping.log", help="Path to log file")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer(args.log_file)
    report = analyzer.generate_report()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()