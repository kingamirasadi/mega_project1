from flask import Flask, render_template, request, redirect, flash, jsonify, url_for, session, Response
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from database import AuthenticationDB
from camera import CameraFeed

auth_db = AuthenticationDB()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('camera_streaming'))
    return render_template('homepage.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the username or email already exists
        if auth_db.get_user_by_username(username):
            flash('Username already exists. Please choose a different username.', 'error')
            return render_template('create_account.html')

        if auth_db.get_user_by_email(email):
            flash('Email already exists. Please use a different email.', 'error')
            return render_template('create_account.html')

        try:
            # Create the user in the database
            user_id = auth_db.create_user(username, password, email)
            if user_id:
                flash('Account created successfully! You can now log in.', 'success')
                return redirect(url_for('home'))  # Redirect to the homepage after success
        except Exception as e:
            flash(f'An error occurred: {str(e)}. Please try again later.', 'error')

    return render_template('create_account.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Get user details by username
        user = auth_db.get_user_by_username(username)

        if user:
            # Check if the provided password matches the stored hashed password
            if check_password_hash(user['password_hash'], password):
                flash('Login successful!', 'success')
                # Store 'user_id' as string, distinguish non-ObjectId usernames
                session['user_id'] = str(user['_id']) if '_id' in user else username
                return redirect(url_for('camera_streaming'))
            else:
                flash('Incorrect password. Please try again.', 'error')
        else:
            flash('Username does not exist. Please check your input or create an account.', 'error')

    return render_template('login.html')  # Render the login page for GET requests or after failed login attempts

@app.route('/check_username', methods=['GET'])
def check_username():
    username = request.args.get('username')  # Get the username from the request
    if username:
        user = auth_db.get_user_by_username(username)  # Check if the username exists in the database
        if user:
            return jsonify({'exists': True})  # Return a JSON response indicating the username is taken
        else:
            return jsonify({'exists': False})  # Return a JSON response indicating the username is available
    return jsonify({'exists': False})

@app.route('/camera_streaming')
def camera_streaming():
    if 'user_id' not in session:
        flash('You must be logged in to view the camera stream.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    # Check if 'user_id' is a valid ObjectId
    user = None
    if ObjectId.is_valid(user_id):
        user = auth_db.get_user_by_id(ObjectId(user_id))  # Query using ObjectId
    else:
        user = auth_db.get_user_by_username(user_id)  # Query by username for non-ObjectId

    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))

    # Render the HTML template for streaming
    return render_template('camera_streaming2.html')

@app.route('/video_feed')
def video_feed():
    # Create an instance of CameraFeed and return the video stream
    camera_feed = CameraFeed(0)
    return Response(camera_feed.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/video_feed1')
def video_feed1():
    # Create an instance of CameraFeed and return the video stream
    camera_feed = CameraFeed('https://192.168.1.210:8080/video')
    return Response(camera_feed.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
