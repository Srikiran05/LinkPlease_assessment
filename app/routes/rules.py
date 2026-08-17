from flask import Blueprint, request, jsonify
from app import db
from app.models import Rule

bp = Blueprint('rules', __name__)

@bp.route('/rules', methods=['POST'])
def create_rule():
    data = request.get_json()
    if not data or 'keyword' not in data or 'dm_message' not in data:
        return jsonify({'error': 'keyword and dm_message are required'}), 400
    
    keyword = data['keyword'].strip().lower()
    dm_message = data['dm_message'].strip()
    
    rule = Rule(keyword=keyword, dm_message=dm_message)
    db.session.add(rule)
    db.session.commit()
    
    return jsonify({
        'rule_id': rule.id,
        'keyword': rule.keyword,
        'dm_message': rule.dm_message
    }), 201
