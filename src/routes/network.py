from flask import Blueprint, jsonify, request
from src.models.network_traffic import NetworkTraffic
from src.models.alert import Alert
from src.database import db
from datetime import datetime, timedelta
from sqlalchemy import func

network_bp = Blueprint('network', __name__)

@network_bp.route('/network/traffic', methods=['GET'])
def get_network_traffic():
    """Get aggregated network traffic data for visualization"""
    try:
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        interval_minutes = request.args.get('interval', 60, type=int)  # Default 1 hour intervals
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Aggregate traffic data by time intervals
        traffic_data = db.session.query(
            func.strftime('%Y-%m-%d %H:00:00', NetworkTraffic.timestamp).label('time_bucket'),
            func.sum(NetworkTraffic.bytes_sent).label('total_bytes_sent'),
            func.sum(NetworkTraffic.bytes_received).label('total_bytes_received'),
            func.sum(NetworkTraffic.packet_count).label('total_packets'),
            func.count(NetworkTraffic.id).label('connection_count')
        ).filter(
            NetworkTraffic.timestamp >= since
        ).group_by(
            func.strftime('%Y-%m-%d %H:00:00', NetworkTraffic.timestamp)
        ).order_by('time_bucket').all()
        
        # Format the data for frontend consumption
        formatted_data = []
        for row in traffic_data:
            formatted_data.append({
                'timestamp': row.time_bucket,
                'bytes_sent': row.total_bytes_sent or 0,
                'bytes_received': row.total_bytes_received or 0,
                'total_bytes': (row.total_bytes_sent or 0) + (row.total_bytes_received or 0),
                'packet_count': row.total_packets or 0,
                'connection_count': row.connection_count or 0
            })
        
        return jsonify({
            'success': True,
            'traffic_data': formatted_data,
            'timeframe_hours': hours,
            'interval_minutes': interval_minutes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@network_bp.route('/network/anomalies', methods=['GET'])
def get_network_anomalies():
    """Get detected network anomalies (alerts related to network traffic)"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get alerts that are network-related anomalies
        anomaly_types = ['DDoS', 'Port Scan', 'Unusual Traffic', 'Brute Force', 'Malware Communication']
        
        anomalies = Alert.query.filter(
            Alert.timestamp >= since,
            Alert.type.in_(anomaly_types)
        ).order_by(Alert.timestamp.desc()).all()
        
        return jsonify({
            'success': True,
            'anomalies': [alert.to_dict() for alert in anomalies],
            'count': len(anomalies),
            'timeframe_hours': hours
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@network_bp.route('/network/top-sources', methods=['GET'])
def get_top_sources():
    """Get top source IPs by traffic volume"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 10, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        top_sources = db.session.query(
            NetworkTraffic.source_ip,
            func.sum(NetworkTraffic.bytes_sent + NetworkTraffic.bytes_received).label('total_bytes'),
            func.sum(NetworkTraffic.packet_count).label('total_packets'),
            func.count(NetworkTraffic.id).label('connection_count')
        ).filter(
            NetworkTraffic.timestamp >= since
        ).group_by(
            NetworkTraffic.source_ip
        ).order_by(
            func.sum(NetworkTraffic.bytes_sent + NetworkTraffic.bytes_received).desc()
        ).limit(limit).all()
        
        formatted_data = []
        for row in top_sources:
            formatted_data.append({
                'source_ip': row.source_ip,
                'total_bytes': row.total_bytes or 0,
                'total_packets': row.total_packets or 0,
                'connection_count': row.connection_count or 0
            })
        
        return jsonify({
            'success': True,
            'top_sources': formatted_data,
            'timeframe_hours': hours,
            'limit': limit
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@network_bp.route('/network/stats', methods=['GET'])
def get_network_stats():
    """Get overall network statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get traffic statistics
        traffic_stats = db.session.query(
            func.sum(NetworkTraffic.bytes_sent).label('total_bytes_sent'),
            func.sum(NetworkTraffic.bytes_received).label('total_bytes_received'),
            func.sum(NetworkTraffic.packet_count).label('total_packets'),
            func.count(NetworkTraffic.id).label('total_connections'),
            func.count(func.distinct(NetworkTraffic.source_ip)).label('unique_sources'),
            func.count(func.distinct(NetworkTraffic.destination_ip)).label('unique_destinations')
        ).filter(NetworkTraffic.timestamp >= since).first()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_bytes_sent': traffic_stats.total_bytes_sent or 0,
                'total_bytes_received': traffic_stats.total_bytes_received or 0,
                'total_bytes': (traffic_stats.total_bytes_sent or 0) + (traffic_stats.total_bytes_received or 0),
                'total_packets': traffic_stats.total_packets or 0,
                'total_connections': traffic_stats.total_connections or 0,
                'unique_sources': traffic_stats.unique_sources or 0,
                'unique_destinations': traffic_stats.unique_destinations or 0
            },
            'timeframe_hours': hours
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

