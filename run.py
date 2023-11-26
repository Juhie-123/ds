from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask import jsonify
import requests
import random
import pyotp
import os
import base64
import qrcode
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

DATABASE = "database.db"

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

otp_store = {}

class User(UserMixin):
    def __init__(self, user_id, email, password, first_name):
        self.id = user_id
        self.email = email
        self.password = password
        self.first_name = first_name


# Modify the load_user function accordingly
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password, first_name FROM userss WHERE id=?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(*user_data)
    return None


# Sample data for dogs and cats
dogs = [
    {"id": 1, "name": "Charlie", "image": "/static/dog1.jpg", "description": "Meet Charlie, the charming Corgi with a heart as big as those adorable ears. Charlie is a playful and intelligent companion, known for their loyalty and affectionate nature. This little bundle of joy is ready to bring smiles and laughter into your home."},
    {"id": 2, "name": "Phoebe", "image": "/static/dog2.jpg", "description": "Introducing Phoebe, the delightful Bolognese who's as fluffy as a cloud. This small, white ball of fur is not just a lap dog, Phoebe is full of personality and loves to be the center of attention. With a sweet disposition, she'll surely add warmth to your home."},
    {"id": 3, "name": "Daisy", "image": "/static/dog3.png", "description": "Daisy, the majestic German Shepherd, is a loyal guardian and a loving friend. With her striking appearance and intelligence, Daisy is ready to be a protective member of your family. Whether playing in the yard or cuddling on the couch, she's a devoted companion."},
    {"id": 4, "name": "Bhairav", "image": "/static/dog4.jpg", "description": "Meet Bhairav, the regal Rajapalayam with a proud bearing and a heart of gold. Known for their courage and loyalty, Bhairav is not just a pet but a symbol of strength and fidelity. With a sleek white coat, he's a magnificent presence waiting to grace your home."},
    {"id": 5, "name": "Veera", "image": "/static/dog6.jpg", "description": "Veera, the spirited Kombai, is a true Indian gem. With a distinctive appearance and a lively spirit, Veera is a wonderful blend of strength and agility. This companion is ready for adventures and will bring a touch of Indian heritage to your life."},
    {"id": 6, "name": "Harry", "image": "/static/dog5.jpg", "description": "Meet Harry, the handsome Husky with piercing blue eyes, is an adventurous and sociable canine companion. Known for their striking coat and friendly demeanor, Harry loves outdoor activities and is always up for a run or a playful game of fetch. Get ready for an energetic and loving addition to your family."}
]

cats = [
    {"id": 1, "name": "Whiskers", "image": "/static/cat1.jpg", "description": "Meet Whiskers, the elegant grey cat, is a picture of sophistication and grace. With a plush, silvery coat and whiskers that dance like wisps of smoke, Whiskers is as charming as they are mysterious. This feline friend is sure to bring a touch of quiet elegance to your home."},
    {"id": 2, "name": "Mittens", "image": "/static/cat2.jpg", "description": "Introducing Mittens, the playful tabby cat, is a bundle of energy and charm. With distinctive stripes and adorable mittens on each paw, Mittens is ready for interactive play and cuddles. This tabby's affectionate nature will warm your heart."},
    {"id": 3, "name": "Snophy", "image": "/static/cat3.jpg", "description": "Snophy, the striped brown beauty, is a cat with a unique pattern that tells a story. With a coat resembling the rich hues of autumn, Snophy is both cozy and captivating. This feline friend is ready to share quiet moments and playful antics."},
    {"id": 4, "name": "Kayal", "image": "/static/cat4.jpg", "description": "Kayal, the enigmatic Kao Mane, is a cat with a distinctive appearance and a captivating gaze. With a coat reminiscent of a moonlit night, Kayal brings a touch of mystery and a whole lot of love to your home."},
    {"id": 5, "name": "Cutey", "image": "/static/cat5.jpg", "description": "Meet Cutey, the orange-striped charmer, is a burst of sunshine in feline form. With a bright and vivacious personality, Cutey's playful antics and affectionate purrs are bound to bring joy to your home. Get ready for a daily dose of cuteness."},
    {"id": 6, "name": "Sweety", "image": "/static/cat6.jpg", "description": "Sweety, the sleek black cat, is a creature of elegance and mystery. With eyes that gleam like polished onyx, Sweety is a gentle companion with a heart full of love. Despite superstitions, this black cat is ready to bring nothing but good luck and warmth into your life."},
]

@app.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user, dogs=dogs, cats=cats)

# Add a route for pet details
@app.route('/pet/<pet_type>/<int:pet_id>')
@login_required
def pet_detail(pet_type, pet_id):
    # Retrieve pet details based on pet_type and pet_id
    if pet_type == 'dog':
        pet = next((dog for dog in dogs if dog["id"] == pet_id), None)
    elif pet_type == 'cat':
        pet = next((cat for cat in cats if cat["id"] == pet_id), None)
    else:
        pet = None

    if pet:
        return render_template('pet_detail.html', user=current_user, pet=pet, pet_type=pet_type)
    else:
        flash('Pet not found', category='error')
        return redirect(url_for('home'))

def verify_recaptcha(recaptcha_response):
    secret_key = "6LddK48oAAAAAOTdkykCV11V2uz_LP1if2jelHCK"
    data = {
        'secret': secret_key,
        'response': recaptcha_response
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = response.json()
    return result.get('success', False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    question = ""  # Initialize the question variable

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        recaptcha_response = request.form.get('g-recaptcha-response')

        # Verify the reCAPTCHA response
        if not verify_recaptcha(recaptcha_response):
            flash('reCAPTCHA verification failed. Please try again.', category='error')
            return redirect(url_for('login'))

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM userss WHERE email=?", (email,))
        user_data = cursor.fetchone()

        if user_data and check_password_hash(user_data[2], password):
            # Randomly select a question and ask during login
            random_question_number = random.randint(1, 3)  # Assuming you have three questions

            # Get the correct answer from user_data
            answer_key = f'answer{random_question_number}'
            correct_answer = user_data[answer_key]

            # Retrieve the predefined question
            if random_question_number == 1:
                question = "What is your favorite color?"
            elif random_question_number == 2:
                question = "What is your favorite food?"
            elif random_question_number == 3:
                question = "Your favorite country?"

            # Check if the provided answer matches the correct answer
            user_answer = request.form.get('answer')

            if user_answer and user_answer.lower() == correct_answer.lower():
                flash('Logged in successfully!', category='success')
                user = User(*user_data)
                login_user(user, remember=True)
                conn.close()
                return redirect(url_for('home'))
            else:
                flash('Incorrect answer to the question. Please try again.', category='error')

        else:
            flash('Incorrect email or password, try again.', category='error')
            conn.close()

    return render_template("login.html", user=current_user, question=question)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Check if the email already exists
        cursor.execute("SELECT * FROM userss WHERE email=?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists', category='error')
        elif len(email) < 4 or len(first_name) < 2 or password1 != password2 or len(password1) < 7:
            flash('Invalid registration data. Please check your input.', category='error')
        else:
            # Insert the new user into the 'users' table
            hashed_password = generate_password_hash(password1, method='sha256')
            # Get answers for questions dynamically
            answers = [request.form.get(f'answer{i}') for i in range(1, 4)]
            cursor.execute(
                "INSERT INTO userss (email, password, first_name, answer1, answer2, answer3) VALUES (?, ?, ?, ?, ?, ?)",
                (email, hashed_password, first_name, *answers))
            conn.commit()
            flash('Account created!', category='success')
            conn.close()

    # Retrieve personal questions from the database
    personal_questions = [
        "What is your favorite color?",
        "What is your favorite food?",
        "Your favorite country?"
    ]

    return render_template("signup.html", user=current_user, personal_questions=personal_questions)

@app.route('/adopt_confirm/<pet_type>/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def adopt_confirm(pet_type, pet_id):
    key="Pneumonoultramicroscopicsilicovolcanoconiosis"

    totp = pyotp.TOTP(key)
    uri = totp.provisioning_uri("juhieshreegmail.com", issuer_name="juhieshree")

    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=4,
    )

    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert the image to a bytes object
    buffered = io.BytesIO()
    img.save(buffered)

    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Make sure to pass the user variable, original_otp, and confirmation_successful to the template
    return render_template(
        'adopt_confirm.html',
        user=current_user,
        pet_type=pet_type,
        pet_id=pet_id,
        img_data=img_data
    )

@app.route('/valid_otp/<pet_type>/<int:pet_id>', methods=['POST'])
def valid_otp(pet_type, pet_id):
    otp = request.form.get('otp')
    key="Pneumonoultramicroscopicsilicovolcanoconiosis"
    totp = pyotp.TOTP(key)

    if totp.verify(otp):
        return render_template('adoption_confirmation.html', user=current_user, pet_type=pet_type, pet_id=pet_id)
    else:
        return "OTP is invalid. Please try again."
    

def initialize_database():
    # Connect to SQLite database (creates a new database if it doesn't exist)
    conn = sqlite3.connect('database.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Define the SQL queries to create tables
    create_user_table = '''
    CREATE TABLE IF NOT EXISTS userss (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        first_name TEXT,
        answer1 TEXT,
        answer2 TEXT,
        answer3 TEXT
    );
    '''

    # Execute the SQL queries
    cursor.execute(create_user_table)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)

