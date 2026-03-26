from database.models import Student

def validate_nim(nim):
    return Student.query.filter_by(nim=nim).first()