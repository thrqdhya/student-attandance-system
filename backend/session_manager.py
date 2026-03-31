import time

sessions = {}
SESSION_TIMEOUT = 30

def create_session(student_id):
    sessions[student_id] = {
        "status": "ACTIVE",
        "last_activity": time.time()
    }

def is_session_active(student_id):
    if student_id not in sessions:
        return False

    last = sessions[student_id]["last_activity"]

    if time.time() - last > SESSION_TIMEOUT:
        sessions[student_id]["status"] = "INACTIVE"
        return False

    return True

def update_activity(student_id):
    if student_id in sessions:
        sessions[student_id]["last_activity"] = time.time()

def logout(student_id):
    if student_id in sessions:
        sessions[student_id]["status"] = "INACTIVE"