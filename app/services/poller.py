import requests
from app.models import DmQueue
from app import db
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def poll_deliveries(app):
    with app.app_context():
        items = DmQueue.query.filter(
            DmQueue.status == 'sending',
            DmQueue.dm_id.isnot(None)
        ).all()
        
        if not items:
            return

        base_url = app.config['PSEUDOGRAM_BASE_URL']
        api_key = app.config['API_KEY']
        headers = {'X-API-Key': api_key}
        
        for item in items:
            try:
                response = requests.get(f"{base_url}/v1/dm/{item.dm_id}", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'delivered':
                        item.status = 'sent'
                    elif status == 'failed':
                        if item.attempt_count < 5:
                            item.attempt_count += 1
                            item.status = 'queued'
                            import datetime as dt
                            backoff = 5 * (2 ** (item.attempt_count - 1))
                            item.next_retry_at = datetime.now(timezone.utc) + dt.timedelta(seconds=backoff)
                            item.idempotency_key = f"{item.comment_id}:{item.rule_id}:{item.attempt_count}"
                        else:
                            item.status = 'failed'
                    elif status == 'queued':
                        pass
                else:
                    logger.error(f"Poller got {response.status_code} for dm_id {item.dm_id}")
            except Exception as e:
                logger.error(f"Network error polling DM {item.dm_id}: {e}")
                
            db.session.commit()
