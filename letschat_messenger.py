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


class Chats(db.Model):
	chatid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	user1id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	user2id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	msgCount = db.Column(db.Integer, nullable=False)


class Contacts(db.Model):
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	contactid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	chatid = db.Column(db.Integer, db.ForeignKey('chats.chatid'), nullable=False)


class Messages(db.Model):
	msgid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	chatid = db.Column(db.Integer, db.ForeignKey('chats.chatid'), nullable=False)
	senderid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	message = db.Column(db.Text)
	date_time = db.Column(db.DateTime, nullable=False)


class Cleared_chats(db.Model):
	clrid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
	chatid = db.Column(db.Integer, db.ForeignKey('chats.chatid'), nullable=False)
	msgid = db.Column(db.Integer, db.ForeignKey('messages.msgid'), nullable=False)


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
		user = db.session.query(Users.userid).filter_by(username=uname).first()

		if user is None:
			return "User " + uname + " doesn't exist."
		else:
			userid = user[0]
			existing_contact = db.session.query(Contacts.contactid).filter_by(userid=session['userid'], contactid=userid).first()
			
			if existing_contact is not None:
				return "Contact already created."
			else:
				existing_chat = db.session.query(Contacts.chatid).filter_by(userid=userid, contactid=session['userid']).first()
				
				if existing_chat is not None:
					chatid = existing_chat[0]
				else:
					chat = Chats(user1id=session['userid'], user2id=userid, msgCount=0)
					db.session.add(chat)
					db.session.commit()
					chatid = chat.chatid

				contact = Contacts(userid=session['userid'], contactid=userid, chatid=chatid)
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
	chatid = request.form['chatid']

	# Deleting the messages which are already cleared by other user
	cleared = db.session.query(Cleared_chats.msgid).filter(Cleared_chats.chatid == chatid, Cleared_chats.userid != session['userid']).all()
	chat = db.session.query(Chats).filter_by(chatid=chatid).first()
	for rec in cleared:
		msg = db.session.query(Messages).filter_by(msgid=rec.msgid).first()
		clr = db.session.query(Cleared_chats).filter_by(msgid=rec.msgid).first()
		
		if chat is not None and msg is not None and clr is not None:
			db.session.delete(msg)
			db.session.delete(clr)
			chat.msgCount -= 1
	db.session.commit()

	# Clearing the messages which are not cleared by other user
	sql = "SELECT msgid FROM messages WHERE chatid = :chatid AND msgid NOT IN "
	sql += "(SELECT msgid FROM cleared_chats WHERE chatid = :chatid AND userid = :userid)"
	row = db.session.execute(sql, {
		'chatid': chatid,
		'userid': session['userid']
	})
	for data in row:
		clr_msg = Cleared_chats(userid=session['userid'], chatid=chatid, msgid=data['msgid'])
		db.session.add(clr_msg)
	db.session.commit()

	return ""


# Exporting chat
@app.route("/export_chat", methods=['POST'])
def export_chat():	
	chatid = request.form['chatid']

	# Retrieving messages between two users
	sql1 = "SELECT senderid, message, date_time FROM messages WHERE chatid = :chatid AND msgid NOT IN "
	sql1 += "(SELECT msgid FROM cleared_chats WHERE chatid = :chatid AND userid = :userid) "
	sql1 += "ORDER BY date_time"
	row1 = db.session.execute(sql1, {
		'chatid': chatid,
		'userid': session['userid']
	})

	# Retrieving name of the user
	rec1 = db.session.query(Users.name).filter_by(userid=session['userid']).first()
	user1name = rec1.name if rec1 is not None else ""

	# Retrieving name of other user
	sql2 = "SELECT name FROM users WHERE userid = (SELECT "
	sql2 += "CASE WHEN user1id = :userid THEN user2id ELSE user1id END "
	sql2 += "AS userid FROM chats WHERE chatid = :chatid)"
	row2 = db.session.execute(sql2, {'userid': session['userid'], 'chatid': chatid})
	rec2 = next(row2, None)
	user2name = rec2.name if rec2 is not None else ""
	
	chat = ""
	for data in row1:
		chat += "[" + data['date_time'][:19] + "] - "
		chat += user1name if data['senderid'] == session['userid'] else user2name
		chat += ": " + data['message'] + "\n"
	
	filename = "static/export_chats/" + str(session['userid']) + "_" + str(chatid) + ".txt"
	with open(filename, 'w') as file:
		file.seek(0)
		file.truncate()
		file.write(chat)
	
	return {'filename': filename, 'user2name': user2name}


# Retrieving chats
@app.route("/retrieve_chats", methods=['POST'])
def retrieve_chats():
	chatid = request.form['chatid']
	msgCnt = int(request.form['msgCnt'])

	# Calculating count of remaining messages which are not retrieved yet
	data = db.session.query(Chats.msgCount).filter_by(chatid=chatid).first()
	remMsgCnt = data[0] if data is not None else 0
	remMsgCnt -= msgCnt
	
	# Retrieving messages between two users
	sql = "SELECT senderid, message, date_time FROM messages WHERE chatid = :chatid AND msgid NOT IN "
	sql += "(SELECT msgid FROM cleared_chats WHERE chatid = :chatid AND userid = :userid) "
	sql += "ORDER BY date_time LIMIT :msgCnt, :remMsgCnt"
	row = db.session.execute(sql, {
		'chatid': chatid,
		'userid': session['userid'],
		'msgCnt': msgCnt,
		'remMsgCnt': remMsgCnt
	})

	msgData = []
	for data in row:
		msgData.append({
			'message': escape(data['message']),
			'date_time': data['date_time'][:19],
			'who': 1 if data['senderid'] == session['userid'] else 0
		})
	return jsonify(msgData)
	

# Sending Message
@app.route("/send_message", methods=['POST'])
def send_message():
	chatid = request.form['chatid']
	msg = request.form['msg']

	message = Messages(chatid=chatid, senderid=session['userid'], message=msg, date_time=datetime.now())
	db.session.add(message)
	chat = Chats.query.get_or_404(chatid)
	chat.msgCount += 1
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
		# Retrieving all the chats of user
		sql1 = "SELECT c.chatid, u.username, u.profile_img_status FROM users u INNER JOIN "
		sql1 += "(SELECT chatid, CASE WHEN user1id = :userid THEN user2id WHEN user2id = :userid THEN user1id ELSE NULL END AS userid, msgCount FROM chats) AS c "
		sql1 += "ON u.userid = c.userid WHERE c.msgCount <> 0 ORDER BY u.username"
		chats = db.session.execute(sql1, {'userid': session['userid']})

		name, profile_img_status = db.session.query(Users.name, Users.profile_img_status).filter_by(userid=session['userid']).first()

		# Retrieving all the contacts of user
		sql2 = "SELECT c.chatid, u.username, u.profile_img_status "
		sql2 += "FROM users u INNER JOIN contacts c ON u.userid = c.contactid "
		sql2 += "WHERE c.userid = :userid ORDER BY u.username"
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
