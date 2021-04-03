import os
import time

path = "static/export_chats/"
local_time = time.time()

for filename in os.listdir(path):
	last_modified_time = os.path.getmtime(path + filename)
	hr = int((local_time - last_modified_time) / (60 * 60))

	if hr >= 24:
		os.remove(path + filename)

print("Exported chat files deleted successfully.")
