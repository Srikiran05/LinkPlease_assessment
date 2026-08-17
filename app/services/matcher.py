from app import db
from app.models import Rule, DmQueue, SentLog, ProcessedEvent, DeletedComment
import logging
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

def process_event_in_background(app, payload: dict):
    with app.app_context():
        event_id = payload.get('event_id')
        event_type = payload.get('event_type')
        data = payload.get('data', {})
        
        # 1. Idempotency Check
        try:
            processed = ProcessedEvent(event_id=event_id)
            db.session.add(processed)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logger.info(f"Duplicate event_id {event_id}, ignoring.")
            return

        comment_id = data.get('comment_id')
        
        # 2. Handle deleted comment
        if event_type == 'comment.deleted':
            try:
                deleted = DeletedComment(comment_id=comment_id)
                db.session.add(deleted)
                
                # Cancel any pending DMs
                DmQueue.query.filter_by(comment_id=comment_id, status='queued').update({'status': 'cancelled'})
                DmQueue.query.filter_by(comment_id=comment_id, status='sending').update({'status': 'cancelled'})
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            return
            
        if event_type == 'comment.created':
            is_deleted = DeletedComment.query.filter_by(comment_id=comment_id).first()
            if is_deleted:
                logger.info(f"Comment {comment_id} was already deleted, skipping.")
                return

            text = data.get('text', '').lower()
            user_id = data.get('from', {}).get('user_id')
            
            if not user_id:
                return

            rules = Rule.query.all()
            for rule in rules:
                if rule.keyword in text:
                    try:
                        sent_log = SentLog(user_id=user_id, rule_id=rule.id)
                        db.session.add(sent_log)
                        db.session.flush()
                        
                        dm = DmQueue(
                            comment_id=comment_id,
                            rule_id=rule.id,
                            recipient_user_id=user_id,
                            message=rule.dm_message,
                            idempotency_key=f"{comment_id}:{rule.id}:0"
                        )
                        db.session.add(dm)
                        db.session.commit()
                        logger.info(f"Queued DM for user {user_id} on rule {rule.id}")
                    except IntegrityError:
                        db.session.rollback()
                        logger.info(f"Duplicate DM rule {rule.id} for user {user_id}, skipping.")
