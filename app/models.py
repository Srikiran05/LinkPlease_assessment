from app import db
import uuid
from datetime import datetime, timezone

def generate_uuid():
    return str(uuid.uuid4())

class Rule(db.Model):
    __tablename__ = 'rules'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    keyword = db.Column(db.String, nullable=False)
    dm_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ProcessedEvent(db.Model):
    __tablename__ = 'processed_events'
    event_id = db.Column(db.String, primary_key=True)
    processed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class DmQueue(db.Model):
    __tablename__ = 'dm_queue'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    comment_id = db.Column(db.String, index=True)
    rule_id = db.Column(db.String, db.ForeignKey('rules.id'))
    recipient_user_id = db.Column(db.String, nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String, default='queued') # queued, sending, sent, failed, cancelled
    dm_id = db.Column(db.String, nullable=True)
    attempt_count = db.Column(db.Integer, default=0)
    next_retry_at = db.Column(db.DateTime, nullable=True)
    idempotency_key = db.Column(db.String, unique=True) # {comment_id}:{rule_id}:{attempt_count}
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SentLog(db.Model):
    __tablename__ = 'sent_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, nullable=False)
    rule_id = db.Column(db.String, db.ForeignKey('rules.id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'rule_id', name='uix_user_rule'),
    )

class DeletedComment(db.Model):
    __tablename__ = 'deleted_comments'
    comment_id = db.Column(db.String, primary_key=True)
    deleted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
