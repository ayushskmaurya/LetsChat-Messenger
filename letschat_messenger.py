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
	contactid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	contactname = db.Column(db.String(100), nullable=False)


class Messages(db.Model):
	msgid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	user1id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	user2id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	message = db.Column(db.Text)
	date_time = db.Column(db.DateTime, nullable=False)


class Chats_count(db.Model):
	chatid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	user1id = db.Column(db.Integer, db.ForeignKey('messages.user1id'), nullable=False)
	user2id = db.Column(db.Integer, db.ForeignKey('messages.user2id'), nullable=False)
	msgCount = db.Column(db.Integer, nullable=False)
	clrCountUser1id = db.Column(db.Integer, default=0, nullable=False)
	clrCountUser2id = db.Column(db.Integer, default=0, nullable=False)


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
	uname = request.form['uname']

	if uname == session['username']:
		return "Please enter valid username."
	
	else:
		user = db.session.query(Contacts.contactid).filter_by(userid=session['userid'], contactname=uname).first()
		if user is not None:
			return "Contact already created."
		
		else:
			user = db.session.query(Users.userid).filter_by(username=uname).first()
			if user is None:
				return "User " + uname + " doesn't exist."
		
			else:
				contact = Contacts(userid=session['userid'], contactname=uname)
				db.session.add(contact)
				db.session.commit()
				return "1"


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
	userid = request.form['userid']

	# Retrieving message count between two users
	sql = "SELECT * FROM chats_count WHERE user1id IN (:u1id, :u2id) AND user2id IN (:u1id, :u2id)"
	row = db.session.execute(sql, {'u1id': session['userid'], 'u2id': userid})
	data = next(row, None)

	if data is not None:
		chat_count = Chats_count.query.get_or_404(data['chatid'])
		if data['user1id'] == session['userid']:
			chat_count.clrCountUser1id = data['msgCount']
		else:
			chat_count.clrCountUser2id = data['msgCount']

		cnt = min([chat_count.clrCountUser1id, chat_count.clrCountUser2id])
		chat_count.msgCount -= cnt
		chat_count.clrCountUser1id -= cnt
		chat_count.clrCountUser2id -= cnt

		if chat_count.msgCount == 0:
			db.session.delete(chat_count)
		db.session.commit()

		db.engine.execute("DELETE FROM messages WHERE msgid IN (SELECT msgid FROM messages WHERE user1id IN (:u1id, :u2id) AND user2id IN (:u1id, :u2id) ORDER BY date_time LIMIT :cnt)", {
			'u1id': session['userid'],
			'u2id': userid,
			'cnt': cnt
		})		

	return ""


# Retrieving chats
@app.route("/retrieve_chats", methods=['POST'])
def retrieve_chats():
	userid = request.form['userid']
	msgCnt = int(request.form['msgCnt'])
	remMsgCnt = 0

	# Retrieving message count between two users
	sql1 = "SELECT * FROM chats_count WHERE user1id IN (:u1id, :u2id) AND user2id IN (:u1id, :u2id)"
	row1 = db.session.execute(sql1, {'u1id': session['userid'], 'u2id': userid})
	data1 = next(row1, None)

	if data1 is not None:
		remMsgCnt = data1['msgCount']
		msgCnt += data1['clrCountUser1id'] if data1['user1id'] == session['userid'] else data1['clrCountUser2id']
	remMsgCnt -= msgCnt

	# Retrieving messages between two users
	sql2 = "SELECT user1id, message, date_time FROM messages WHERE user1id IN (:u1id, :u2id) AND user2id IN (:u1id, :u2id) ORDER BY date_time LIMIT :msgCnt, :remMsgCnt"
	row2 = db.session.execute(sql2, {
		'u1id': session['userid'],
		'u2id': userid,
		'msgCnt': msgCnt,
		'remMsgCnt': remMsgCnt
	})

	msgData = []
	for data in row2:
		msgData.append({
			'message': escape(data['message']),
			'date_time': data['date_time'][:19],
			'who': 1 if data['user1id'] == session['userid'] else 0
		})
	return jsonify(msgData)


# Sending Message
@app.route("/send_message", methods=['POST'])
def send_message():
	userid = request.form['userid']
	msg = request.form['msg']
	
	# Inserting message into database table
	message = Messages(user1id=session['userid'], user2id=userid, message=msg, date_time=datetime.now())
	db.session.add(message)
	db.session.commit()
	
	# Retrieving message count between two users
	sql = "SELECT chatid, msgCount FROM chats_count WHERE user1id IN (:u1id, :u2id) AND user2id IN (:u1id, :u2id)"
	row = db.session.execute(sql, {'u1id': session['userid'], 'u2id': userid})
	data = next(row, None)

	# If it's first time that two users are chatting
	# then inserting message count as 1
	if data is None:
		chat_count = Chats_count(user1id=session['userid'], user2id=userid, msgCount=1)
		db.session.add(chat_count)
		db.session.commit()

	# If two users had a chat before
	# then updating message count by incrementing the current count by 1
	else:
		chat_count = Chats_count.query.get_or_404(data['chatid'])
		chat_count.msgCount += 1
		db.session.commit()

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
		sql1 = "SELECT userid, username, profile_img_status FROM users WHERE "
		sql1 += "userid IN (SELECT user1id FROM chats_count WHERE user2id=:userid) OR "
		sql1 += "userid IN (SELECT user2id FROM chats_count WHERE user1id=:userid) "
		sql1 += "ORDER BY username"
		chats = db.session.execute(sql1, {'userid': session['userid']})

		name, profile_img_status = db.session.query(Users.name, Users.profile_img_status).filter_by(userid=session['userid']).first()

		sql2 = "SELECT users.userid, users.profile_img_status, contacts.contactname "
		sql2 += "FROM contacts INNER JOIN users ON contacts.contactname = users.username "
		sql2 += "WHERE contacts.userid = :userid ORDER BY contacts.contactname"
		contacts = db.session.execute(sql2, {'userid': session['userid']})

	return render_template("chat.html",
		cdt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:19],
		chats = chats,
		name = name,
		profile_img_status = profile_img_status,
		contacts = contacts,
		uname = session['username']
	)


@app.route("/signout")
def signout():
	if 'username' in session:
		session.pop('username', None)
		session.pop('userid', None)
	return redirect("/")


if __name__ == '__main__':
	app.run()
