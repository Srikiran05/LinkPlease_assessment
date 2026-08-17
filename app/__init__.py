from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging
import threading

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)

    with app.app_context():
        # Setup WAL mode
        from sqlalchemy import text
        try:
            db.session.execute(text('PRAGMA journal_mode=WAL;'))
            db.session.commit()
        except Exception:
            pass

        from app import models
        db.create_all()
        
        # Seed default rule
        if not models.Rule.query.filter_by(keyword='price').first():
            default_rule = models.Rule(keyword='price', reply_text='Here is the price!')
            db.session.add(default_rule)
            db.session.commit()

        from app.routes import rules, webhook, stats
        app.register_blueprint(rules.bp)
        app.register_blueprint(webhook.bp)
        app.register_blueprint(stats.bp)
        
        # Start background workers (since Gunicorn will run with 1 worker, this is safe)
        from worker import sender_loop, poller_loop
        threading.Thread(target=sender_loop, args=(app,), daemon=True).start()
        threading.Thread(target=poller_loop, args=(app,), daemon=True).start()

    return app
