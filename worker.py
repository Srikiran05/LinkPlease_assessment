import time
from app import create_app
from app.services.dm_sender import process_dm_batch
from app.services.poller import poll_deliveries
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sender_loop(app):
    while True:
        try:
            process_dm_batch(app)
        except Exception as e:
            logger.error(f"Error in sender loop: {e}")
        time.sleep(3)

def poller_loop(app):
    while True:
        try:
            poll_deliveries(app)
        except Exception as e:
            logger.error(f"Error in poller loop: {e}")
        time.sleep(30)

if __name__ == '__main__':
    app = create_app()
    
    sender_thread = threading.Thread(target=sender_loop, args=(app,), daemon=True)
    poller_thread = threading.Thread(target=poller_loop, args=(app,), daemon=True)
    
    sender_thread.start()
    poller_thread.start()
    
    logger.info("Workers started. Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting workers.")
