# FAILURES.md — Known Failure Modes

## 1. Process crash during POST /dm/send before saving dm_id
If the mock API receives our POST request and processes it, but our Flask app crashes right before updating SQLite with the new `dm_id`, the DM remains `queued`. On restart, we retry with the *same* `attempt_count`. Thanks to the `Idempotency-Key` (which includes attempt_count), the mock API will return the same `dm_id` instead of sending a duplicate. However, if the mock API loses its idempotency cache, a duplicate DM could be sent.

## 2. Global Thread Sleep on 429 locks all processing
When a 429 is received, the DM Sender thread sleeps for `Retry-After` seconds. While this correctly respects the rate limit and avoids locking the database, it means *no* messages will be sent at all during this window. If a burst of 500 valid messages arrives, they will be backlogged sequentially instead of distributing the retry load concurrently.

## 3. SQLite Concurrency under High Volume
While SQLite WAL mode handles reads cleanly, it strictly serializes writes. Under extreme load (e.g., thousands of comments per second), the background thread writing `processed_events` will face `OperationalError: database is locked`. The system would need a transition to PostgreSQL to truly scale horizontally across multiple instances.

## 4. Delivery poller window: DMs can stay in 'sending' for up to 30 seconds
The poller runs every 30 seconds. A DM accepted by the API at T=0 won't be confirmed as delivered or failed until T=30s. Under load, this means `/stats` will show inflated `queued` numbers for up to 30 seconds after the actual delivery confirmation. If the system crashes at T=29s, that delivery status resolution is delayed further.
