from flask import Flask, render_template, request, redirect, flash, jsonify, url_for, session, Response
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from database import AuthenticationDB
from camera import CameraFeed
from camera2 import LiveCam
from camera3 import CameraFeed3
from face_database_handler import FaceDatabaseHandler

auth_db = AuthenticationDB()
db_handler = FaceDatabaseHandler(
        db_uri="mongodb://localhost:27017",
        db_name="face_recognition_db",
        collection_name="recognized_faces"
    )

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('camera_streaming'))
    return render_template('homepage.html')

@app.route('/user_manage')
def user_manage():
    return render_template('admin_login.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if auth_db.get_user_by_username(username):
            flash('Username already exists. Please choose a different username.', 'error')
            return render_template('create_account.html')

        if auth_db.get_user_by_email(email):
            flash('Email already exists. Please use a different email.', 'error')
            return render_template('create_account.html')

        try:
            user_id = auth_db.create_user(username, password, email)
            if user_id:
                flash('Account created successfully! You can now log in.', 'success')
                session.clear()  # Ensure no user is automatically logged in
                return redirect(url_for('login'))  # Redirect to login page instead of home
        except Exception as e:
            flash(f'An error occurred: {str(e)}. Please try again later.', 'error')

    return render_template('create_account.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = auth_db.get_user_by_username(username)

        if user and check_password_hash(user['password_hash'], password):
            flash('Login successful!', 'success')
            session['user_id'] = str(user['_id']) if '_id' in user else username
            return redirect(url_for('camera_streaming'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = auth_db.get_user_by_username(username)

        if user and check_password_hash(user['password_hash'], password):
            flash('Login successful!', 'success')
            session['user_id'] = str(user['_id']) if '_id' in user else username
            return render_template('user_manage.html')
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin_login.html')

@app.route('/camera_streaming')
def camera_streaming():
    if 'user_id' not in session:
        flash('You must be logged in to view the camera stream.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = auth_db.get_user_by_id(ObjectId(user_id)) if ObjectId.is_valid(user_id) else auth_db.get_user_by_username(user_id)

    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))

    return render_template('camera_streaming2.html')

@app.route('/video_feed0')
def video_feed0():
    camera_feed0 = CameraFeed('')
    return Response(camera_feed0.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed1')
def video_feed1():
    try:
        camera_feed1 = LiveCam('https://192.168.1.210:8080/video')
        return Response(camera_feed1.LiveCamFeed(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/video_feed2')
def video_feed2():
    camera_feed2 = CameraFeed(url='https://192:8080/video', db_handler=db_handler)
    return Response(camera_feed2.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed3')
def video_feed3():
    try:
        camera_feed3 = CameraFeed3(0, db_handler)
        return Response(camera_feed3.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
