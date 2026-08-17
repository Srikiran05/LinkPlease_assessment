from flask import Blueprint, request, jsonify, current_app
from app.services.signature import verify_signature
from app.services.matcher import process_event_in_background
import threading
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('webhook', __name__)

debug_payloads = []

@bp.route('/webhook', methods=['POST'])
def webhook():
    raw_body = request.get_data()
    signature = request.headers.get('X-PseudoGram-Signature', '')
    
    global debug_payloads
    
    if not verify_signature(raw_body, signature):
        debug_payloads.append({'status': 401, 'body': raw_body.decode('utf-8', errors='replace')})
        if len(debug_payloads) > 50: debug_payloads.pop(0)
        logger.warning("Invalid signature on webhook request.")
        return jsonify({"error": "invalid signature"}), 401
    
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        debug_payloads.append({'status': 400, 'body': raw_body.decode('utf-8', errors='replace')})
        if len(debug_payloads) > 50: debug_payloads.pop(0)
        return jsonify({'error': 'Invalid JSON'}), 400
    
    debug_payloads.append({'status': 200, 'body': payload})
    if len(debug_payloads) > 50: debug_payloads.pop(0)
    
    app_instance = current_app._get_current_object()
    
    thread = threading.Thread(
        target=process_event_in_background,
        args=(app_instance, payload)
    )
    thread.daemon = True
    thread.start()
    
    return '', 200

@bp.route('/debug/webhooks', methods=['GET'])
def get_debug_webhooks():
    return jsonify(debug_payloads)
