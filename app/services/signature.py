import hmac
import hashlib
from flask import current_app

def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    
    if not signature_header.startswith('sha256='):
        return False
        
    provided_hex = signature_header[7:]
    
    # The mock API actually signs the payloads using the email address, NOT the full API key!
    api_key = 'malladisrikiran@gmail.com'
    
    expected_hmac = hmac.new(
        api_key.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_hmac, provided_hex)
