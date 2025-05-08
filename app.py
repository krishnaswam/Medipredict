import os 
import numpy as np 
import tensorflow as tf 
import joblib 
import bcrypt 
import mysql.connector 
from flask import Flask, render_template, request, redirect, url_for, session, flash 
from werkzeug.utils import secure_filename 
from tensorflow.keras.preprocessing import image 
#pip install tensorflow==2.10 keras==2.10 
# Initialize Flask App 
app = Flask(_name_) 
app.secret_key = 'your_secret_key' 
app.config["UPLOAD_FOLDER"] = "static/uploads" 
# Ensure upload directory exists 
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True) 
# Connect to MySQL Database 
db = mysql.connector.connect( 
    host="localhost", 
    user="root", 
    password="Sunny@123", 
    database="health_prediction") 
cursor = db.cursor() 
# Load AI Models 
lung_model = tf.keras.models.load_model("CNN_Model.h5", compile=False) 
heart_model = joblib.load("heart_model.pkl") 
# Class Labels for Lung Model 
lung_labels = ['NORMAL', 'PNEUMONIA'] 
# Home Page 
@app.route('/') 
def index(): 
    return render_template('index.html')
# Signup Route 
@app.route('/signup', methods=['GET', 'POST']) 
def signup(): 
    if request.method == 'POST': 
        username = request.form['username'] 
        email = request.form['email'] 
        password = request.form['password'] 
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) 
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,)) 
        existing_user = cursor.fetchone() 
        if existing_user: 
            flash('Email already registered. Please login.', 'danger') 
            return redirect(url_for('login')) 
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",  
                       (username, email, hashed_password)) 
        db.commit() 
        flash('Account created successfully! Please login.', 'success') 
        return redirect(url_for('login')) 
     return render_template('signup.html') 
# Login Route 
@app.route('/login', methods=['GET', 'POST']) 
def login(): 
    if request.method == 'POST': 
        email = request.form['email'] 
        password = request.form['password'].encode('utf-8') 
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,)) 
        user = cursor.fetchone() 
        if user and bcrypt.checkpw(password, user[3].encode('utf-8')):  # Check hashed password 
            session['user_id'] = user[0] 
            session['username'] = user[1] 
            flash(f'Welcome, {user[1]}!', 'success') 
            return redirect(url_for('index')) 
        else: 
            flash('Invalid credentials, please try again.', 'danger') 
    return render_template('login.html') 
# Logout Route 
@app.route('/logout') 
def logout(): 
    session.clear() 
    flash('Logged out successfully.', 'success') 
    return redirect(url_for('login')) 
# Lung Disease Prediction Route 
@app.route('/lung_prediction', methods=['GET', 'POST']) 
def lung_prediction(): 
    if 'user_id' not in session: 
        flash('Please log in to access this feature.', 'danger') 
        return redirect(url_for('login')) 
    if request.method == 'POST': 
        file = request.files['image'] 
        if file and file.filename: 
            filename = secure_filename(file.filename) 
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename) 
            file.save(filepath) 
            # Preprocess Image 
            img = image.load_img(filepath, target_size=(224, 224)) 
            img_array = image.img_to_array(img) / 255.0 
            img_array = np.expand_dims(img_array, axis=0) 
            # Make Prediction 
            prediction = lung_model.predict(img_array) 
            result = lung_labels[int(prediction[0][0] > 0.5)] 
            return render_template('lung_prediction.html', result=f"Prediction: {result}",  
                                   image_url=url_for('static', filename=f'uploads/{filename}')) 
    return render_template('lung_prediction.html') 
# Heart Disease Prediction Route 
@app.route('/heart_prediction', methods=['GET', 'POST']) 
def heart_prediction(): 
    if 'user_id' not in session: 
        flash('Please log in to access this feature.', 'danger') 
        return redirect(url_for('login')) 
    if request.method == 'POST':
     features = [ 
            int(request.form['age']), int(request.form['sex']), int(request.form['cp']), 
            int(request.form['trestbps']), int(request.form['chol']), int(request.form['fbs']), 
            int(request.form['restecg']), int(request.form['thalach']), int(request.form['exang']), 
            float(request.form['oldpeak']), int(request.form['slope']), int(request.form['ca']), 
int(request.form['thal'])   ] 
        features_array = np.array([features]) 
        # Make Prediction 
        prediction = heart_model.predict(features_array) 
        result = "YOU HAVE NO DISEASE" if prediction[0] == 0 else "YOU HAVE DISEASE" 
        return render_template('heart_prediction.html', result=result) 
    return render_template('heart_prediction.html') 
@app.route('/add_patient', methods=['GET', 'POST']) 
def add_patient(): 
    if 'user_id' not in session: 
        flash('Please log in to add patient information.', 'danger') 
        return redirect(url_for('login')) 
    if request.method == 'POST': 
        name = request.form['name'] 
        gender = request.form['gender'] 
        age = int(request.form['age']) 
        contact_no = request.form['contact_no'] 
        lab_results = request.form['lab_results'] 
        medical_history = request.form['medical_history'] 
        medications = request.form['medications'] 
        # Insert into the database 
        cursor.execute(""" 
            INSERT INTO patients (user_id, name, gender, age, contact_no, lab_results, medical_history, 
medications) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
        """, (session['user_id'], name, gender, age, contact_no, lab_results, medical_history, medications)) 
        db.commit() 
        flash('Patient information added successfully!', 'success') 
        return redirect(url_for('view_patients'))  # Redirect to dashboard or another page 
    return render_template('add_patient.html')  # Create this HTML form 
@app.route('/view_patients', methods=['GET']) 
def view_patients(): 
    if 'user_id' not in session: 
        flash('Please log in to view patient information.', 'danger') 
        return redirect(url_for('login')) 
    user_id = session['user_id'] 
    cursor.execute("SELECT * FROM patients WHERE user_id = %s", (user_id,)) 
    patients = cursor.fetchall() 
    return render_template('view_patients.html', patients=patients) 
# Run the App 
if _name_ == '_main_': 
    app.run(debug=True) 