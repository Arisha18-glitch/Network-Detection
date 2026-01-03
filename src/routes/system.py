from flask import Blueprint, jsonify, request
from src.models.system_log import SystemLog
from src.database import db
from datetime import datetime, timedelta
import psutil
import os

system_bp = Blueprint('system', __name__)

@system_bp.route('/status/health', methods=['GET'])
def get_system_health():
    """Check the overall health of the system"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check database connectivity
        db_status = 'healthy'
        try:
            db.session.execute('SELECT 1')
            db.session.commit()
        except Exception:
            db_status = 'unhealthy'
        
        # Determine overall health status
        health_status = 'healthy'
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90 or db_status == 'unhealthy':
            health_status = 'warning'
        if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
            health_status = 'critical'
        
        return jsonify({
            'success': True,
            'health': {
                'status': health_status,
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'detection_engine': 'healthy',  # Simulated - would check actual service
                    'api_server': 'healthy',
                    'database': db_status
                },
                'system_metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'health': {
                'status': 'critical',
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 500

@system_bp.route('/status/logs', methods=['GET'])
def get_system_logs():
    """Retrieve system logs with filtering options"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        level = request.args.get('level')  # INFO, WARNING, ERROR, DEBUG
        component = request.args.get('component')
        hours = request.args.get('hours', 24, type=int)
        
        # Build query
        query = SystemLog.query
        
        # Filter by time
        if hours:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(SystemLog.timestamp >= since)
        
        # Filter by level
        if level:
            query = query.filter(SystemLog.level == level.upper())
        
        # Filter by component
        if component:
            query = query.filter(SystemLog.component == component)
        
        # Order by timestamp descending and limit results
        logs = query.order_by(SystemLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs],
            'count': len(logs),
            'filters': {
                'level': level,
                'component': component,
                'hours': hours,
                'limit': limit
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/status/components', methods=['GET'])
def get_component_status():
    """Get status of individual system components"""
    try:
        components = {
            'detection_engine': {
                'status': 'healthy',
                'last_check': datetime.utcnow().isoformat(),
                'uptime_hours': 24.5,  # Simulated
                'processed_packets': 1250000  # Simulated
            },
            'api_server': {
                'status': 'healthy',
                'last_check': datetime.utcnow().isoformat(),
                'uptime_hours': 24.5,
                'requests_handled': 15420
            },
            'database': {
                'status': 'healthy',
                'last_check': datetime.utcnow().isoformat(),
                'size_mb': round(os.path.getsize(os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')) / (1024*1024), 2) if os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')) else 0,
                'connections': 1
            },
            'notification_service': {
                'status': 'healthy',
                'last_check': datetime.utcnow().isoformat(),
                'notifications_sent': 45
            }
        }
        
        return jsonify({
            'success': True,
            'components': components
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper function to add system logs (used by other components)
def add_system_log(level, message, component):
    """Add a system log entry"""
    try:
        log = SystemLog(
            level=level.upper(),
            message=message,
            component=component
        )
        db.session.add(log)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Failed to add system log: {e}")
        return False

