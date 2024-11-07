from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from PIL import Image
import pytesseract  # Tesseract OCR library
from deep_translator import GoogleTranslator  # Deep Translator library

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# File to store user credentials
USER_DATA_FILE = 'users.txt'

# File upload settings
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to save users
def save_user(username, password_hash):
    with open(USER_DATA_FILE, 'a') as file:
        file.write(f"{username},{password_hash}\n")

# Helper function to load users
def load_users():
    users = {}
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as file:
            for line in file:
                username, password_hash = line.strip().split(',')
                users[username] = password_hash
    return users

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        users = load_users()
        if username in users:
            flash("Username already exists!")
            return redirect(url_for('register'))

        save_user(username, password_hash)
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            flash("Login successful!")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password!")
            return redirect(url_for('login'))

    return render_template('login.html')

# Home route (after login)
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))  # If not logged in, redirect to login page
    return render_template('home.html', username=session['username'])

# Root route - redirect to login if not logged in, otherwise to home
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return redirect(url_for('home'))  # Redirect to home if logged in

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))  # Redirect to login page after logout

# Translation route
@app.route('/translation')
def translation():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('translation.html')

# Image Translation Route (for handling form submission)
@app.route('/translate-image', methods=['POST'])
def translate_image():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Check if the form contains a file
    if 'imageUpload' not in request.files:
        flash("No file part")
        return redirect(request.url)
    
    file = request.files['imageUpload']
    
    # If no file is selected
    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    # Debugging: Print the file's name for verification
    print("File received:", file.filename)

    # Check if the file is allowed
    if file and allowed_file(file.filename):
        # Secure the file name and save it
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Ensure the upload folder exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # Save the uploaded image to the upload folder
        file.save(file_path)

        # OCR Logic to extract text from the image
        try:
            # Open the image using PIL
            img = Image.open(file_path)
            
            # Perform OCR to extract text
            extracted_text = pytesseract.image_to_string(img)

            # Check if any text was extracted
            if extracted_text.strip() == "":
                flash("No text found in the image.")
            else:
                flash(f"Text extracted: {extracted_text}")

            # Translate the extracted text (Spanish to English)
            translated_text = GoogleTranslator(source='auto', target='en').translate(extracted_text)
            flash(f"Translated text: {translated_text}")

        except Exception as e:
            flash(f"Error processing the image: {str(e)}")

        return redirect(url_for('translation'))
    
    # If the file type is not allowed
    flash("Invalid file type. Only image files are allowed (png, jpg, jpeg, gif).")
    return redirect(request.url)

# About Us route
@app.route('/about')
def about():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('about.html')

# Help route
@app.route('/help')
def help():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('help.html')

# Feedback route (GET and POST)
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        feedback_text = request.form['feedback']
        
        # Save the feedback to a file (feedback.txt)
        with open('feedback.txt', 'a') as file:
            file.write(feedback_text + "\n")
        
        flash("Feedback submitted successfully!")
        return redirect(url_for('feedback'))  # Redirect back to feedback page to show the message

    return render_template('feedback.html')

# Privacy Policy route
@app.route('/privacy')
def privacy():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('privacy.html')

# Functional Requirements route
@app.route('/requirements')
def requirements():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('requirements.html')

if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
