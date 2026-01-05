from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from models import db, Person, User
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import africastalking

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'footprints2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///registry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
os.makedirs('uploads', exist_ok=True)
os.makedirs('static', exist_ok=True)

# ============================================
# INITIALIZE AFRICA'S TALKING
# ============================================
AT_USERNAME = os.getenv('AT_USERNAME')
AT_API_KEY = os.getenv('AT_API_KEY')

if AT_USERNAME and AT_API_KEY:
    africastalking.initialize(username=AT_USERNAME, api_key=AT_API_KEY)
    sms = africastalking.SMS
    SMS_ENABLED = True
    print(f"✅ Africa's Talking initialized with username: {AT_USERNAME}")
else:
    SMS_ENABLED = False
    print("⚠️ SMS not configured - check .env file")


def send_sms(phone_number, message):
    """Send SMS using Africa's Talking"""
    if not SMS_ENABLED:
        print("❌ SMS disabled - credentials missing")
        return False, "SMS not configured"
    
    try:
        phone_clean = phone_number.replace(' ', '').replace('-', '')
        if phone_clean.startswith('0'):
            phone_clean = '+233' + phone_clean[1:]
        elif not phone_clean.startswith('+'):
            phone_clean = '+233' + phone_clean

        response = sms.send(message, [phone_clean])
        print(f"✅ SMS sent successfully to {phone_clean}: {response}")
        return True, response
    except Exception as e:
        print(f"❌ SMS failed: {str(e)}")
        return False, str(e)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            return redirect('/')
        flash('Wrong username or password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/')
@login_required
def index():
    # ALL COUNTS FOR DASHBOARD TILES
    total = Person.query.count()
    lame = Person.query.filter_by(disability_type='Lame').count()
    visual = Person.query.filter_by(disability_type='Visually Impaired').count()
    deaf = Person.query.filter_by(disability_type='Deaf & Dumb').count()
    other = Person.query.filter(Person.disability_type.notin_(['Lame', 'Visually Impaired', 'Deaf & Dumb'])).count()

    return render_template('index.html', total=total, lame=lame, visual=visual, deaf=deaf, other=other)


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    total_members = Person.query.count()
    next_id = total_members + 1

    if request.method == 'POST':
        try:
            # Passport Photo
            filename = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename != '':
                    filename = secure_filename(photo.filename)
                    photo.save(os.path.join('uploads', filename))

            # Full Body Photo
            full_filename = None
            if 'full_photo' in request.files:
                full_photo = request.files['full_photo']
                if full_photo and full_photo.filename != '':
                    full_filename = "full_" + secure_filename(full_photo.filename)
                    full_photo.save(os.path.join('uploads', full_filename))

            # Ghana Card Photo
            ghana_card_filename = None
            if 'ghana_card_photo' in request.files:
                ghana_card_photo = request.files['ghana_card_photo']
                if ghana_card_photo and ghana_card_photo.filename != '':
                    ghana_card_filename = "ghana_card_" + secure_filename(ghana_card_photo.filename)
                    ghana_card_photo.save(os.path.join('uploads', ghana_card_filename))

            # Create new Person with ALL fields
            p = Person(
                name=request.form['name'],
                date_of_birth=request.form.get('date_of_birth'),
                gender=request.form.get('gender'),
                nationality=request.form.get('nationality'),
                hometown=request.form.get('hometown'),
                area_ga_west=request.form.get('area_ga_west'),
                gps_address=request.form.get('gps_address'),
                ghana_card_number=request.form.get('ghana_card_number'),
                ghana_card_photo_path=ghana_card_filename,
                disability_identified=request.form.get('disability_identified'),
                disability_cause=request.form.get('disability_cause'),
                emergency_name=request.form.get('emergency_name'),
                emergency_relationship=request.form.get('emergency_relationship'),
                emergency_phone=request.form.get('emergency_phone'),
                registered_organization=request.form.get('registered_organization'),
                organization_name=request.form.get('organization_name'),
                additional_notes=request.form.get('additional_notes'),
                marital_status=request.form.get('marital_status'),
                educational_level=request.form.get('educational_level'),
                languages_spoken=request.form.get('languages_spoken'),
                profession=request.form.get('profession'),
                english_proficiency=request.form.get('english_proficiency'),
                phone_number=request.form.get('phone_number'),
                email=request.form.get('email'),
                residential_address=request.form.get('residential_address'),
                disability_type=request.form.get('disability_type'),
                disability_other=request.form.get('disability_other', ''),
                degree_of_disability=request.form.get('degree_of_disability'),
                disability_needs=request.form.get('disability_needs'),
                social_needs=request.form.get('social_needs'),
                living_conditions=request.form.get('living_conditions'),
                guarantor_name=request.form.get('guarantor_name'),
                guarantor_phone=request.form.get('guarantor_phone'),
                photo_path=filename,
                full_photo_path=full_filename
            )

            db.session.add(p)
            db.session.commit()
            flash('Member registered successfully!', 'success')

            # === SEND REAL SMS ===
            try:
                phone = request.form.get('phone_number', '').strip()
                name = request.form.get('name', '').strip()

                if phone and SMS_ENABLED:
                    group_link = os.getenv('WHATSAPP_GROUP_LINK', 'https://chat.whatsapp.com/I25BFGzd7Tc8KY06VxmyAQ')

                    message = f"Hello {name}!\n\nWelcome to Footprints Disabled Impact family! ❤️\n\nYou have been successfully registered.\n\nPlease join our official WhatsApp group:\n{group_link}\n\nWe look forward to supporting you!\n\n- FDI Team"

                    success, response = send_sms(phone, message)

                    if success:
                        flash(f'✅ SMS sent successfully to {phone}!', 'success')
                    else:
                        flash(f'⚠️ SMS failed: {response}', 'warning')
                elif not phone:
                    flash('No phone number provided — SMS not sent', 'warning')
                elif not SMS_ENABLED:
                    flash('SMS not configured - check .env file', 'warning')

            except Exception as e:
                print("SMS Error:", str(e))
                flash(f'SMS error: {str(e)}', 'warning')

            return redirect('/')

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect('/register')

    return render_template('register.html', next_id=next_id)


@app.route('/search')
@login_required
def search():
    q = request.args.get('query', '')
    results = Person.query.filter(Person.name.ilike(f'%{q}%')).all()
    return render_template('results.html', results=results, query=q)


@app.route('/category/<cat>')
@login_required
def category(cat):
    query = request.args.get('query', '').lower()

    if cat == 'all':
        results = Person.query.all()
        title = "All Members"
    elif cat == 'lame':
        results = Person.query.filter_by(disability_type='Lame').all()
        title = "Lame"
    elif cat == 'visual':
        results = Person.query.filter_by(disability_type='Visually Impaired').all()
        title = "Visually Impaired"
    elif cat == 'deaf':
        results = Person.query.filter_by(disability_type='Deaf & Dumb').all()
        title = "Deaf & Dumb"
    elif cat == 'other':
        results = Person.query.filter(Person.disability_type.notin_(['Lame', 'Visually Impaired', 'Deaf & Dumb'])).all()
        title = "Other Disabilities"
    else:
        results = []
        title = "Category"

    if query:
        results = [p for p in results if query in p.name.lower() or query in (p.disability_type or '').lower()]

    return render_template('category_results.html', results=results, title=title, cat=cat)


@app.route('/view/<int:id>')
@login_required
def view(id):
    person = Person.query.get_or_404(id)
    return render_template('print_form.html', person=person)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    person = Person.query.get_or_404(id)

    if request.method == 'POST':
        person.name = request.form['name']
        person.date_of_birth = request.form.get('date_of_birth')
        person.gender = request.form.get('gender')
        person.nationality = request.form.get('nationality')
        person.hometown = request.form.get('hometown')
        person.area_ga_west = request.form.get('area_ga_west')
        person.gps_address = request.form.get('gps_address')
        person.ghana_card_number = request.form.get('ghana_card_number')
        person.disability_identified = request.form.get('disability_identified')
        person.disability_cause = request.form.get('disability_cause')
        person.emergency_name = request.form.get('emergency_name')
        person.emergency_relationship = request.form.get('emergency_relationship')
        person.emergency_phone = request.form.get('emergency_phone')
        person.registered_organization = request.form.get('registered_organization')
        person.organization_name = request.form.get('organization_name')
        person.additional_notes = request.form.get('additional_notes')
        person.marital_status = request.form.get('marital_status')
        person.educational_level = request.form.get('educational_level')
        person.languages_spoken = request.form.get('languages_spoken')
        person.profession = request.form.get('profession')
        person.english_proficiency = request.form.get('english_proficiency')
        person.phone_number = request.form.get('phone_number')
        person.email = request.form.get('email')
        person.residential_address = request.form.get('residential_address')
        person.disability_type = request.form.get('disability_type')
        person.disability_other = request.form.get('disability_other', '')
        person.degree_of_disability = request.form.get('degree_of_disability')
        person.disability_needs = request.form.get('disability_needs')
        person.social_needs = request.form.get('social_needs')
        person.living_conditions = request.form.get('living_conditions')
        person.guarantor_name = request.form.get('guarantor_name')
        person.guarantor_phone = request.form.get('guarantor_phone')

        if 'photo' in request.files and request.files['photo'].filename:
            photo = request.files['photo']
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            person.photo_path = filename

        if 'full_photo' in request.files and request.files['full_photo'].filename:
            full_photo = request.files['full_photo']
            full_filename = "full_" + secure_filename(full_photo.filename)
            full_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], full_filename))
            person.full_photo_path = full_filename

        if 'ghana_card_photo' in request.files and request.files['ghana_card_photo'].filename:
            ghana_card_photo = request.files['ghana_card_photo']
            ghana_card_filename = "ghana_card_" + secure_filename(ghana_card_photo.filename)
            ghana_card_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], ghana_card_filename))
            person.ghana_card_photo_path = ghana_card_filename

        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('view', id=person.id))

    return render_template('edit.html', person=person)


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    p = Person.query.get_or_404(id)
    for path in [p.photo_path, p.full_photo_path, p.ghana_card_photo_path]:
        if path:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], path))
            except:
                pass
    db.session.delete(p)
    db.session.commit()
    flash('Deleted')
    return redirect('/search?query=')


with app.app_context():
    db.create_all()

    if not User.query.first():
        users = [
            ("chairman@fdi.com", "admin001"),
            ("secretary@fdi.com", "admin002"),
            ("organizer@fdi.com", "admin003")
        ]

        for username, password in users:
            user = User(username=username)
            user.password_hash = generate_password_hash(password)
            db.session.add(user)

        db.session.commit()
        print("3 admin accounts created!")

if __name__ == '__main__':
    app.run(debug=True)