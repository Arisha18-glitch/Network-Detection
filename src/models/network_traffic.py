from src.database import db
from datetime import datetime

class NetworkTraffic(db.Model):
    __tablename__ = 'network_traffic'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    source_ip = db.Column(db.String(45), nullable=False)
    destination_ip = db.Column(db.String(45), nullable=False)
    bytes_sent = db.Column(db.BigInteger, nullable=False, default=0)
    bytes_received = db.Column(db.BigInteger, nullable=False, default=0)
    packet_count = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<NetworkTraffic {self.source_ip} -> {self.destination_ip} at {self.timestamp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'packet_count': self.packet_count
        }

