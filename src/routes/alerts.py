from flask import Blueprint, jsonify, request
from src.models.alert import Alert
from src.database import db
from datetime import datetime, timedelta
import json

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts with optional filtering"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        status = request.args.get('status')
        severity = request.args.get('severity')
        
        # Build query
        query = Alert.query
        
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        
        # Order by timestamp descending and limit results
        alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific alert by ID"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        return jsonify({
            'success': True,
            'alert': alert.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['PUT'])
def acknowledge_alert(alert_id):
    """Acknowledge a specific alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        alert.status = 'Acknowledged'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Alert {alert_id} acknowledged',
            'alert': alert.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts (last 24 hours by default)"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        alerts = Alert.query.filter(Alert.timestamp >= since).order_by(Alert.timestamp.desc()).all()
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts),
            'timeframe_hours': hours
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics"""
    try:
        # Count alerts by status
        active_count = Alert.query.filter(Alert.status == 'Active').count()
        acknowledged_count = Alert.query.filter(Alert.status == 'Acknowledged').count()
        resolved_count = Alert.query.filter(Alert.status == 'Resolved').count()
        
        # Count alerts by severity
        critical_count = Alert.query.filter(Alert.severity == 'Critical').count()
        high_count = Alert.query.filter(Alert.severity == 'High').count()
        medium_count = Alert.query.filter(Alert.severity == 'Medium').count()
        low_count = Alert.query.filter(Alert.severity == 'Low').count()
        
        # Recent alerts (last 24 hours)
        since_24h = datetime.utcnow() - timedelta(hours=24)
        recent_count = Alert.query.filter(Alert.timestamp >= since_24h).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'by_status': {
                    'active': active_count,
                    'acknowledged': acknowledged_count,
                    'resolved': resolved_count
                },
                'by_severity': {
                    'critical': critical_count,
                    'high': high_count,
                    'medium': medium_count,
                    'low': low_count
                },
                'recent_24h': recent_count,
                'total': Alert.query.count()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

