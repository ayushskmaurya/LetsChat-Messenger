document.getElementById("chat-window").style.height = (window.innerHeight - 50 - 70).toString() + "px";
$(document).ready(function() {
	$("#message").keydown(function(event) {
		if (event.keyCode === 13)
			$("#send").click();
	});
});

// Displaying user chats and chat box wrt to window size
const chatsDiv = document.getElementById("chats");
const chatBoxDiv = document.getElementById("chat-box");
const mediaQuery = window.matchMedia('(max-width: 575px)');
var showUserChats = true;

window.onresize = function() {
	document.getElementById("chat-window").style.height = (window.innerHeight - 50 - 70).toString() + "px";

	if (mediaQuery.matches) {
		if(showUserChats) {
			chatBoxDiv.style.display = "none";
			chatsDiv.style.display = "block";
		}
		else {
			chatsDiv.style.display = "none";
			chatBoxDiv.style.display = "block";
		}
	}
	else {
		chatsDiv.style.display = "block";
		chatBoxDiv.style.display = "block";
	}
};

function back_button() {
	chatBoxDiv.style.display = "none";
	chatsDiv.style.display = "block";
	showUserChats = true;
}

// Show error if occured while creating contact
function showError(errorCreateContact) {
	document.getElementById("errorCreateContact").innerHTML = errorCreateContact;
	document.getElementById("errorCreateContact").style.display = "block";
}

// Validating existence of user while creating contact &
// Creating contact if valid user
function createContact() {
	let uname = document.getElementById("uname").value.trim();
	if(uname.length === 0)
		showError("Please enter username.");
	
	else {
		$.ajax({
			url: "/create_contact",
			method: "POST",
			data: {uname:uname},
			success: function(status) {
				if(status == "1")
					window.location.replace("/chat");
				else
					showError(status);
			}
		});
	}
}

// Message format
function msgFormat(who) {
	let msgDiv = document.createElement("DIV");
	if(who == 0)
		msgDiv.className = "msg-container";
	else
		msgDiv.className = "msg-container smsg-container";
	return msgDiv;
}

// Retrieving chats
function retrieve_chats(chatid) {
	$.ajax({
		url: "/retrieve_chats",
		method: "POST",
		data: {chatid:chatid, msgCnt:msgCnt},
		success: function(msgData) {
			for(let data of msgData) {
				let msg_dt;
				let msgClass;
				
				let msgDiv = msgFormat(data['who']);
				if(data['who'] == 0)
					msgClass = "msg rmsg";
				else
					msgClass = "msg smsg";
					
				msg_dt = "<div class='" + msgClass + "'>";
				msg_dt += data['message'];
				msg_dt += "<span class='dt'>" + data['date_time'] + "</span>";
				msg_dt += "</div>";
				
				msgDiv.innerHTML = msg_dt;
				document.getElementById("chat-window").appendChild(msgDiv);

				$("#chat-window").animate({ 
                    scrollTop: document.getElementById("chat-window").scrollHeight 
                }, 0); 

				msgCnt++;
			}
		}
	});
}

// Chat Window
var msgCnt = 0;
var ID = 0;
function chat(chatid, user, img_status) {

	if(window.innerWidth < 576) {
		chatsDiv.style.display = "none";
		chatBoxDiv.style.display = "block";
		showUserChats = false;
	}

	document.getElementById("chat-window").innerHTML = "";
	msgCnt = 0;
	window.clearInterval(ID);
	ID = window.setInterval(retrieve_chats, 1000, chatid);

	document.getElementById("set-user-profile-img").setAttribute("onclick", "viewProfilePhoto('" + user + "');");
	set_profile_photo("user-profile-img", "user-default-profile-img", "set-user-profile-img", user, img_status);
	document.getElementById("user-name").innerHTML = user;
	document.getElementById("current-user").style.display = "block";
	document.getElementById("clear-chat").setAttribute("onclick", "clear_chat('" + chatid + "', '" + user + "', '" + img_status + "');");
	document.getElementById("export-chat").setAttribute("onclick", "export_chat('" + chatid + "');");

	document.getElementById("message").value = "";
	document.getElementById("send").setAttribute("onclick", "sendMsg('"+ chatid +"')");
}

// Clearing chat
function clear_chat(chatid, user, img_status) {
	$("#clearChatModal").modal("hide");
	$.ajax({
		url: "/clear_chat",
		method: "POST",
		data: {chatid:chatid},
		success: function() {	
			chat(chatid, user, img_status);
		}
	});
}

// Exporting chat
function export_chat(chatid) {
	$.ajax({
		url: "/export_chat",
		method: "POST",
		data: {chatid:chatid},
		success: function(data) {	
			let download_link = document.createElement('a');
			download_link.href = data['filename'];
			download_link.download = "Chat with " + data['user2name'];
			document.body.appendChild(download_link);
			download_link.click();
			document.body.removeChild(download_link);
		}
	});
}

// Closing contact modal
function chatWithContact(chatid, user, img_status) {
	$("#contactsModal").modal("hide");
	chat(chatid, user, img_status);
}

// Sending Message
function sendMsg(chatid) {
	let msg = document.getElementById("message").value.trim();
	if(msg.length !== 0) {
		$.ajax({
			url: "/send_message",
			method: "POST",
			data: {chatid:chatid, msg:msg},
			success: function() {
				document.getElementById("message").value = "";
			}
		});
	}
}

// View Profile Photo of any user
function viewProfilePhoto(user) {
	document.getElementById("viewProfilePhoto").src = "/static/profile_photos/" + user + ".jpg";
	$('#viewProfilePhotoModal').modal('show'); 
}
