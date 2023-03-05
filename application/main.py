from flask import request
from datetime import datetime, timedelta
from crontab import CronTab
import os
import ftplib, ssl
import magic
import ast
import requests
from requests.auth import HTTPDigestAuth

# Import Local Files
from admin import retrieve_glob_var, retrieve_arkime_var


########## START Data Transfer (Smart Meter): Initiate FTP ##########

# Source: https://stackoverflow.com/questions/48260616/python3-6-ftp-tls-and-session-reuse
class MyFTP_TLS(ftplib.FTP_TLS):
	"""Explicit FTPS, with shared TLS session"""
	def ntransfercmd(self, cmd, rest=None):
		conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
		if self._prot_p:
			session = self.sock.session
			if isinstance(self.sock, ssl.SSLSocket):
				session = self.sock.session
			conn = self.context.wrap_socket(conn, server_hostname=self.host, session=session)
		return conn, size


def initiate_ftp(ftp_dir):
	endpoint = request.referrer.split("/")[-1]
	if endpoint == "smart_meter":
		# Initiate FTP for Smart Meter
		print("Initiate FTP for Smart Meter")
		success, dir_list = windows_ftp_start(ftp_dir)
	elif endpoint == "t_pot":
		# Initiate FTP for T-Pot
		files = ""
		print("Initiate FTP for T-Pot")
	else:
		files = ""
	
	if not success:
		return False, dir_list
	return True, dir_list


def windows_ftp_start(ftp_dir):
	if ftp_dir == "SmartMeterData":
		ftp_dir = ["SmartMeterData", "Archive_SmartMeterData"]
	else:
		ftp_dir = [ftp_dir]

	dir_list = []		# Store Dir & corresponding Filenames
	for root_dir in ftp_dir:
		try:
			global_dict = retrieve_glob_var()
			ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
			ftps.prot_p()		# Set up secure connection
			root = ftps.mlsd(root_dir)	# FTP Root directory
			if root_dir == "WiresharkData":
				ftps.quit()
				return True, "Wireshark"
		except Exception as e:
			try:
				ftps.quit()
			except Exception as econn:
				print("Smart Meter Windows machine is NOT online.")
				return False, e
			print("FTP Connection Error: {}".format(e))
			return False, e

		try:
			for dir_name in root:
				# dir_name[0] = dir/filename
				# dir_name[1] = dir/file data
				##print("Dir: {}".format(dir_list[0]))		# Print Dir
				if dir_name[1]["type"] == "dir":
					if dir_name[0] not in dir_list:
						dir_list.append(dir_name[0])
			ftps.quit()
		except Exception as e:
			ftps.quit()
			print("File Permissions Error: {}".format(e))
			##print("Dict: {}".format(dir_list))	# Print stored list
			return False, e

	print("List: {}".format(dir_list))	# Print stored list
	return True, dir_list


########## END Data Transfer (Smart Meter): Initiate FTP ##########
########## START Data Transfer (Smart Meter): Transfer Data ##########

def windows_ftp_process(form):
	print("data_source: {}".format(form.data_source.data))
	print("meters: {}".format(form.meters.data))
	#print("file_type: {}".format(form["file_type"]))
	success, file_dict = windows_ftp_initiate(form.data_source.data, form.meters.data, form.wireshark_source.data)
	if not success:
		return success, file_dict

	print("date: {}".format(form.date.data))
	print("start_time: {}".format(form.start_time.data))
	print("end_time: {}".format(form.end_time.data))
	success, file_dict = windows_ftp_filter_datetime(form.data_source.data, form.date.data, form.start_time.data, form.end_time.data, file_dict)
	if not success:
		return success, file_dict

	success, message = windows_ftp_transfer(form.data_source.data, file_dict)

	#print("export_name: {}".format(form["export_name"]))
	return success, message


def windows_ftp_initiate(ftp_dir, meters, wireshark_src):
	file_dict = {}		# Store Dir & corresponding Filenames

	if ftp_dir == "SmartMeterData":
		ftp_dir = ["SmartMeterData", "Archive_SmartMeterData"]
	else:
		ftp_dir = [ftp_dir]

	import time
	start = time.time()
	global_dict = retrieve_glob_var()
	ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
	ftps.prot_p()		# Set up secure connection
	for root_dir in ftp_dir:
		try:
			#global_dict = retrieve_glob_var()
			#ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
			#ftps.prot_p()		# Set up secure connection
			root = ftps.mlsd(root_dir)	# FTP Root directory
			if root_dir == "WiresharkData":
				file_dict[root_dir] = []
		except Exception as e:
			try:
				ftps.quit()
			except Exception as econn:
				print("Smart Meter Windows machine is NOT online.")
				return False, e
			print("FTP Connection Error: {}".format(e))
			return False, e

		try:
			for dir_list in root:
				if root_dir == "WiresharkData":
					print(dir_list[0])
					if wireshark_src == dir_list[0].split(".")[0].split("_")[-1]:
						file_dict[root_dir] += [dir_list[0]]
				elif dir_list[0] in meters:
					# dir_list[0] = dir/filename
					# dir_list[1] = dir/file data
					##print("Dir: {}".format(dir_list[0]))		# Print Dir
					if dir_list[1]["type"] == "dir":
						directory = root_dir + "/" + dir_list[0]
						file_dict[directory] = []
						file_list = ftps.mlsd(directory)
						for data in file_list:
							##print("File: {}".format(data[0]))	# Print Filename
							file_dict[directory] += [data[0]]
			#ftps.quit()
		except Exception as e:
			ftps.quit()
			print("File Permissions Error: {}".format(e))
			##print("Dict: {}".format(file_dict))	# Print stored dictionary
			return False, e
	try:
		ftps.quit()
	except Exception as e:
		print("Unable to end FTP connection gracefully: {}".format(e))
		return False, e

	end = time.time()
	print(end-start)
	##print("Dict: {}".format(file_dict))	# Print stored dictionary
	return True, file_dict


def windows_ftp_filter_datetime(data_source, date, start_time, end_time, file_dict):
	filtered_dict = {}
	start_datetime = datetime.combine(date, start_time) - timedelta(hours=8)
	start_date = start_datetime.strftime("%Y%m%d")
	start_time = int(start_datetime.strftime("%H%M%S"))
	end_datetime = datetime.combine(date, end_time) - timedelta(hours=8)
	end_date = end_datetime.strftime("%Y%m%d")
	end_time = int(end_datetime.strftime("%H%M%S"))
	if end_datetime < start_datetime:
		return False, "Start Datetime cannot be later than End Datetime"

	print("start_date: {}".format(start_date))
	print("start_time: {}".format(start_time))
	print("end_date: {}".format(end_date))
	print("end_time: {}".format(end_time))

	for meter in file_dict:
		filtered_dict[meter] = []
		for csv_file in file_dict[meter]:
			filtered_date_file = csv_file.split("_")[0]
			##print(start_date, filtered_date_file)	# Print Filtered Date & Date of selected .csv file

			if data_source == "WiresharkData":
				filtered_time_file = int("{}00".format(csv_file.split("_")[1].split(".")[0]))
			else:
				filtered_time_file = int(csv_file.split("_")[1].split(".")[0])
			# Filter .csv filename if date is same
			if start_date == end_date == filtered_date_file:
				# Store .csv filename if Start time <= filtered range <= End time
				if (start_time <= filtered_time_file) and (filtered_time_file <= end_time):
					##print("{} <= {} <= {}".format(start_time, filtered_time_file, end_time))	# Print Filtered Start-End times & Time of selected .csv file
					filtered_dict[meter] += [csv_file]
			else:
				if filtered_date_file == start_date:
					# Store .csv filename if Start time <= filtered range <= 235959
					if (start_time <= filtered_time_file) and (filtered_time_file <= 235959):
						##print("{} <= {} <= 235959".format(start_time, filtered_time_file))	# Print Filtered Start-End times & Time of selected .csv file
						filtered_dict[meter] += [csv_file]

				elif filtered_date_file == end_date:
					# Store .csv filename if 000000 <= filtered range <= End time
					if (000000 <= filtered_time_file) and (filtered_time_file <= end_time):
						##print("000000 <= {} <= {}".format(filtered_time_file, end_time))	# Print Filtered Start-End times & Time of selected .csv file
						filtered_dict[meter] += [csv_file]

	return True, filtered_dict


# Download filtered files from file_dict via FTP
def windows_ftp_transfer(data_source, file_dict, job_name=None):
	download_dir = ""
	download_cnt = 0	# Count number of files downloaded
	directory_cnt = 0	# Count number of directories downloaded into
	##print("file_dict: {}".format(file_dict))

	try:
		# Download files via FTPS
		global_dict = retrieve_glob_var()
		ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
		ftps.prot_p()		# Set up secure connection
		current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		import time
		for directory in file_dict:
			if len(file_dict[directory]) == 0:
				continue
			ftps.cwd("/"+directory)		# Change FTP directory
			current_dir = os.getcwd()
			if job_name is not None:	# job_name taken from Job Schedule
				download_dir = "{}/FTP_Downloads/Smart_Meter/{}/{}/{}/{}".format("/".join(current_dir.split("/")[:-2]), data_source, job_name, current_datetime, directory.split("/")[1])
			else:
				download_dir = "{}/FTP_Downloads/Smart_Meter/{}/{}/{}".format("/".join(current_dir.split("/")[:-2]), data_source, current_datetime, directory.split("/")[1])
			if not os.path.isdir(download_dir):		# Mkdir if Download directory does not exist
				os.makedirs(download_dir)
			os.chdir(download_dir)		# Change Download directory

			print("Downloading files for {}.".format(directory))
			start_dur = time.time()
			for csv_file in file_dict[directory]:	# Download every selected file from this FTP directory
				with open(csv_file, "wb") as f:
					# Command for Downloading the file "RETR csv_file"
					ftps.retrbinary(f"RETR {csv_file}", f.write)
					download_cnt += 1
			end_dur = time.time()
			print("Downloaded {} files so far in {} seconds.".format(download_cnt, end_dur-start_dur))
			directory_cnt += 1
			os.chdir(current_dir)		# Revert to CWD

	except Exception as e:
		print("Error Downloading File: {}".format(e))
		return False, e

	ftps.quit()
	download_folder = download_dir.split("/")[-1]
	download_path = "/".join(download_dir.split("/")[:-1])	# Re-store the Download directory
	#message = [download_cnt, directory_cnt, "/".join(download_dir.split("/")[:-1])]
	message = [download_cnt, download_folder, download_path]
	return True, message


########## END Data Transfer (Smart Meter): Transfer Data ##########
########## START Data Transfer (Smart Meter): Schedule Transfer ##########

def windows_ftp_automate(form):
	print("data_source: {}".format(form.data_source.data))
	print("meters: {}".format(form.meters.data))
	print("start_time: {}".format(form.start_time.data))
	print("transfer_dur: +{} minutes".format(form.transfer_dur.data))	# end_time = start_time + transfer_dur
	end_time = (datetime.combine(form.date.data, form.start_time.data) + timedelta(minutes=int(form.transfer_dur.data))).strftime("%H:%M:%S")
	print("end_time: {}".format(end_time))
	print("job_name: {}".format(form.job_name.data))

	#print("date: {}".format(form.date.data))	# Cron should not have date as it is an ongoing basis. If no date specified, default param should be today's date.

	# Cron Params: schedule, command, comment
	## schedule: freq, week/month, scheduled_time
	## command: data_source, meters, start_time, end_time
	## comment: job_name

	print("transfer_freq: {}".format(form.transfer_freq.data))	# For Cron
	if form.transfer_freq.data == "Daily":
		print("transfer_freq_time: {}".format(form.transfer_freq_time.data))
		success, cron, job = cronjob_format(
			"daily", None, form.transfer_freq_time.data, form.job_name.data,
			form.data_source.data, form.meters.data, form.start_time.data, end_time)
	elif form.transfer_freq.data == "Weekly":
		print("transfer_freq_week: {}".format(form.transfer_freq_week.data))
		print("transfer_freq_week_time: {}".format(form.transfer_freq_week_time.data))
		if not form.transfer_freq_week.data:
			return False, "Unspecified Parameters", "Please ensure your parameters are selected."
		success, cron, job = cronjob_format(
			"weekly", form.transfer_freq_week.data, form.transfer_freq_week_time.data, form.job_name.data,
			form.data_source.data, form.meters.data, form.start_time.data, end_time)
	elif form.transfer_freq.data == "Monthly":
		print("transfer_freq_month: {}".format(form.transfer_freq_month.data))
		print("transfer_freq_month_time: {}".format(form.transfer_freq_month_time.data))
		success, cron, job = cronjob_format(
			"monthly", form.transfer_freq_month.data, form.transfer_freq_month_time.data, form.job_name.data,
			form.data_source.data, form.meters.data, form.start_time.data, end_time)
	else:
		return False, "Unspecified Parameters", "Please ensure your parameters are selected."

	return success, cron, "{}-Duration of Data To Collect: {} minutes".format(job, form.transfer_dur.data)


""" References:
https://pypi.org/project/python-crontab/
https://crontab.guru/
sudo cat /var/spool/cron/crontabs/user
date
crontab -l"""
def cronjob_format(freq, week_month, sched_time, job_name, data_source, meters, start_time, end_time):
	# Every job requires: frequency, week/month, scheduled_time, job_name, data_source, meters, start_time, end_time
	sched_time = str(sched_time)

	# Initialise Cron
	root_cron = CronTab(user=retrieve_glob_var()["cron_user"])
	##root_cron.remove_all()
	##root_cron.write()

	# Creating a new job
	job = root_cron.new(command="cd {} && /usr/bin/python3 -c 'from main import cronjob_process; cronjob_process(\"{}\", \"{}\", \"{}\", \"{}\")' >> {}/jobs_completed.txt".format(os.getcwd(), data_source, meters, start_time, end_time, os.getcwd()), comment=job_name)

	if data_source == "SmartMeterData":
		job_message = "Job Name: {}-Data Source: {}-Meters: {}-Data Start Time: {}-Data End Time: {}".format(job_name, data_source, meters, start_time, end_time)
	else:
		job_message = "Job Name: {}-Data Source: {}-Data Start Time: {}-Data End Time: {}".format(job_name, data_source, start_time, end_time)

	hour = sched_time.split(":")[0]
	minute = sched_time.split(":")[1]

	# Setting up restrictions for the job
	match freq:
		case "daily":
			# The job takes place at x time every day
			job.minute.on(minute)
			job.hour.on(hour)
			cron_message = "{}:{}H every day".format(hour, minute)
		case "weekly":
			# The job takes place at x time on [y]-day of the week
			job.minute.on(minute)
			job.hour.on(hour)
			job.dow.on(*week_month, )
			cron_message = "{}:{}H every {}".format(hour, minute, ", ".join(week_month))
		case "monthly":
			# The job takes place at x time on the zth day of the month
			job.minute.on(minute)
			job.hour.on(hour)
			job.dom.on(week_month)
			cron_message = "{}:{}H on every {} day of the month".format(hour, minute, week_month)

	# Clearing the restrictions of a job
	##job.clear()
	##root_cron.remove_all()

	try:
		root_cron.write()
	except Exception as e:
		print("Error writing Cron job: {}\nJob: {}".format(e, job))
		job.clear()
		return False, e, job_message

	return True, cron_message, job_message


def cronjob_process(data_source, meters, start_time, end_time):
	# Data1: 'WiresharkData', [], '07:00:00', '12:00:00'	>> 2 files downloaded
	# cd /home/user/Desktop/BlueTeam/venv_2/ICT3211_BlueTeamPlatform/application && python3 -c "from main import cronjob_process; cronjob_process('WiresharkData', [], '07:00:00', '12:00:00')"

	# Data2: 'SmartMeterData', ['Meter1', 'Meter2'], '07:00:00', '12:00:00'	>> 4 files downloaded
	# cd /home/user/Desktop/BlueTeam/venv_2/ICT3211_BlueTeamPlatform/application && python3 -c "from main import cronjob_process; cronjob_process('SmartMeterData', ['Meter1', 'Meter2'], '07:00:00', '12:00:00')"

	# Artificially-inserted value for "date" parameter
	from datetime import date
	date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
	
	##date = datetime.strptime("2023-02-01", "%Y-%m-%d")	# For demo purpose only
	
	start_time = datetime.strptime(start_time, "%H:%M:%S").time()
	end_time = datetime.strptime(end_time, "%H:%M:%S").time()

	success, file_dict = windows_ftp_initiate(data_source, meters)
	if not success:
		print("Cron unable to initiate FTP: {}".format(file_dict))

	success, file_dict = windows_ftp_filter_datetime(date, start_time, end_time, file_dict)
	if not success:
		print("Cron unable to download files: {}".format(file_dict))

	success, message = windows_ftp_transfer(data_source, file_dict)
	print("Cron Job Success: {}".format(message))


########## END Data Transfer (Smart Meter): Schedule Transfer ##########
########## START Data Transfer (Smart Meter): Manage Schedules ##########

def retrieve_cronjobs():
	# [{"id": "1", "name": "Job One", "data_source": "SmartMeterData", "meters": "['meter1', 'meter2']", "start_time": "12:00", "end_time": "12:30"}]

	cron_list = []
	job_id = 0

	try:
		# Initialise Cron
		root_cron = CronTab(user=retrieve_glob_var()["cron_user"])
	except Exception as e:
		print("Cron User Error: {}".format(e))
		return "Cron User Error"

	for job in root_cron:
		job_id += 1
		try:
			parameters = job.command.split(">>")[0].split("cronjob_process")[2].split("\", \"")
		except Exception as e:
			print("Cron Split Error (Job ID: {}): {}".format(job_id, e))
			continue
		job_enabled = str(job)[0]

		meters = parameters[1].strip("\"()' ")
		if meters == "[]":
			meters = "-"
		meter_list = ast.literal_eval(meters)
		meters = ", ".join(meter_list)

		sched = str(job).split(" cd ")[0].split(" ")
		if job_enabled == "#":
			sched.pop(0)
		minute = sched[0]
		hour = sched[1]
		day_of_month = sched[2]
		day_of_week = sched[4]
		
		try:
			if int(minute) < 10:
				minute = "0{}".format(minute)
			if int(hour) < 10:
				hour = "0{}".format(hour)
		except:
			pass

		if minute != "*" and hour != "*" and day_of_month != "*":
			sched_desc = "{}:{}H on every {} day of the month.".format(hour, minute, day_of_month)
		elif minute != "*" and hour != "*" and day_of_week != "*":
			sched_desc = "{}:{}H every {}.".format(hour, minute, ", ".join(day_of_week.split(",")))
		elif minute != "*" and hour != "*":
			sched_desc = "{}:{}H every day.".format(hour, minute)

		cron_dict = {"id": job_id, "name": job.comment, "sched_desc": sched_desc, "data_source": parameters[0].strip("\"()' "), "meters": meters, "start_time": ":".join(parameters[2].strip("\"()' ").split(":")[0:2]), "end_time": ":".join(parameters[3].strip("\"()' ").split(":")[0:2]), "enabled": job_enabled}
		cron_list.append(cron_dict)

	return cron_list


def action_cronjobs(action_jobid):
	action = action_jobid.split("_")[0]
	job_id = int(action_jobid.split("_")[1])

	job_cnt = 0
	# Initialise Cron
	root_cron = CronTab(user=retrieve_glob_var()["cron_user"])
	for job in root_cron:
		job_cnt += 1
		if job_cnt == job_id:
			if action == "enable":
				job.enable()
			elif action == "disable":
				job.enable(False)
			elif action == "delete":
				root_cron.remove(job)
			else:
				print("Unable to ascertain Job {} action for Job ID: {}.".format(action, job_id))

	try:
		root_cron.write()
	except Exception as e:
		print("Error Enabling/Disabling Cron job: {}\nJob: {}".format(e, job))
		root_cron.clear()


########## END Data Transfer (Smart Meter): Manage Schedules ##########


########## START App Launch ##########

def list_of_local_apps():
	system_apps = ["pipewire", "enchant-2", "gnome-todo", "im-config", "man", "mousetweaks", "file-roller", "gnome-shell", "gnome-system-monitor", "unattended-upgrades", "m2300w", "totem", "ucf", "debconf", "os-prober", "libreoffice", "info", "update-manager", "orca", "gnome-control-center", "pnm2ppa", "eog", "system-config-printer", "gnome-session", "speech-dispatcher", "rygel", "apturl", "npm", "perl", "brltty", "evince", "file", "systemd", "dconf", "remmina", "rsync", "distro-info", "gcc", "gettext", "locale", "plymouth", "gedit", "gnome-logs", "ibus", "pulseaudio", "nodejs", "tracker3", "lftp", "nano", "groff", "seahorse", "foo2qpdl", "update-notifier", "aspell", "ghostscript", "p11-kit", "dpkg", "python3", "session-migration", "gdb", "foo2zjs", "rhythmbox", "zenity", "nautilus", "yelp"]
	share_path = "/usr/share"
	bin_path = "/usr/bin"
	app_list = []

	for path in os.listdir(share_path):
		if os.path.os.path.isfile(os.path.join(bin_path, path)) and path not in system_apps:
			app_list.append(path)
	return app_list


def retrieve_arkime_views():
	# Call http://<arkime>:8005/api/views to return a dict similar to arkime_views
	arkime_cred = retrieve_arkime_var()
	try:
		request_views = requests.get("http://{}:8005/api/views".format(request.remote_addr),
						auth=HTTPDigestAuth(arkime_cred["arkime_user"], arkime_cred["arkime_password"]))
		if request_views.status_code != 200:
			message = "Unable to authenticate. Are the credentials correct?"
			print(message)
			return 0, message
		views_dict = ast.literal_eval(request_views.text)
	except Exception as e:
		print("Unable to GET /api/views: {}".format(e))
		return 0, str(e)
	return 1, views_dict["data"]


########### END App Launch ###########


########## START Help ##########
# Code Here
########### END Help ###########
