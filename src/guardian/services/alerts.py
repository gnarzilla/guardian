# src/guardian/services/alerts.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import json
from guardian.core import Service, Result

@dataclass
class Alert:
    """Security alert information"""
    level: str  # 'info', 'warning', 'critical'
    message: str
    timestamp: datetime
    details: Dict
    recommendations: List[str]

class KeyAlertSystem(Service):
    """Alert system for SSH key usage"""
    
    def __init__(self):
        super().__init__()
        self.alert_history = self.config_dir / 'alerts.json'
        self._init_alert_store()
    
    def _init_alert_store(self):
        """Initialize alert storage"""
        if not self.alert_history.exists():
            self.alert_history.write_text('[]')
    
    def check_key_usage(self, key_path: Path, usage_data: Dict) -> Result:
        """Check for suspicious key usage patterns"""
        alerts = []
        
        # Check usage timing
        if timing_alert := self._check_timing(usage_data):
            alerts.append(timing_alert)
        
        # Check access patterns
        if pattern_alert := self._check_patterns(usage_data):
            alerts.append(pattern_alert)
        
        # Check locations
        if location_alert := self._check_locations(usage_data):
            alerts.append(location_alert)
        
        # Store alerts if any found
        if alerts:
            self._store_alerts(alerts)
            return self.create_result(
                True,
                "Security alerts detected",
                {'alerts': [a.__dict__ for a in alerts]}
            )
        
        return self.create_result(
            True,
            "No security concerns detected"
        )
    
    def _check_timing(self, usage_data: Dict) -> Optional[Alert]:
        """Check for suspicious timing patterns"""
        current_hour = datetime.now().hour
        
        # Night time usage (configurable)
        if 0 <= current_hour <= 5:
            return Alert(
                level='warning',
                message="Key usage during unusual hours",
                timestamp=datetime.now(),
                details={
                    'hour': current_hour,
                    'normal_hours': '6:00-23:00'
                },
                recommendations=[
                    "Verify if this access was intended",
                    "Consider restricting key usage hours if unexpected"
                ]
            )
        
        # Rapid successive uses
        recent_uses = [
            u for u in usage_data.get('recent_uses', [])
            if datetime.now() - u['timestamp'] < timedelta(minutes=5)
        ]
        if len(recent_uses) > 5:  # More than 5 uses in 5 minutes
            return Alert(
                level='critical',
                message="Unusually rapid key usage detected",
                timestamp=datetime.now(),
                details={
                    'uses_count': len(recent_uses),
                    'timeframe': '5 minutes'
                },
                recommendations=[
                    "Check for automated processes",
                    "Verify no unauthorized access attempts",
                    "Consider implementing rate limiting"
                ]
            )
        
        return None
    
    def _check_patterns(self, usage_data: Dict) -> Optional[Alert]:
        """Check for suspicious usage patterns"""
        # Check for failed attempts
        recent_failures = [
            u for u in usage_data.get('recent_uses', [])
            if not u.get('success', True)
        ]
        if len(recent_failures) >= 3:  # 3 or more failures
            return Alert(
                level='critical',
                message="Multiple authentication failures detected",
                timestamp=datetime.now(),
                details={
                    'failure_count': len(recent_failures),
                    'hosts': [f['host'] for f in recent_failures]
                },
                recommendations=[
                    "Check for potential brute force attempts",
                    "Verify key permissions",
                    "Consider temporarily disabling access if suspicious"
                ]
            )
        
        return None
    
    def _check_locations(self, usage_data: Dict) -> Optional[Alert]:
        """Check for suspicious access locations"""
        known_hosts = set(usage_data.get('known_hosts', []))
        current_host = usage_data.get('current_host')
        
        if current_host and current_host not in known_hosts:
            return Alert(
                level='warning',
                message="Access from new location detected",
                timestamp=datetime.now(),
                details={
                    'new_host': current_host,
                    'known_hosts': list(known_hosts)
                },
                recommendations=[
                    "Verify if this new access point is legitimate",
                    "Add to known hosts if authorized",
                    "Update access controls if unauthorized"
                ]
            )
        
        return None
    
    def _store_alerts(self, alerts: List[Alert]):
        """Store alerts in history"""
        try:
            existing = json.loads(self.alert_history.read_text())
        except:
            existing = []
        
        # Add new alerts
        existing.extend([
            {
                'level': alert.level,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'details': alert.details,
                'recommendations': alert.recommendations
            }
            for alert in alerts
        ])
        
        # Keep last 100 alerts
        existing = existing[-100:]
        self.alert_history.write_text(json.dumps(existing, indent=2))

class AlertNotifier(Service):
    """Handle alert notifications"""
    
    def notify(self, alert: Alert) -> Result:
        """Send alert notification"""
        # Terminal notification
        self.console.print(Panel(
            "\n".join([
                f"[bold red]Security Alert ({alert.level.upper()})[/bold red]",
                f"Message: {alert.message}",
                f"Time: {alert.timestamp}",
                "",
                "[bold]Details:[/bold]",
                *[f"• {k}: {v}" for k, v in alert.details.items()],
                "",
                "[bold]Recommendations:[/bold]",
                *[f"• {r}" for r in alert.recommendations]
            ]),
            title="Guardian Security Alert",
            style="red"
        ))
        
        # System notification (if available)
        try:
            import notify2
            notify2.init('Guardian')
            notification = notify2.Notification(
                "Guardian Security Alert",
                f"{alert.level.upper()}: {alert.message}"
            )
            notification.show()
        except ImportError:
            pass
        
        return self.create_result(True, "Alert notification sent")
