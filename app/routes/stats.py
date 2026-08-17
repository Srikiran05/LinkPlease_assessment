from flask import Blueprint, jsonify
from app import db
from app.models import DmQueue, SentLog

bp = Blueprint('stats', __name__)

@bp.route('/stats', methods=['GET'])
def get_stats():
    sent = db.session.query(DmQueue).filter_by(status='sent').count()
    failed = db.session.query(DmQueue).filter_by(status='failed').count()
    queued = db.session.query(DmQueue).filter(DmQueue.status.in_(['queued','sending'])).count()
    
    total_sent_logs = db.session.query(SentLog).count()
    total_dms = db.session.query(DmQueue).count()
    duplicates_blocked = total_sent_logs - total_dms
    
    return jsonify({
        "sent": sent,
        "failed": failed,
        "queued": queued,
        "duplicates_blocked": duplicates_blocked if duplicates_blocked > 0 else 0
    }), 200
@bp.route('/debug/queue', methods=['GET'])
def debug_queue():
    items = DmQueue.query.all()
    res = []
    for i in items:
        res.append({
            'id': i.id,
            'status': i.status,
            'attempt_count': i.attempt_count,
            'dm_id': i.dm_id,
            'next_retry_at': i.next_retry_at.isoformat() if i.next_retry_at else None
        })
    return jsonify(res)
