import hashlib
import time
from flask import current_app
from database.models import Session, Lecturer, db
from datetime import datetime, timedelta

def generate_secure_token(lecturer_id):
    timestamp = str(time.time())
    secret = current_app.config['SECRET_KEY']
    raw_data = f"SESSION_{lecturer_id}_{timestamp}_{secret}"
    return hashlib.sha256(raw_data.encode()).hexdigest()


def create_session_logic(lecturer_id):
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return None, "Lecturer not found"

    token_qr = generate_secure_token(lecturer_id)

    expiry_minutes = current_app.config.get('QR_EXPIRY_MINUTES', 5)
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

    new_session = Session(
        lecturer_id=lecturer_id,
        token_qr=token_qr,
        expires_at=expires_at
    )

    db.session.add(new_session)
    db.session.commit()

    return new_session, None