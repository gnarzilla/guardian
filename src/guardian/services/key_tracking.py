# src/guardian/services/key_tracking.py
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import json
from typing import List, Dict, Optional, Tuple
from guardian.core import Service, Result

@dataclass
class KeyUsage:
    """Key usage information"""
    key_id: str
    last_used: datetime
    usage_count: int
    hosts: List[str]
    platforms: List[str]
    success_rate: float

@dataclass
class UsagePattern:
    """Key usage pattern information"""
    common_times: List[str]
    common_hosts: List[str]
    usage_frequency: Dict[str, int]  # day -> count
    average_daily_uses: float
    unusual_patterns: List[Dict]

class KeyTracker(Service):
    def __init__(self):
        super().__init__()
        self.db_path = self.config_dir / 'keytracking.db'
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with all necessary tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Basic key and usage tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS keys (
                    key_id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    last_used DATETIME,
                    total_uses INTEGER DEFAULT 0,
                    algorithm TEXT,
                    key_size INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS key_usage (
                    id INTEGER PRIMARY KEY,
                    key_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    host TEXT NOT NULL,
                    platform TEXT,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    FOREIGN KEY (key_id) REFERENCES keys(key_id)
                )
            """)
            
            # Alert tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY,
                    key_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    details TEXT,
                    recommendations TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (key_id) REFERENCES keys(key_id)
                )
            """)
            
            # Known hosts tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS known_hosts (
                    key_id TEXT NOT NULL,
                    host TEXT NOT NULL,
                    first_seen DATETIME NOT NULL,
                    last_seen DATETIME NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    PRIMARY KEY (key_id, host),
                    FOREIGN KEY (key_id) REFERENCES keys(key_id)
                )
            """)

    def _generate_key_id(self, key_path: Path) -> str:
        """Generate unique ID for a key"""
        import hashlib
        
        # Use public key fingerprint as ID
        result = subprocess.run(
            ['ssh-keygen', '-l', '-f', str(key_path)],
            capture_output=True,
            text=True
        )
        
        fingerprint = result.stdout.split()[1]
        return fingerprint

    def register_key(self, path: Path) -> Result:
        """Register a key for tracking"""
        try:
            # Generate unique key ID from public key
            key_id = self._generate_key_id(path)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO keys
                    (key_id, path, created_at)
                    VALUES (?, ?, ?)
                """, (key_id, str(path), datetime.now()))
                
            return self.create_result(
                True,
                "Key registered for tracking",
                {'key_id': key_id}
            )
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to register key: {str(e)}",
                error=e
            )

    def analyze_usage_patterns(self, key_path: Path, 
                             days: int = 30) -> Result:
        """Analyze key usage patterns"""
        try:
            key_id = self._generate_key_id(key_path)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get usage data for specified period
                usage_data = conn.execute("""
                    SELECT 
                        strftime('%H', timestamp) as hour,
                        strftime('%w', timestamp) as day_of_week,
                        host,
                        success
                    FROM key_usage
                    WHERE key_id = ?
                    AND timestamp > datetime('now', ?)
                """, (key_id, f'-{days} days')).fetchall()
                
                if not usage_data:
                    return self.create_result(
                        False,
                        "No usage data found for analysis"
                    )
                
                # Analyze timing patterns
                hour_counts = {}
                day_counts = {}
                host_counts = {}
                
                for usage in usage_data:
                    # Count by hour
                    hour = int(usage['hour'])
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                    
                    # Count by day
                    day = int(usage['day_of_week'])
                    day_counts[day] = day_counts.get(day, 0) + 1
                    
                    # Count by host
                    host = usage['host']
                    host_counts[host] = host_counts.get(host, 0) + 1
                
                # Find common patterns
                common_hours = [
                    hour for hour, count in hour_counts.items()
                    if count > len(usage_data) * 0.1  # More than 10% of uses
                ]
                
                common_hosts = [
                    host for host, count in host_counts.items()
                    if count > len(usage_data) * 0.1
                ]
                
                # Calculate average daily usage
                total_days = min(days, 
                               (datetime.now() - datetime.fromtimestamp(
                                   key_path.stat().st_mtime
                               )).days)
                avg_daily = len(usage_data) / total_days if total_days > 0 else 0
                
                # Detect unusual patterns
                unusual = []
                
                # Check for odd hours
                odd_hours = [
                    hour for hour, count in hour_counts.items()
                    if 0 <= hour <= 5 and count > 0
                ]
                if odd_hours:
                    unusual.append({
                        'type': 'odd_hours',
                        'details': {
                            'hours': odd_hours,
                            'count': sum(hour_counts[h] for h in odd_hours)
                        }
                    })
                
                # Check for sudden spikes
                for day in range(days):
                    date = datetime.now() - timedelta(days=day)
                    date_str = date.strftime('%Y-%m-%d')
                    
                    daily_count = conn.execute("""
                        SELECT COUNT(*) as count
                        FROM key_usage
                        WHERE key_id = ?
                        AND date(timestamp) = date(?)
                    """, (key_id, date_str)).fetchone()['count']
                    
                    if daily_count > avg_daily * 3:  # 3x normal usage
                        unusual.append({
                            'type': 'usage_spike',
                            'details': {
                                'date': date_str,
                                'count': daily_count,
                                'average': avg_daily
                            }
                        })
                
                pattern = UsagePattern(
                    common_times=[f"{h:02d}:00" for h in sorted(common_hours)],
                    common_hosts=common_hosts,
                    usage_frequency=day_counts,
                    average_daily_uses=avg_daily,
                    unusual_patterns=unusual
                )
                
                return self.create_result(
                    True,
                    "Usage patterns analyzed",
                    {'patterns': pattern.__dict__}
                )
                
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to analyze usage patterns: {str(e)}",
                error=e
            )

    def get_key_usage(self, key_path: Path) -> Result:
        """Get comprehensive key usage statistics"""
        try:
            key_id = self._generate_key_id(key_path)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get basic key info
                key_info = conn.execute("""
                    SELECT * FROM keys WHERE key_id = ?
                """, (key_id,)).fetchone()
                
                if not key_info:
                    return self.create_result(
                        False,
                        "Key not found in tracking database"
                    )
                
                # Get usage statistics
                stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_uses,
                        COUNT(DISTINCT host) as unique_hosts,
                        COUNT(DISTINCT platform) as unique_platforms,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                        MAX(timestamp) as last_used
                    FROM key_usage
                    WHERE key_id = ?
                """, (key_id,)).fetchone()
                
                # Get recent usage
                recent_uses = conn.execute("""
                    SELECT *
                    FROM key_usage
                    WHERE key_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (key_id,)).fetchall()
                
                # Get known hosts
                known_hosts = conn.execute("""
                    SELECT *
                    FROM known_hosts
                    WHERE key_id = ?
                    ORDER BY last_seen DESC
                """, (key_id,)).fetchall()
                
                return self.create_result(
                    True,
                    "Usage statistics retrieved",
                    {
                        'key_info': dict(key_info),
                        'stats': dict(stats),
                        'recent_uses': [dict(u) for u in recent_uses],
                        'known_hosts': [dict(h) for h in known_hosts]
                    }
                )
                
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to get usage statistics: {str(e)}",
                error=e
            )

    # Previous methods (record_usage, _check_for_alerts, etc.) remain the same

    def record_usage(self, key_path: Path, host: str, 
                    platform: Optional[str] = None,
                    success: bool = True,
                    details: Optional[Dict] = None) -> Result:
        """Record key usage and check for alerts"""
        try:
            key_id = self._generate_key_id(key_path)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Record usage
                conn.execute("""
                    INSERT INTO key_usage
                    (key_id, timestamp, host, platform, success, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    key_id,
                    datetime.now(),
                    host,
                    platform,
                    success,
                    json.dumps(details) if details else None
                ))
                
                # Update key stats
                conn.execute("""
                    UPDATE keys
                    SET last_used = ?, total_uses = total_uses + 1
                    WHERE key_id = ?
                """, (datetime.now(), key_id))
                
                # Check for suspicious patterns
                alerts = self._check_for_alerts(conn, key_id, host)
                
                # Store any alerts
                for alert in alerts:
                    conn.execute("""
                        INSERT INTO alerts
                        (key_id, level, message, timestamp, details, recommendations)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        key_id,
                        alert['level'],
                        alert['message'],
                        datetime.now(),
                        json.dumps(alert['details']),
                        json.dumps(alert['recommendations'])
                    ))
                
                if alerts:
                    self._notify_alerts(alerts)
            
            return self.create_result(True, "Usage recorded successfully")
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to record usage: {str(e)}",
                error=e
            )

    def _check_for_alerts(self, conn, key_id: str, current_host: str) -> List[Dict]:
        """Check for suspicious patterns"""
        alerts = []
        
        # Check for unusual hours
        hour = datetime.now().hour
        if 0 <= hour <= 5:
            alerts.append({
                'level': 'warning',
                'message': 'Key usage during unusual hours',
                'details': {
                    'hour': hour,
                    'host': current_host
                },
                'recommendations': [
                    'Verify if this access was intended',
                    'Consider restricting key usage hours'
                ]
            })
        
        # Check for rapid usage
        recent_uses = conn.execute("""
            SELECT COUNT(*) as count
            FROM key_usage
            WHERE key_id = ?
            AND timestamp > datetime('now', '-5 minutes')
        """, (key_id,)).fetchone()['count']
        
        if recent_uses > 5:
            alerts.append({
                'level': 'critical',
                'message': 'Unusually rapid key usage',
                'details': {
                    'uses_count': recent_uses,
                    'timeframe': '5 minutes'
                },
                'recommendations': [
                    'Check for automated processes',
                    'Verify no unauthorized access'
                ]
            })
        
        # Check for new hosts
        known_hosts = set(row['host'] for row in conn.execute("""
            SELECT DISTINCT host
            FROM key_usage
            WHERE key_id = ?
            AND timestamp < datetime('now', '-1 hour')
        """, (key_id,)))
        
        if current_host not in known_hosts:
            alerts.append({
                'level': 'warning',
                'message': 'Access from new location',
                'details': {
                    'new_host': current_host,
                    'known_hosts': list(known_hosts)
                },
                'recommendations': [
                    'Verify if this new access point is legitimate',
                    'Add to known hosts if authorized'
                ]
            })
        
        return alerts

    def _notify_alerts(self, alerts: List[Dict]):
        """Send notifications for alerts"""
        try:
            # Terminal notification
            console = Console()
            for alert in alerts:
                console.print(Panel(
                    "\n".join([
                        f"[bold red]Security Alert ({alert['level'].upper()})[/bold red]",
                        f"Message: {alert['message']}",
                        "",
                        "[bold]Details:[/bold]",
                        *[f"• {k}: {v}" for k, v in alert['details'].items()],
                        "",
                        "[bold]Recommendations:[/bold]",
                        *[f"• {r}" for r in alert['recommendations']]
                    ]),
                    title="Guardian Security Alert",
                    style="red"
                ))
            
            # System notification if available
            try:
                import notify2
                notify2.init('Guardian')
                for alert in alerts:
                    notification = notify2.Notification(
                        "Guardian Security Alert",
                        f"{alert['level'].upper()}: {alert['message']}"
                    )
                    notification.show()
            except ImportError:
                pass
                
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {e}")

    def get_alerts(self, key_path: Path, 
                  level: Optional[str] = None,
                  limit: int = 100) -> Result:
        """Get recent alerts for a key"""
        try:
            key_id = self._generate_key_id(key_path)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                    SELECT *
                    FROM alerts
                    WHERE key_id = ?
                """
                params = [key_id]
                
                if level:
                    query += " AND level = ?"
                    params.append(level)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                alerts = []
                for row in conn.execute(query, params):
                    alerts.append({
                        'level': row['level'],
                        'message': row['message'],
                        'timestamp': row['timestamp'],
                        'details': json.loads(row['details']),
                        'recommendations': json.loads(row['recommendations']),
                        'acknowledged': bool(row['acknowledged'])
                    })
                
                return self.create_result(
                    True,
                    f"Found {len(alerts)} alerts",
                    {'alerts': alerts}
                )
                
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to get alerts: {str(e)}",
                error=e
            )
