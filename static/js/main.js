var isUsernameInvalid = false;
var isError = false;
var error;

// Show error if occured while signing in
function showError(errorSiginin) {
	document.getElementById("errorSignin").innerHTML = errorSiginin;
	document.getElementById("errorSignin").style.display = "block";
}

// Validating user inputs for signing in
function validateSignin() {
	let uname = document.getElementById("unameSignin").value.trim();
	let pwd = document.getElementById("pwdSignin").value;

	if(uname.length === 0)
		showError("Please enter username.");
	else if(pwd.length === 0)
		showError("Please enter password.");
	else {
		$.ajax({
			url: "/verify",
			method: "POST",
			data: {uname:uname, pwd:pwd},
			success: function(status) {
				if (status != "1")
					showError(status);
				else
					window.location.replace("/chat");
			}
		});
	}
}

// Validating the non-existence of username for new account creation
function validateUsername(uname) {
	isUsernameInvalid = false;
	unameStatus = document.getElementById("unameStatus");
	$.ajax({
		url: "/validate_username",
		method: "POST",
		data: {uname:uname},
		success: function(status) {
			if(status == "1") {
				isUsernameInvalid = true;
				unameStatus.innerHTML = "Username not available.";
				unameStatus.className = "unameStatus-invalid";
				document.getElementById("uname").className = "form-control input uname-invalid";
			}
			else {
				unameStatus.innerHTML = "Perfect!";
				unameStatus.className = "unameStatus-valid";
				document.getElementById("uname").className = "form-control input uname-valid";
			}
			unameStatus.style.display = "block";
		}
	});
}

function validate() {
	isError = false;
	let name = document.getElementById("name").value.trim();
	let uname = document.getElementById("uname").value.trim();
	let pwd = document.getElementById("pwd").value;
	let cpwd = document.getElementById("cpwd").value;

	// Validating user inputs for creating new account
	if(name.length === 0) {
		isError = true; 
		error = "Please enter your name.";
	}
	else if(uname.length === 0) {
		isError = true; 
		error = "Please enter username.";
	}
	else if(isUsernameInvalid) {
		isError = true; 
		error = "Sorry! The username you entered is not available. Please try again.";
	}
	else if(pwd.length === 0) {
		isError = true; 
		error = "Please enter password.";
	}
	else if(pwd !== cpwd) {
		isError = true; 
		error = "Passwords do not match.";
	}
	
	if(isError) {
		document.getElementById("errorCreate").innerHTML = error;
		document.getElementById("errorCreate").style.display = "block";
		isError = false;
	}
	else {
		// Creating new account
		$.ajax({
			url: "/create_account",
			method: "POST",
			data: {name:name, uname:uname, pwd:pwd},
			success: function(status) {
				if(status == "1")
					window.location.replace("/chat");
			}
		});
	}
}
