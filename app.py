"""
The application module where urls and functions are registered.
"""
from flask import *
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import db
from models import User, Admin, FaceImage
from flask_mail import Mail, Message
import random
import string
import os
import cv2
import uuid
from static.detection.pytorch_infer import inference
from PIL import Image

# application instance
app = Flask(__name__)
# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:xuxianda6403838@127.0.0.1:3306/project1'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SECRET_KEY'] = 'ece1779'
# Initialize the database
db.init_app(app)
# Initialize the frontend
bootstrap = Bootstrap(app)
# Configure the email
app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'ece1779@163.com'
app.config['MAIL_PASSWORD'] = 'CVEBVBFIQQGZCIKI'
# Initialize the email instance
mail = Mail(app)

#################### User
@app.route('/', methods=['GET', 'POST'])
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    """
    Deals with the login of the common user.
    """
    # Clears the session history first
    session.clear()
    if request.method == 'POST':
        # Gets information from the bootstrap form
        username = request.form.get('username')
        password = request.form.get('password')
        # Firstly checks whether the username is in use
        user_info = User.query.filter_by(username=username).first()
        if user_info is None:
            # Display the error
            flash('User does not exist!')
            return render_template('user_login.html', username=username)
        # Secondly checks whether the password is correct
        elif not check_password_hash(user_info.password, password):
            # Display the error
            flash('Wrong password!')
            return render_template('user_login.html', username=username)
        # Records the login information in session
        session['is_login'] = True
        session['is_user'] = True
        session['is_admin'] = False
        session['name'] = username
        # Redirects to the mask detection page
        return redirect('/mask_detect')
    return render_template('user_login.html')

@app.route('/getUsers', methods=['GET', 'POST'])
def getUsers():
    """
    Gets the information of all the users.
    :return: The user information in the json format.
    """
    data = []
    if request.method == 'GET':
        # Queries all the user information from the database
        users = User.query.filter().order_by(User.id.asc()).all()
        for user in users:
            d = {
                'id': user.id,
                'username': user.username,
                'password': user.password,
                'email': user.email
            }
            data.append(d)
    # Returns the data in the json format
    return jsonify({'total': len(data), 'rows': data})

@app.route('/deleteUser', methods=['GET', 'POST'])
def deleteUser():
    """
    Deletes a user based on its id.
    :return: The operation response.
    """
    if request.method == 'POST':
        # Queries the user from the database based on its id
        deleteId = request.values.get('id')
        user = User.query.filter_by(id=deleteId).first()
        # Deletes the user
        db.session.delete(user)
        db.session.commit()
        # Returns the response in the json format
        return jsonify({
            'success': True,
            'msg': 'Successfully delete the user!'
        })

@app.route('/user_forget', methods=['GET', 'POST'])
def user_forget():
    """
    Helps the user retrieve the password.
    Sends auth code to the user email.
    If the user enters the correct auth code, he can reset the password.
    """
    if request.method == 'POST':
        # Gets information from the bootstrap form
        username = request.form.get('username')
        authcode = request.form.get('authcode')
        if username and authcode:
            # Checks whether the auth code has been sent
            if 'auth_code' not in session:
                flash('Please sends auth code to the email!')
                return render_template('user_forget.html', username=username)
            # Checks whether the user enters the correct auth code
            if authcode != session['auth_code']:
                flash('The auth code is not correct!')
                return render_template('user_forget.html', username=username)
            # Success!
            return redirect(url_for('user_reset_password',username=username))
        else:
            # Checks whether the information is complete
            flash('The information is not complete!')
            return render_template('user_forget.html', username=username)
    return render_template('user_forget.html')

@app.route('/user_reset_password/?<string:username>', methods=['GET', 'POST'])
def user_reset_password(username):
    """
    Helps the user retrieves his password
    :param username: the username
    """
    if request.method == 'POST':
        # Gets information from the bootstrap form
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        # Checks whether the two passwords match with each other
        if password != confirm:
            # Display the error
            flash('The two passwords do not match!')
            return render_template('user_reset_password.html')
        # Updates the password for the user
        user = User.query.filter_by(username=username).first()
        user.password = generate_password_hash(password, salt_length=8)
        db.session.commit()
        # Display the information
        flash('Successfully resets the password!')
        return render_template('user_login.html')
    return render_template('user_reset_password.html')

@app.route('/user_change_password', methods=['GET', 'POST'])
def user_change_password():
    """
    Helps the user changes his password
    """
    # Checks whether the user logs in
    if 'name' not in session:
        return render_template('not_login.html')
    if request.method == 'POST':
        # Gets information from the bootstrap form
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        # Checks whether the two passwords match with each other
        if password != confirm:
            # Display the error
            flash('The two passwords do not match!')
            return render_template('user_change_password.html')
        # Updates the password for the user
        user = User.query.filter_by(username=session['name']).first()
        user.password = generate_password_hash(password, salt_length=8)
        db.session.commit()
        # Display the information
        flash('Successfully changes the password!')
        return render_template('user_change_password.html')
    return render_template('user_change_password.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Logs the user out
    """
    if session.get('is_login'):
        # Clears the session
        session.clear()
        # Redirects to the home page
        return redirect('/')
    return redirect('/')

#################### Admin
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """
    Deals with the login of the admin
    """
    if request.method == 'POST':
        # Gets the information from the bootstrap form
        username = request.form.get('adminname')
        password = request.form.get('password')
        # Query the admin from the database based on his username
        user_info = Admin.query.filter_by(username=username).first()
        # Firstly checks whether the admin exists
        if user_info is None:
            # Display the error
            flash('Admin does not exist!')
            return render_template('admin_login.html')
        # Secondly checks whether the password is correct
        elif user_info.password != password:
            # Display the error
            flash('Wrong password!')
            return render_template('admin_login.html')
        # Records the information in the session
        session['is_login'] = True
        session['is_user'] = False
        session['is_admin'] = True
        session['name'] = username
        # Redirects to the admin home page
        return redirect('/admin')
    return render_template('admin_login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """
    The admin home page
    (1) Display all the user information
    (2) Enables the admin to add a new user
    """
    # Checks whether the admin logs in
    if 'name' not in session:
        return render_template('not_login.html')
    return render_template('admin.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registers a new user
    """
    # Checks whether the admin logs in
    if 'name' not in session:
        return render_template('not_login.html')
    if request.method == 'POST':
        # Gets the information from the bootstrap form
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        email = request.form.get('email')
        # Checks whether all the information is complete
        if username and password and confirm and email:
            # Checks whether the two passwords match with each other
            if password != confirm:
                # Display the error
                flash('The two passwords do not match!')
                return render_template('register.html', username=username)
            # Checks whether the username already exists
            sameUser = User.query.filter_by(username=username).first()
            if sameUser:
                # Display the error
                flash('The username already exists!')
                return render_template('register.html', username=username)
            # Adds a new user to the database
            newUser = User(
                username = username,
                password = generate_password_hash(password, salt_length=8),
                email = email
            )
            db.session.add(newUser)
            db.session.commit()
            # Display the information
            flash('Success!')
            return render_template('register.html')
        else:
            # Displays the error
            flash('You need to enter all of them!')
            if username:
                return render_template('register.html', username=username)
            return render_template('register.html')
    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    """
    An endpoint to register a user automatically
    """
    if request.method == 'POST':
        # Parameters are not allowed to be appended to the URL
        if request.args:
            return jsonify({
                "success": False,
                "error": {
                    "code": "servererrorcode",
                    "message": "Parameters are not allowed to be appended to the URL!"
                }
            })
        # Gets the information from the HTTP request body
        username = request.values.get('username')
        password = request.values.get('password')
        # Checks whether all the information is complete
        if username and password:
            # Checks whether the user already exists
            sameUser = User.query.filter_by(username=username).first()
            if sameUser:
                # Returns the response of failure
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "servererrorcode",
                        "message": "The user already exists!"
                    }
                })
            # Adds the user to the database
            newUser = User(
                username=username,
                password=generate_password_hash(password, salt_length=8),
                email="default@mail.utoronto.ca"
            )
            db.session.add(newUser)
            db.session.commit()
            # Returns the response of success
            return jsonify({
                'success': True
            })
        else:
            # Returns the response of failure
            return jsonify({
                "success": False,
                "error": {
                    "code": "servererrorcode",
                    "message": "The username and the password should be entered!"
                }
            })

#################### Mask Detection
baseDir = os.path.abspath(os.path.dirname(__file__))
uploadDir = os.path.join(baseDir, 'static/uploads')
@app.route('/mask_detect', methods=['GET', 'POST'])
def mask_detect():
    """
    Detects masks in the picture
    """
    # Checks whether the user logs in
    if 'name' not in session:
        return render_template('not_login.html')
    if request.method == 'POST':
        file = request.files.get('fileUpload')
        if not os.path.exists(uploadDir):
            os.makedirs(uploadDir)
        # Checks whether a file is selected
        if file:
            fileName = secure_filename(file.filename)
            # Checks whether it is a picture
            types = ['jpeg', 'jpg', 'png', 'tif', 'bmp']
            if fileName.split('.')[-1] in types:
                # Regenerates file name randomly
                fileName = str(uuid.uuid4().hex) + '.' + str(fileName.split('.')[-1])
                uploadPath = os.path.join(uploadDir, fileName)
                # Saves original image
                file.save(uploadPath)
                # Processes the image
                image = cv2.imread(uploadPath)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                # Gets output from Face Mask Detection
                detectionData = inference(image, show_result=False, target_shape=(360, 360))
                newImage = Image.fromarray(detectionData[-1])
                # Saves new image
                newImage.save(uploadPath)
                # Categories the image
                # 0: No face
                # 1: All faces wear masks
                # 2: All faces not wear masks
                # 3: Some faces wear masks
                withMasks = 0
                withoutMasks = 0
                number_of_faces = len(detectionData)-1
                for face in detectionData[:-1]:
                    if face[0] == 0:
                        withMasks += 1
                    else:
                        withoutMasks += 1
                category = -1
                if number_of_faces == 0:
                    category = 0
                elif withMasks == number_of_faces:
                    category = 1
                elif withoutMasks == number_of_faces:
                    category = 2
                else:
                    category = 3
                # Stores the category and path into database
                newFaceImage = FaceImage(
                    category=category,
                    path=uploadPath
                )
                db.session.add(newFaceImage)
                db.session.commit()
                # Display success
                flash('Upload successfully!')
                return render_template('mask_detect.html',
                                       imageName = fileName,
                                       withMasks=withMasks,
                                       withoutMasks=withoutMasks,
                                       number_of_faces=number_of_faces)
            else:
                flash('Unknown types!')
                return render_template('mask_detect.html')
        else:
            flash('No file selected!')
            return render_template('mask_detect.html')
    return render_template('mask_detect.html')

#################### Error Handler
@app.errorhandler(404)
def page_not_found(error):
    """
    Deals with the 404 error
    """
    return render_template('404.html')

@app.errorhandler(500)
def internal_error(error):
    """
    Deals with the 500 error
    """
    return render_template('500.html')

#################### Mail
@app.route('/email', methods=['GET', 'POST'])
def email():
    """
    Sends auth code to the user email to help the user retrieve the password
    """
    if request.method == 'POST':
        username = request.form.get('username')
        # Checks whether the username is entered
        if not username:
            flash('Please enter the username!')
            return render_template('user_forget.html')
        user = User.query.filter_by(username=username).first()
        # Checks whether the user exists
        if not user:
            flash('The user does not exist!')
            return render_template('user_forget.html')
        # Sends auth code to the email
        address = user.email
        # Randomly generates 8-byte auth code
        session['auth_code'] = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        message = Message(
            subject='Password Retrieval',
            sender='ece1779@163.com',
            recipients=[address],
            html = render_template('email.html', auth_code=session['auth_code'])
        )
        mail.send(message)
        msg = "Successfully sends auth code to " + address
        # Displays the email address
        flash(msg)
        return render_template('user_forget.html', username=username)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
