function set_profile_photo(img_id, default_img_id, set_id, user, img_status) {
	if (img_status == "1" || img_status == "True") {
		document.getElementById(default_img_id).style.display = "none";
		document.getElementById(set_id).src = "/static/profile_photos/" + user + ".jpg";
		document.getElementById(img_id).style.display = "inline-block";
	}
	else {
		document.getElementById(img_id).style.display = "none";
		document.getElementById(default_img_id).style.display = "inline-block";
	}
}
