import time
import requests
from app.models import DmQueue
from app import db
from datetime import datetime, timezone
import logging
from app.services.rate_limiter import dm_rate_limiter

logger = logging.getLogger(__name__)

def process_dm_batch(app):
    with app.app_context():
        now = datetime.now(timezone.utc)
        items = DmQueue.query.filter(
            DmQueue.status == 'queued',
            (DmQueue.next_retry_at <= now) | (DmQueue.next_retry_at.is_(None))
        ).order_by(DmQueue.created_at.asc()).limit(5).all()

        if not items:
            return

        base_url = app.config['PSEUDOGRAM_BASE_URL']
        api_key = app.config['API_KEY']
        
        for item in items:
            dm_rate_limiter.acquire()
            
            headers = {
                'X-API-Key': api_key,
                'Idempotency-Key': item.idempotency_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                "recipient_user_id": item.recipient_user_id,
                "message": item.message,
                "comment_id": item.comment_id
            }
            
            try:
                response = requests.post(f"{base_url}/v1/dm/send", json=payload, headers=headers)
                
                if response.status_code in (200, 202):
                    data = response.json()
                    item.status = 'sending'
                    item.dm_id = data.get('dm_id')
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 10))
                    logger.warning(f"Rate limited, sleeping for {retry_after} seconds.")
                    time.sleep(retry_after)
                    break
                elif response.status_code == 500:
                    item.attempt_count += 1
                    if item.attempt_count >= 5:
                        item.status = 'failed'
                    else:
                        import datetime as dt
                        backoff = 5 * (2 ** (item.attempt_count - 1))
                        item.next_retry_at = datetime.now(timezone.utc) + dt.timedelta(seconds=backoff)
                elif response.status_code == 400:
                    item.status = 'failed'
                    logger.error(f"Bad request for DM {item.id}: {response.text}")
                else:
                    item.status = 'failed'
                    logger.error(f"Unexpected status {response.status_code} for DM {item.id}")
            except Exception as e:
                logger.error(f"Network error sending DM {item.id}: {e}")
                
            db.session.commit()
