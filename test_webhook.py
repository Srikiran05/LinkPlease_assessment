import hmac
import hashlib
import json
import requests
import time
import sys

# Default API key used in config.py for local testing
API_KEY = "bWFsbGFkaXNyaWtpcmFuQGdtYWlsLmNvbQ.7c14e383d729c7fcad6a"
WEBHOOK_URL = "http://127.0.0.1:5000/webhook"

def send_test_webhook(event_type="comment.created", text="I would like the PRICE please!", event_id=None, comment_id=None):
    if not event_id:
        event_id = f"evt_{int(time.time())}"
    if not comment_id:
        comment_id = f"cmt_{int(time.time())}"
        
    payload = {
      "event_id": event_id,
      "event_type": event_type,
      "sent_at": "2026-08-17T12:00:00.000Z",
      "data": {
        "comment_id": comment_id,
        "post_id": "post_44de1b",
        "text": text,
        "created_at": "2026-08-17T11:59:00.000Z",
        "from": {
          "user_id": f"usr_{int(time.time())}",
          "username": "test_user"
        }
      }
    }

    # Must serialize to raw bytes exactly as the server receives it
    raw_body = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    # Generate the HMAC-SHA256 signature
    signature = hmac.new(
        API_KEY.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'X-PseudoGram-Signature': f'sha256={signature}'
    }

    print(f"Sending {event_type} webhook to {WEBHOOK_URL}...")
    response = requests.post(WEBHOOK_URL, data=raw_body, headers=headers)

    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    return event_id, comment_id

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "create"
    
    if action == "create":
        # Simulate a user commenting "PRICE"
        send_test_webhook()
    elif action == "duplicate":
        # Simulate Instagram sending the exact same event twice
        print("Sending first event...")
        event_id, comment_id = send_test_webhook()
        print("\nSending exact same event again (duplicate)...")
        send_test_webhook(event_id=event_id, comment_id=comment_id)
    elif action == "delete":
        # Simulate a user commenting and then deleting their comment
        event_id, comment_id = send_test_webhook()
        print("\nSimulating comment deletion...")
        send_test_webhook(event_type="comment.deleted", text="", comment_id=comment_id)
    else:
        print("Usage: python test_webhook.py [create|duplicate|delete]")
