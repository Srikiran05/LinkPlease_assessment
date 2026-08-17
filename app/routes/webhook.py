from flask import Blueprint, request, jsonify, current_app
from app.services.signature import verify_signature
from app.services.matcher import process_event_in_background
import threading

bp = Blueprint('webhook', __name__)

@bp.route('/webhook', methods=['POST'])
def webhook():
    raw_body = request.get_data()
    signature = request.headers.get('X-PseudoGram-Signature', '')
    
    if not verify_signature(raw_body, signature):
        return jsonify({"error": "invalid signature"}), 401
    
    payload = request.get_json()
    
    app_instance = current_app._get_current_object()
    
    thread = threading.Thread(
        target=process_event_in_background,
        args=(app_instance, payload)
    )
    thread.daemon = True
    thread.start()
    
    return '', 200
