from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # NEW FIELDS ADDED
    date_of_birth = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    nationality = db.Column(db.String(50))
    hometown = db.Column(db.String(100))
    area_ga_west = db.Column(db.String(100))
    gps_address = db.Column(db.String(100))
    ghana_card_number = db.Column(db.String(50))
    ghana_card_photo_path = db.Column(db.String(200))  # For Ghana Card photo
    disability_identified = db.Column(db.String(100))
    disability_cause = db.Column(db.String(200))
    emergency_name = db.Column(db.String(100))
    emergency_relationship = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    registered_organization = db.Column(db.String(20))  # Yes/No
    organization_name = db.Column(db.String(200))
    additional_notes = db.Column(db.Text)

    # ORIGINAL FIELDS
    marital_status = db.Column(db.String(50))
    educational_level = db.Column(db.String(100))
    languages_spoken = db.Column(db.String(200))
    profession = db.Column(db.String(100))
    english_proficiency = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(100))
    residential_address = db.Column(db.String(300))
    disability_type = db.Column(db.String(50))
    disability_other = db.Column(db.String(100))
    degree_of_disability = db.Column(db.String(100))
    disability_needs = db.Column(db.String(300))
    social_needs = db.Column(db.String(300))
    living_conditions = db.Column(db.String(50))
    guarantor_name = db.Column(db.String(200))
    guarantor_phone = db.Column(db.String(20))
    photo_path = db.Column(db.String(200))
    full_photo_path = db.Column(db.String(200))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)