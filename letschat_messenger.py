from flask import Flask, render_template, request, session, redirect, escape, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from PIL import Image
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = str(random.randint(1111, 9999)).encode()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///letschat_messenger.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Declaring Models
class Created_key(db.Model):
	key = db.Column(db.String(255), primary_key=True)


class Users(db.Model):
	userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	name = db.Column(db.String(100), nullable=False)
	username = db.Column(db.String(100), unique=True, nullable=False)
	password = db.Column(db.String(255), nullable=False)
	profile_img_status = db.Column(db.Boolean, default=False, nullable=False)


class Contacts(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	contactid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)


class Chats(db.Model):
	chatid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	user1id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	user2id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	msgCount = db.Column(db.Integer, nullable=False)


class Messages(db.Model):
	msgid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	chatid = db.Column(db.Integer, db.ForeignKey('chats.chatid'), nullable=False)
	message = db.Column(db.Text)
	date_time = db.Column(db.DateTime, nullable=False)


# Generating key for encrypting and decrypting passwords
def create_key():
	if len(Created_key.query.all()) == 0:
		db.session.add(Created_key(key=Fernet.generate_key().decode()))
	db.session.commit()


# Verifying user credentials before signing in
@app.route("/verify", methods=['POST'])
def verify():
	uname = request.form['uname']
	pwd = request.form['pwd']
	
	user = db.session.query(Users.userid, Users.password).filter_by(username=uname).first()
	if user is None:
		return "Username doesn't exist."
	else:
		# Decrypting user password
		key = Created_key.query.first().key.encode()
		f = Fernet(key)
		decrypted_pwd = f.decrypt(user[1].encode()).decode()
		
		if decrypted_pwd != pwd:
			return "Incorrect pasword."
		else:
			session['username'] = uname
			session['userid'] = user[0]
	return "1"


# Validating the non-existence of username for new account creation
@app.route("/validate_username", methods=['POST'])
def validate_username():
	uname = request.form['uname']

	userid = db.session.query(Users.userid).filter_by(username=uname).first()
	if userid is not None:
		return "1"
	return "0"


# Creating new account
@app.route("/create_account", methods=['POST'])
def create_account():
	name = request.form['name']
	uname = request.form['uname']
	pwd = request.form['pwd']

	# Encrypting password	
	key = Created_key.query.first().key.encode()
	f = Fernet(key) 
	encrypted_pwd = f.encrypt(pwd.encode()).decode()
	# Inserting user record
	user = Users(name=name, username=uname, password=encrypted_pwd)
	db.session.add(user)
	db.session.commit()

	session['username'] = uname
	session['userid'] = user.userid
	return "1"


# Validating existence of user while creating contact &
# Creating contact if valid user
@app.route("/create_contact", methods=['POST'])
def create_contact():
	return ""


# Uploading user's profile photo.
@app.route("/upload_profile_photo", methods=['POST'])
def upload_profile_photo():
	photo = Image.open(request.files['profile-photo'])
	photo = photo.convert('RGB')
	size = min(photo.size)
	profile_photo = photo.crop((0, 0, size, size))

	photo_name = str(session['username']) + ".jpg"
	filename = os.path.join("static\\profile_photos", photo_name)
	profile_photo.save(filename)

	user = Users.query.get_or_404(session['userid'])
	user.profile_img_status = True
	db.session.commit()
	
	return redirect("/chat")


# Clearing chat
@app.route("/clear_chat", methods=['POST'])
def clear_chat():
	return ""


# Exporting chat
@app.route("/export_chat", methods=['POST'])
def export_chat():	
	return ""


# Retrieving chats
@app.route("/retrieve_chats", methods=['POST'])
def retrieve_chats():
	return ""


# Sending Message
@app.route("/send_message", methods=['POST'])
def send_message():
	return ""


@app.route("/")
def index():
	if 'username' in session:
		return redirect("/chat")
	return render_template("index.html")


@app.route("/chat")
def chat():
	if 'username' not in session:
		return redirect("/")
	
	else:
		return render_template("chat.html")


@app.route("/signout")
def signout():
	if 'username' in session:
		session.pop('username', None)
		session.pop('userid', None)
	return redirect("/")


if __name__ == '__main__':
	app.run()
