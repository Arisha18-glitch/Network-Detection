"""
AI-Based Network Detection Engine
Implements rule-based detection techniques to identify patterns in network traffic behavior.
"""

import random
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import threading
import time

class NetworkDetectionEngine:
    def __init__(self, app=None):
        self.app = app
        self.detection_rules = {
            'ddos_threshold': 1000,  # packets per minute from single source
            'port_scan_threshold': 20,  # unique ports accessed from single source
            'unusual_traffic_multiplier': 5,  # times normal traffic volume
            'brute_force_threshold': 10,  # failed connections per minute
        }
        self.baseline_traffic = {}
        self.running = False
        self.detection_thread = None
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
    
    def start_detection(self):
        """Start the detection engine in a background thread"""
        if not self.running and self.app:
            self.running = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            self._log_system_event('INFO', 'Detection engine started', 'detection_engine')
    
    def stop_detection(self):
        """Stop the detection engine"""
        self.running = False
        if self.detection_thread:
            self.detection_thread.join()
        self._log_system_event('INFO', 'Detection engine stopped', 'detection_engine')
    
    def _detection_loop(self):
        """Main detection loop that runs continuously"""
        while self.running:
            try:
                # Import models within app context
                from src.models.alert import Alert
                from src.models.network_traffic import NetworkTraffic
                from src.models.system_log import SystemLog
                from src.database import db
                
                # Generate simulated network traffic data
                self._generate_simulated_traffic(db, NetworkTraffic)
                
                # Run detection algorithms
                self._detect_ddos_attacks(db, Alert, NetworkTraffic)
                self._detect_port_scans(db, Alert, NetworkTraffic)
                self._detect_unusual_traffic(db, Alert, NetworkTraffic)
                self._detect_brute_force_attempts(db, Alert, NetworkTraffic)
                
                # Sleep for a short interval before next detection cycle
                time.sleep(30)  # Run detection every 30 seconds
                
            except Exception as e:
                print(f"Detection loop error: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def _generate_simulated_traffic(self, db, NetworkTraffic):
        """Generate simulated network traffic data for demonstration"""
        try:
            # Generate normal traffic
            for _ in range(random.randint(10, 50)):
                source_ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
                dest_ip = f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}"
                
                traffic = NetworkTraffic(
                    source_ip=source_ip,
                    destination_ip=dest_ip,
                    bytes_sent=random.randint(100, 10000),
                    bytes_received=random.randint(100, 5000),
                    packet_count=random.randint(1, 100)
                )
                db.session.add(traffic)
            
            # Occasionally generate suspicious traffic patterns
            if random.random() < 0.1:  # 10% chance
                self._generate_suspicious_traffic(db, NetworkTraffic)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Failed to generate traffic data: {str(e)}")
    
    def _generate_suspicious_traffic(self, db, NetworkTraffic):
        """Generate suspicious traffic patterns for testing detection"""
        attack_type = random.choice(['ddos', 'port_scan', 'brute_force'])
        
        if attack_type == 'ddos':
            # Generate high-volume traffic from single source
            attacker_ip = f"203.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            target_ip = "192.168.1.100"
            
            for _ in range(random.randint(50, 200)):
                traffic = NetworkTraffic(
                    source_ip=attacker_ip,
                    destination_ip=target_ip,
                    bytes_sent=random.randint(64, 1500),
                    bytes_received=0,
                    packet_count=1
                )
                db.session.add(traffic)
        
        elif attack_type == 'port_scan':
            # Generate traffic to many different ports
            scanner_ip = f"185.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            target_ip = "192.168.1.50"
            
            for port in range(20, 100, 2):  # Scan multiple ports
                traffic = NetworkTraffic(
                    source_ip=scanner_ip,
                    destination_ip=target_ip,
                    bytes_sent=64,
                    bytes_received=0,
                    packet_count=1
                )
                db.session.add(traffic)
        
        elif attack_type == 'brute_force':
            # Generate repeated connection attempts
            attacker_ip = f"91.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            target_ip = "192.168.1.10"
            
            for _ in range(random.randint(15, 30)):
                traffic = NetworkTraffic(
                    source_ip=attacker_ip,
                    destination_ip=target_ip,
                    bytes_sent=random.randint(100, 500),
                    bytes_received=random.randint(50, 200),
                    packet_count=random.randint(1, 5)
                )
                db.session.add(traffic)
    
    def _detect_ddos_attacks(self, db, Alert, NetworkTraffic):
        """Detect potential DDoS attacks based on traffic volume"""
        try:
            # Look for high packet rates from single sources in the last 5 minutes
            since = datetime.utcnow() - timedelta(minutes=5)
            
            # Query for high-volume sources
            from sqlalchemy import func
            high_volume_sources = db.session.query(
                NetworkTraffic.source_ip,
                func.sum(NetworkTraffic.packet_count).label('total_packets'),
                func.count(NetworkTraffic.id).label('connection_count')
            ).filter(
                NetworkTraffic.timestamp >= since
            ).group_by(
                NetworkTraffic.source_ip
            ).having(
                func.sum(NetworkTraffic.packet_count) > self.detection_rules['ddos_threshold']
            ).all()
            
            for source in high_volume_sources:
                # Check if we already have a recent alert for this source
                existing_alert = Alert.query.filter(
                    Alert.source_ip == source.source_ip,
                    Alert.type == 'DDoS',
                    Alert.timestamp >= since,
                    Alert.status == 'Active'
                ).first()
                
                if not existing_alert:
                    self._create_alert(
                        db, Alert,
                        alert_type='DDoS',
                        source_ip=source.source_ip,
                        destination_ip='Multiple',
                        severity='High',
                        description=f'Potential DDoS attack detected from {source.source_ip}. '
                                   f'{source.total_packets} packets in 5 minutes.',
                        details={
                            'packet_count': source.total_packets,
                            'connection_count': source.connection_count,
                            'detection_rule': 'high_packet_rate',
                            'threshold': self.detection_rules['ddos_threshold']
                        }
                    )
        
        except Exception as e:
            print(f"DDoS detection error: {str(e)}")
    
    def _detect_port_scans(self, db, Alert, NetworkTraffic):
        """Detect potential port scanning activities"""
        try:
            # Look for sources connecting to many different destinations in short time
            since = datetime.utcnow() - timedelta(minutes=10)
            
            from sqlalchemy import func
            potential_scanners = db.session.query(
                NetworkTraffic.source_ip,
                func.count(func.distinct(NetworkTraffic.destination_ip)).label('unique_destinations'),
                func.count(NetworkTraffic.id).label('total_connections')
            ).filter(
                NetworkTraffic.timestamp >= since
            ).group_by(
                NetworkTraffic.source_ip
            ).having(
                func.count(func.distinct(NetworkTraffic.destination_ip)) > self.detection_rules['port_scan_threshold']
            ).all()
            
            for scanner in potential_scanners:
                existing_alert = Alert.query.filter(
                    Alert.source_ip == scanner.source_ip,
                    Alert.type == 'Port Scan',
                    Alert.timestamp >= since,
                    Alert.status == 'Active'
                ).first()
                
                if not existing_alert:
                    self._create_alert(
                        db, Alert,
                        alert_type='Port Scan',
                        source_ip=scanner.source_ip,
                        destination_ip='Multiple',
                        severity='Medium',
                        description=f'Potential port scan detected from {scanner.source_ip}. '
                                   f'Connected to {scanner.unique_destinations} unique destinations.',
                        details={
                            'unique_destinations': scanner.unique_destinations,
                            'total_connections': scanner.total_connections,
                            'detection_rule': 'multiple_destinations',
                            'threshold': self.detection_rules['port_scan_threshold']
                        }
                    )
        
        except Exception as e:
            print(f"Port scan detection error: {str(e)}")
    
    def _detect_unusual_traffic(self, db, Alert, NetworkTraffic):
        """Detect unusual traffic patterns based on baseline"""
        try:
            # Simple anomaly detection based on traffic volume
            since = datetime.utcnow() - timedelta(minutes=15)
            
            from sqlalchemy import func
            current_traffic = db.session.query(
                func.sum(NetworkTraffic.bytes_sent + NetworkTraffic.bytes_received).label('total_bytes')
            ).filter(NetworkTraffic.timestamp >= since).scalar() or 0
            
            # Use a simple baseline (in real implementation, this would be more sophisticated)
            baseline = 500000  # 500KB baseline for 15 minutes
            
            if current_traffic > baseline * self.detection_rules['unusual_traffic_multiplier']:
                # Check for existing alert
                existing_alert = Alert.query.filter(
                    Alert.type == 'Unusual Traffic',
                    Alert.timestamp >= since,
                    Alert.status == 'Active'
                ).first()
                
                if not existing_alert:
                    self._create_alert(
                        db, Alert,
                        alert_type='Unusual Traffic',
                        source_ip='Multiple',
                        destination_ip='Multiple',
                        severity='Medium',
                        description=f'Unusual traffic volume detected. Current: {current_traffic} bytes, '
                                   f'Expected: ~{baseline} bytes.',
                        details={
                            'current_bytes': current_traffic,
                            'baseline_bytes': baseline,
                            'multiplier': current_traffic / baseline if baseline > 0 else 0,
                            'detection_rule': 'traffic_volume_anomaly'
                        }
                    )
        
        except Exception as e:
            print(f"Unusual traffic detection error: {str(e)}")
    
    def _detect_brute_force_attempts(self, db, Alert, NetworkTraffic):
        """Detect potential brute force attacks"""
        try:
            # Look for repeated connection attempts to same destination
            since = datetime.utcnow() - timedelta(minutes=5)
            
            from sqlalchemy import func
            potential_brute_force = db.session.query(
                NetworkTraffic.source_ip,
                NetworkTraffic.destination_ip,
                func.count(NetworkTraffic.id).label('connection_attempts')
            ).filter(
                NetworkTraffic.timestamp >= since
            ).group_by(
                NetworkTraffic.source_ip,
                NetworkTraffic.destination_ip
            ).having(
                func.count(NetworkTraffic.id) > self.detection_rules['brute_force_threshold']
            ).all()
            
            for attempt in potential_brute_force:
                existing_alert = Alert.query.filter(
                    Alert.source_ip == attempt.source_ip,
                    Alert.destination_ip == attempt.destination_ip,
                    Alert.type == 'Brute Force',
                    Alert.timestamp >= since,
                    Alert.status == 'Active'
                ).first()
                
                if not existing_alert:
                    self._create_alert(
                        db, Alert,
                        alert_type='Brute Force',
                        source_ip=attempt.source_ip,
                        destination_ip=attempt.destination_ip,
                        severity='High',
                        description=f'Potential brute force attack from {attempt.source_ip} '
                                   f'to {attempt.destination_ip}. {attempt.connection_attempts} attempts in 5 minutes.',
                        details={
                            'connection_attempts': attempt.connection_attempts,
                            'detection_rule': 'repeated_connections',
                            'threshold': self.detection_rules['brute_force_threshold']
                        }
                    )
        
        except Exception as e:
            print(f"Brute force detection error: {str(e)}")
    
    def _create_alert(self, db, Alert, alert_type, source_ip, destination_ip, severity, description, details=None):
        """Create a new alert in the database"""
        try:
            alert = Alert(
                type=alert_type,
                source_ip=source_ip,
                destination_ip=destination_ip,
                severity=severity,
                description=description,
                details=json.dumps(details) if details else None
            )
            db.session.add(alert)
            db.session.commit()
            
            print(f'Alert created: {alert_type} from {source_ip}')
            
        except Exception as e:
            db.session.rollback()
            print(f"Failed to create alert: {str(e)}")
    
    def _log_system_event(self, level, message, component):
        """Log system events"""
        try:
            from src.models.system_log import SystemLog
            from src.database import db
            log = SystemLog(
                level=level,
                message=message,
                component=component
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"Failed to log system event: {e}")

# Global detection engine instance
detection_engine = NetworkDetectionEngine()

