from src.database import db
from datetime import datetime
import json

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    type = db.Column(db.String(100), nullable=False)  # e.g., DDoS, Port Scan, Unusual Traffic
    source_ip = db.Column(db.String(45), nullable=False)  # IPv4 or IPv6
    destination_ip = db.Column(db.String(45), nullable=False)
    port = db.Column(db.Integer, nullable=True)
    protocol = db.Column(db.String(10), nullable=True)  # TCP, UDP, ICMP, etc.
    severity = db.Column(db.String(20), nullable=False, default='Medium')  # Low, Medium, High, Critical
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Active')  # Active, Acknowledged, Resolved
    details = db.Column(db.Text, nullable=True)  # JSON string for additional context

    def __repr__(self):
        return f'<Alert {self.id}: {self.type} from {self.source_ip}>'

    def to_dict(self):
        details_dict = {}
        if self.details:
            try:
                details_dict = json.loads(self.details)
            except json.JSONDecodeError:
                details_dict = {'raw': self.details}
        
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'type': self.type,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'port': self.port,
            'protocol': self.protocol,
            'severity': self.severity,
            'description': self.description,
            'status': self.status,
            'details': details_dict
        }

