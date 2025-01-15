import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from .config import DB_PATH

class MemorySystem:
    def __init__(self):
        self.db_path = DB_PATH
        self.setup_database()

    def setup_database(self):
        """Initialize the database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    analysis TEXT,
                    decision TEXT,
                    reasoning TEXT,
                    action_details TEXT,
                    next_check TEXT,
                    action_result TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary_type TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly'
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    category TEXT,
                    metadata TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_timestamp 
                ON decisions(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_summaries_dates 
                ON memory_summaries(start_date, end_date)
            """)
    
    def store_decision(self, decision: Dict[str, Any]):
        """Store a decision in the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO decisions 
                (timestamp, analysis, decision, reasoning, action_details, next_check, action_result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                decision.get('analysis'),
                decision.get('decision'),
                decision.get('reasoning'),
                json.dumps(decision.get('action_details')),
                decision.get('next_check'),
                json.dumps(decision.get('action_result', {}))
            ))
    
    def get_recent_decisions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get decisions from the last N hours"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM decisions 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff,))
            
            return [{
                **dict(row),
                'action_details': json.loads(row['action_details']) if row['action_details'] else None,
                'action_result': json.loads(row['action_result']) if row['action_result'] else None
            } for row in cursor.fetchall()]
    
    def create_summary(self, summary_type: str, start_date: datetime, end_date: datetime):
        """Create a summary of decisions and actions for a time period"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM decisions 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start_date.isoformat(), end_date.isoformat()))
            
            decisions = cursor.fetchall()
            
            # Analysis of the period
            actions_taken = sum(1 for d in decisions if d['decision'] == 'Action')
            successful_actions = sum(1 for d in decisions 
                                  if d['action_result'] and 
                                  json.loads(d['action_result']).get('status') == 'success')
            
            summary = {
                'total_decisions': len(decisions),
                'actions_taken': actions_taken,
                'successful_actions': successful_actions,
                'key_events': self._extract_key_events(decisions),
                'period_analysis': self._analyze_period(decisions)
            }
            
            conn.execute("""
                INSERT INTO memory_summaries 
                (summary_type, start_date, end_date, summary, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                summary_type,
                start_date.isoformat(),
                end_date.isoformat(),
                json.dumps(summary),
                datetime.now().isoformat()
            ))
    
    def _extract_key_events(self, decisions: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """Extract important events from decisions"""
        key_events = []
        for decision in decisions:
            if decision['decision'] == 'Action':
                action_details = json.loads(decision['action_details']) if decision['action_details'] else {}
                action_result = json.loads(decision['action_result']) if decision['action_result'] else {}
                
                if action_result.get('status') == 'success':
                    key_events.append({
                        'timestamp': decision['timestamp'],
                        'type': 'action',
                        'details': action_details,
                        'result': action_result,
                        'importance': self._calculate_event_importance(decision)
                    })
        
        return sorted(key_events, key=lambda x: x['importance'], reverse=True)[:5]  # Top 5 most important events
    
    def _calculate_event_importance(self, decision: sqlite3.Row) -> float:
        """Calculate importance score for an event"""
        importance = 1.0
        
        # Actions are more important than no-actions
        if decision['decision'] == 'Action':
            importance *= 1.5
        
        # Successful actions are more important
        action_result = json.loads(decision['action_result']) if decision['action_result'] else {}
        if action_result.get('status') == 'success':
            importance *= 1.2
        
        return importance
    
    def _analyze_period(self, decisions: List[sqlite3.Row]) -> Dict[str, Any]:
        """Analyze a period of decisions for patterns and insights"""
        return {
            'common_actions': self._get_common_actions(decisions),
            'effectiveness': self._calculate_effectiveness(decisions),
            'patterns': self._identify_patterns(decisions)
        }
    
    def _get_common_actions(self, decisions: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """Analyze common actions taken"""
        action_counts = {}
        for decision in decisions:
            if decision['decision'] == 'Action':
                action_details = json.loads(decision['action_details']) if decision['action_details'] else {}
                tool = action_details.get('tool', 'unknown')
                action_counts[tool] = action_counts.get(tool, 0) + 1
        
        return [{'tool': tool, 'count': count} 
                for tool, count in sorted(action_counts.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True)]
    
    def _calculate_effectiveness(self, decisions: List[sqlite3.Row]) -> Dict[str, float]:
        """Calculate effectiveness metrics"""
        total_actions = 0
        successful_actions = 0
        tool_success = {}
        tool_attempts = {}
        
        for decision in decisions:
            if decision['decision'] == 'Action':
                total_actions += 1
                action_details = json.loads(decision['action_details']) if decision['action_details'] else {}
                action_result = json.loads(decision['action_result']) if decision['action_result'] else {}
                tool = action_details.get('tool', 'unknown')
                
                tool_attempts[tool] = tool_attempts.get(tool, 0) + 1
                if action_result.get('status') == 'success':
                    successful_actions += 1
                    tool_success[tool] = tool_success.get(tool, 0) + 1
        
        overall_success_rate = successful_actions / total_actions if total_actions > 0 else 0
        tool_success_rates = {
            tool: tool_success.get(tool, 0) / attempts
            for tool, attempts in tool_attempts.items()
        }
        
        return {
            'overall_success_rate': overall_success_rate,
            'tool_success_rates': tool_success_rates
        }
    
    def _identify_patterns(self, decisions: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """Identify patterns in decision making"""
        patterns = []
        
        # Time-based patterns
        hour_distribution = {}
        for decision in decisions:
            timestamp = datetime.fromisoformat(decision['timestamp'])
            hour = timestamp.hour
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        
        peak_hours = sorted(hour_distribution.items(), 
                          key=lambda x: x[1], 
                          reverse=True)[:3]
        
        patterns.append({
            'type': 'time_pattern',
            'description': f'Most active hours: {[hour for hour, _ in peak_hours]}',
            'details': {'peak_hours': peak_hours}
        })
        
        # Action sequence patterns
        action_sequences = []
        prev_action = None
        sequence_count = 0
        
        for decision in decisions:
            if decision['decision'] == 'Action':
                action_details = json.loads(decision['action_details']) if decision['action_details'] else {}
                current_action = action_details.get('tool')
                
                if current_action == prev_action:
                    sequence_count += 1
                else:
                    if sequence_count > 2:  # Pattern threshold
                        action_sequences.append({
                            'action': prev_action,
                            'count': sequence_count
                        })
                    sequence_count = 1
                    prev_action = current_action
        
        if action_sequences:
            patterns.append({
                'type': 'action_sequence',
                'description': 'Repeated action patterns detected',
                'details': {'sequences': action_sequences}
            })
        
        return patterns

    def get_relevant_context(self, current_situation: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant historical context for current situation"""
        current_time = current_situation.get('current_time', datetime.now())
        
        # Get recent decisions
        recent = self.get_recent_decisions(24)  # Last 24 hours
        
        # Get relevant summaries
        summaries = self.get_recent_summaries()
        
        # Get patterns
        patterns = self._identify_relevant_patterns(current_situation)
        
        # Get relevant notes
        notes = self.get_relevant_notes()
        
        return {
            'recent': recent,
            'summaries': summaries,
            'patterns': patterns,
            'notes': notes
        }
    
    def get_relevant_notes(self) -> List[Dict[str, Any]]:
        """Get relevant notes from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM notes 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                
                notes = []
                for row in cursor.fetchall():
                    note = dict(row)
                    if note['metadata']:
                        note['metadata'] = json.loads(note['metadata'])
                    notes.append(note)
                
                return notes
                
        except Exception as e:
            print(f"Error retrieving notes: {e}")
            return []

    def get_recent_summaries(self) -> List[Dict[str, Any]]:
        """Get recent summaries from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM memory_summaries
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                
                summaries = []
                for row in cursor.fetchall():
                    summary = dict(row)
                    summary['summary'] = json.loads(summary['summary'])
                    summaries.append(summary)
                
                return summaries
                
        except Exception as e:
            print(f"Error retrieving summaries: {e}")
            return []

    def _identify_relevant_patterns(self, current_situation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify patterns relevant to current situation"""
        current_time = current_situation.get('current_time', datetime.now())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get decisions from similar times of day
                hour_range_start = (current_time - timedelta(hours=1)).hour
                hour_range_end = (current_time + timedelta(hours=1)).hour
                
                cursor = conn.execute("""
                    SELECT * FROM decisions 
                    WHERE CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                    LIMIT 50
                """, (hour_range_start, hour_range_end))
                
                time_based_decisions = cursor.fetchall()
                
                patterns = []
                
                if time_based_decisions:
                    # Analyze success rates during this time period
                    success_rate = self._calculate_effectiveness(time_based_decisions)
                    patterns.append({
                        'type': 'time_effectiveness',
                        'description': f'Historical effectiveness during {current_time.hour}:00',
                        'details': success_rate
                    })
                    
                    # Analyze common actions during this time
                    common_actions = self._get_common_actions(time_based_decisions)
                    if common_actions:
                        patterns.append({
                            'type': 'time_based_actions',
                            'description': f'Common actions during this time of day',
                            'details': common_actions
                        })
                
                return patterns
                
        except Exception as e:
            print(f"Error identifying patterns: {e}")
            return []

    def cleanup_old_data(self, days: int = 30):
        """Clean up old data from the database"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete old decisions but keep their summaries
                conn.execute("DELETE FROM decisions WHERE timestamp < ?", (cutoff,))
                
                # Keep important notes
                conn.execute("""
                    DELETE FROM notes 
                    WHERE timestamp < ? 
                    AND category NOT IN ('important', 'milestone')
                """, (cutoff,))
                
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
