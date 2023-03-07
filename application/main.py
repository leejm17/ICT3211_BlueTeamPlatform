from flask import request
from datetime import datetime, timedelta
from crontab import CronTab
import os
import ftplib, ssl
import magic
import ast
import requests
from requests.auth import HTTPBasicAuth

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


"""Initiate FTP for Smart Meter"""
def windows_ftp_start(ftp_dir):
	print("Initiate FTP for Smart Meter")

	# If SmartMeterData, then ftp_dir has two folders
	if ftp_dir == "SmartMeterData":
		ftp_dir = ["SmartMeterData", "Archive_SmartMeterData"]
	# Else WiresharkData, then ftp_dir has only one folder
	else:
		ftp_dir = [ftp_dir]

	# List to store Dir & corresponding Folder Names
	dir_list = []

	"""Iterate ftp_dir folders"""
	for root_dir in ftp_dir:
		try:
			"""Initialise FTP Connection"""
			global_dict = retrieve_glob_var()
			ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
			ftps.prot_p()				# Set up secure connection
			root = ftps.mlsd(root_dir)	# FTP Root directory
			# Return immediately if WiresharkData is established"""
			if root_dir == "WiresharkData":
				ftps.quit()
				return True, "Wireshark"
		except Exception as e:
			try:
				# Exit connection if any error
				ftps.quit()
			except Exception as econn:
				# If unable to exit connection, then machine is NOT online
				print("Smart Meter Windows machine is NOT online.")
				return False, e
			print("FTP Connection Error: {}".format(e))
			return False, e

		try:
			"""Iterate all files/folders in FTP Root directory"""
			for dir_name in root:
				"""
				dir_name[0] = dir/filename
				dir_name[1] = dir/file's metadata
				##print("Dir: {}".format(dir_list[0]))		# Print Dir
				"""
				# Append foldername if file's metadata reveals a folder, and it is not in dir_list
				if dir_name[1]["type"] == "dir":
					if dir_name[0] not in dir_list:
						dir_list.append(dir_name[0])
			ftps.quit()
		except Exception as e:
			# FTP directory has Permissions Error iterating files
			ftps.quit()
			print("File Permissions Error: {}".format(e))
			print("Dict: {}".format(dir_list))	# Print stored list so far
			return False, e

	return True, dir_list


########## END Data Transfer (Smart Meter): Initiate FTP ##########
########## START Data Transfer (Smart Meter): Transfer Data ##########

"""Data Transfer Process"""
def windows_ftp_process(form):
	print("Smart Meter Data Transfer Process")

	"""
	Initiate FTP for Data Transfer Process
	:return file_dict: Full list of {FTP Directory: Filenames} based on data_source, meters
	"""
	print("\tdata_source: {}".format(form.data_source.data))
	print("\tmeters: {}".format(form.meters.data))
	success, file_dict = windows_ftp_initiate(form.data_source.data, form.meters.data, form.wireshark_source.data)
	if not success:
		return success, file_dict

	"""Filter Files for Data Transfer Process
	:return file_dict: Filtered list of {FTP Directory: Filenames} based on date, start_time, end_time
	"""
	print("\tdate: {}".format(form.date.data))
	print("\tstart_time (utc): {}".format(form.start_time.data))
	print("\tend_time (utc): {}".format(form.end_time.data))
	success, file_dict = windows_ftp_filter_datetime(form.data_source.data, form.date.data, form.start_time.data, form.end_time.data, file_dict)
	if not success:
		return success, file_dict

	"""Download filtered files from file_dict via FTP"""
	success, message = windows_ftp_transfer(form.data_source.data, file_dict)

	return success, message


"""Initiate FTP for Data Transfer Process"""
def windows_ftp_initiate(ftp_dir, meters, wireshark_src):
	print("Initiate FTP for Data Transfer Process")

	# Dict to store Dir & corresponding File Names
	file_dict = {}

	# If SmartMeterData, then ftp_dir has two folders
	if ftp_dir == "SmartMeterData":
		ftp_dir = ["SmartMeterData", "Archive_SmartMeterData"]
	# Else WiresharkData, then ftp_dir has only one folder
	else:
		ftp_dir = [ftp_dir]

	# Calculate Time taken to iterate and store FTP Directories and Files
	import time
	start_dur = time.time()

	"""Initialise FTP Connection"""
	global_dict = retrieve_glob_var()
	ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
	ftps.prot_p()		# Set up secure connection

	"""Iterate ftp_dir folders and store files"""
	for root_dir in ftp_dir:
		try:
			root = ftps.mlsd(root_dir)	# FTP Root directory
			# WiresharkData folder has no sub-directories
			if root_dir == "WiresharkData":
				file_dict[root_dir] = []
		except Exception as e:
			try:
				# Exit connection if any error
				ftps.quit()
			except Exception as econn:
				# If unable to exit connection, then machine is NOT online
				print("Smart Meter Windows machine is NOT online.")
				return False, e
			print("FTP Connection Error: {}".format(e))
			return False, e

		try:
			"""Iterate all files/folders in FTP Root directory"""
			for dir_list in root:
				"""
				dir_list[0] = dir/filename
				dir_list[1] = dir/file's metadata
				##print("Dir: {}".format(dir_list[0]))		# Print Dir
				"""
				# WiresharkData folder contains filenames in a specific format
				if root_dir == "WiresharkData":
					print(dir_list[0])
					if wireshark_src == dir_list[0].split(".")[0].split("_")[-1]:
						file_dict[root_dir] += [dir_list[0]]

				# If filename is a meter name
				elif dir_list[0] in meters:
					# If file's metadata reveals a folder, then it is a meter folder
					if dir_list[1]["type"] == "dir":
						directory = root_dir + "/" + dir_list[0]

						"""Iterate and append all files in meter folder"""
						file_list = ftps.mlsd(directory)
						file_dict[directory] = []
						for data in file_list:
							##print("File: {}".format(data[0]))	# Print Filename
							file_dict[directory] += [data[0]]
		except Exception as e:
			# FTP directory has Permissions Error iterating files
			ftps.quit()
			print("File Permissions Error: {}".format(e))
			##print("Dict: {}".format(file_dict))	# Print stored dictionary so far
			return False, e
	try:
		ftps.quit()
	except Exception as e:
		print("Unable to end FTP connection gracefully: {}".format(e))
		return False, e

	# Print Time taken to iterate and store FTP Directories and Files
	end_dur = time.time()
	print("Storing of FTP Directories and Files in {} seconds.".format(end_dur-start_dur))

	return True, file_dict


"""Filter Files for Data Transfer Process"""
def windows_ftp_filter_datetime(data_source, date, start_time, end_time, file_dict):
	# Dict to store Dir & filtered File Names based on date, start_time, end_time
	filtered_dict = {}

	# Format date and time
	start_datetime = datetime.combine(date, start_time) - timedelta(hours=8)
	start_date = start_datetime.strftime("%Y%m%d")
	start_time = int(start_datetime.strftime("%H%M%S"))
	end_datetime = datetime.combine(date, end_time) - timedelta(hours=8)
	end_date = end_datetime.strftime("%Y%m%d")
	end_time = int(end_datetime.strftime("%H%M%S"))

	# Return user input error
	if end_datetime < start_datetime:
		return False, "Start Datetime cannot be later than End Datetime"

	print("Filter Files for Data Transfer Process")
	print("\tstart_date: {}".format(start_date))
	print("\tstart_time: {} (gmt+8)".format(start_time))
	print("\tend_date: {}".format(end_date))
	print("\tend_time: {} (gmt+8)".format(end_time))

	"""Iterate folders in file_dict"""
	for meter in file_dict:
		filtered_dict[meter] = []
		
		"""Iterate all files in folder"""
		for csv_file in file_dict[meter]:
			filtered_date_file = csv_file.split("_")[0]
			##print(start_date, filtered_date_file)	# Print Filtered Date & Date of selected .csv file

			# WiresharkData filenames are of a specific time format
			if data_source == "WiresharkData":
				filtered_time_file = int("{}00".format(csv_file.split("_")[1].split(".")[0]))
			# SmartMeterData filenames are of a different time format
			else:
				filtered_time_file = int(csv_file.split("_")[1].split(".")[0])

			if start_date == end_date == filtered_date_file:
				"""Append .csv filename if start, end dates and time are same"""
				# Store .csv filename if Start time <= filtered range <= End time
				if (start_time <= filtered_time_file) and (filtered_time_file <= end_time):
					##print("{} <= {} <= {}".format(start_time, filtered_time_file, end_time))	# Print Filtered Start-End times & Time of selected .csv file
					filtered_dict[meter] += [csv_file]

			else:
				"""Compare start & end dates if dates are NOT same"""
				if filtered_date_file == start_date:
					"""Append .csv filename if same as START date & time"""
					# Store .csv filename if Start time <= filtered range <= 235959
					if (start_time <= filtered_time_file) and (filtered_time_file <= 235959):
						##print("{} <= {} <= 235959".format(start_time, filtered_time_file))	# Print Filtered Start-End times & Time of selected .csv file
						filtered_dict[meter] += [csv_file]

				elif filtered_date_file == end_date:
					"""Append .csv filename if same as END date & time"""
					# Store .csv filename if 000000 <= filtered range <= End time
					if (000000 <= filtered_time_file) and (filtered_time_file <= end_time):
						##print("000000 <= {} <= {}".format(filtered_time_file, end_time))	# Print Filtered Start-End times & Time of selected .csv file
						filtered_dict[meter] += [csv_file]

	return True, filtered_dict


"""Download filtered files from file_dict via FTP"""
def windows_ftp_transfer(data_source, file_dict, job_name=None):
	#download_dir = ""
	download_cnt = 0	# Count number of files downloaded
	directory_cnt = 0	# Count number of directories downloaded into
	print("Download filtered files from file_dict via FTP")
	##print("file_dict: {}".format(file_dict))

	try:
		"""Initialise FTP Connection"""
		global_dict = retrieve_glob_var()
		ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
		ftps.prot_p()		# Set up secure connection
		current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		# Calculate Time taken to iterate and download all files
		import time
		start_all = time.time()

		"""Iterate folders in filtered file_dict"""
		from __main__ import app
		for directory in file_dict:
			# If folder contains no file, skip to next folder
			if len(file_dict[directory]) == 0:
				continue

			"""Set up Download Directory"""
			ftps.cwd("/"+directory)		# Change FTP directory
			if job_name is not None:
				# :param job_name: Only exists for Job Schedule
				download_dir = "{}/FTP_Downloads/Smart_Meter/{}/{}/{}/{}".format("/".join(app.config["APP_DIR"].split("/")[:-2]), data_source, job_name, current_datetime, directory.split("/")[1])
			else:
				download_dir = "{}/FTP_Downloads/Smart_Meter/{}/{}/{}".format("/".join(app.config["APP_DIR"].split("/")[:-2]), data_source, current_datetime, directory.split("/")[1])

			# Mkdir if Download directory does NOT exist
			if not os.path.isdir(download_dir):
				os.makedirs(download_dir)

			# Store and change Download directory
			current_dir = os.getcwd()
			os.chdir(download_dir)

			# Calculate Time taken to iterate and download files from this directory
			print("\tDownloading files for {}:".format(directory))
			start_dur = time.time()

			"""Download filtered files from this folder (FTP directory)"""
			for csv_file in file_dict[directory]:
				try:
					with open(csv_file, "wb") as f:
						# Command for Downloading the file "RETR csv_file"
						ftps.retrbinary(f"RETR {csv_file}", f.write)
						download_cnt += 1
				except Exception as e:
					continue

			# Print Time taken to iterate and download files from this directory
			end_dur = time.time()
			print("\t\tDownloaded {} files so far in {} seconds.".format(download_cnt, end_dur-start_dur))
			directory_cnt += 1

			# Revert to CWD
			os.chdir(current_dir)

	except Exception as e:
		print("Error Downloading File: {}".format(e))
		# Print Time taken to iterate and download all files
		end_all = time.time()
		print("\tDownloaded {} files out of {} in {} seconds.".format(download_cnt, len(file_dict), end_all-start_all))
		return False, e

	ftps.quit()

	# Print Time taken to iterate and download all files
	end_all = time.time()
	print("{} files in {} seconds.\n".format(download_cnt, end_all-start_all))

	# Return message containing files downloaded & download directory
	download_path = "/".join(download_dir.split("/")[:-1])
	message = [download_cnt, download_path]

	return True, message


########## END Data Transfer (Smart Meter): Transfer Data ##########
########## START Data Transfer (Smart Meter): Schedule Transfer ##########

"""Initialise the Scheduling of Data Transfer Process"""
def windows_ftp_automate(form):
	print("Initialise the Scheduling of Data Transfer Process")
	print("\tdata_source: {}".format(form.data_source.data))
	print("\tmeters: {}".format(form.meters.data))
	print("\tstart_time: {}".format(form.start_time.data))
	print("\ttransfer_dur: +{} minutes".format(form.transfer_dur.data))	# end_time = start_time + transfer_dur
	end_time = (datetime.combine(form.date.data, form.start_time.data) + timedelta(minutes=int(form.transfer_dur.data))).strftime("%H:%M:%S")
	print("\tend_time: {}".format(end_time))
	print("\tjob_name: {}".format(form.job_name.data))
	print("\ttransfer_freq: {}".format(form.transfer_freq.data))	# For Cron

	"""
	Cron Params: schedule, command, comment
	1. schedule: freq, week/month, scheduled_time
	2. command: data_source, meters, start_time, end_time
	3. comment: job_name
	"""

	if form.transfer_freq.data == "Daily":
		"""
		:param week_month: None
		:param sched_time: time
		"""
		print("\ttransfer_freq_time: {}\n".format(form.transfer_freq_time.data))
		success, cron, job = cronjob_format(
			"daily", None, form.transfer_freq_time.data, form.job_name.data,
			form.data_source.data, form.meters.data, form.start_time.data, end_time)

	elif form.transfer_freq.data == "Weekly":
		"""
		:param week_month: week
		:param sched_time: week_time
		"""
		print("\ttransfer_freq_week: {}".format(form.transfer_freq_week.data))
		print("\ttransfer_freq_week_time: {}\n".format(form.transfer_freq_week_time.data))
		if not form.transfer_freq_week.data:
			return False, "Unspecified Parameters", "Please ensure your parameters are selected."
		success, cron, job = cronjob_format(
			"weekly", form.transfer_freq_week.data, form.transfer_freq_week_time.data, form.job_name.data,
			form.data_source.data, form.meters.data, form.start_time.data, end_time)

	elif form.transfer_freq.data == "Monthly":
		"""
		:param week_month: month
		:param sched_time: month_time
		"""
		print("\ttransfer_freq_month: {}".format(form.transfer_freq_month.data))
		print("\ttransfer_freq_month_time: {}\n".format(form.transfer_freq_month_time.data))
		success, cron, job = cronjob_format(
			"monthly", form.transfer_freq_month.data, form.transfer_freq_month_time.data, form.job_name.data,
			form.data_source.data, form.meters.data, form.start_time.data, end_time)

	else:
		"""Frequency is NOT recognised"""
		return False, "Unspecified Parameters", "Please ensure your parameters are selected."

	return success, cron, "{}-Duration of Data To Collect: {} minutes".format(job, form.transfer_dur.data)


""" References:
https://pypi.org/project/python-crontab/
https://crontab.guru/
sudo cat /var/spool/cron/crontabs/user
date
crontab -l"""
"""Schedule Job (Data Transfer Process)"""
def cronjob_format(freq, week_month, sched_time, job_name, data_source, meters, start_time, end_time):
	# Every job requires: frequency, week/month, scheduled_time, job_name, data_source, meters, start_time, end_time
	sched_time = str(sched_time)

	"""Initialise Cron"""
	root_cron = CronTab(user=retrieve_glob_var()["cron_user"])

	"""Create New Job"""
	from __main__ import app
	job = root_cron.new(command="cd {} && /usr/bin/python3 -c 'from main import cronjob_process; cronjob_process(\"{}\", \"{}\", \"{}\", \"{}\")' >> {}/jobs_completed.txt".format(app.config["APP_DIR"], data_source, meters, start_time, end_time, app.config["APP_DIR"]), comment=job_name)

	"""Craft Display Message"""
	if data_source == "SmartMeterData":
		job_message = "Job Name: {}-Data Source: {}-Meters: {}-Data Start Time: {}-Data End Time: {}".format(job_name, data_source, meters, start_time, end_time)
	else:
		job_message = "Job Name: {}-Data Source: {}-Data Start Time: {}-Data End Time: {}".format(job_name, data_source, start_time, end_time)

	# Format Time
	hour = sched_time.split(":")[0]
	minute = sched_time.split(":")[1]

	"""Setting Job Restrictions (Schedule) based on Form Data (Frequency)"""
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

	try:
		# Execute Job Creation
		root_cron.write()
	except Exception as e:
		# Job Creation cannot be executed
		print("Error writing Cron job: {}\nJob: {}".format(e, job))
		job.clear()
		return False, e, job_message

	return True, cron_message, job_message


"""Method to call for scheduled jobs (Data Transfer process)"""
def cronjob_process(data_source, meters, start_time, end_time):
	# Data1: 'WiresharkData', [], '07:00:00', '12:00:00'	>> 2 files downloaded
	# cd /home/user/Desktop/BlueTeam/venv_2/ICT3211_BlueTeamPlatform/application && python3 -c "from main import cronjob_process; cronjob_process('WiresharkData', [], '07:00:00', '12:00:00')"

	# Data2: 'SmartMeterData', ['Meter1', 'Meter2'], '07:00:00', '12:00:00'	>> 4 files downloaded
	# cd /home/user/Desktop/BlueTeam/venv_2/ICT3211_BlueTeamPlatform/application && python3 -c "from main import cronjob_process; cronjob_process('SmartMeterData', ['Meter1', 'Meter2'], '07:00:00', '12:00:00')"

	# Today's date (i.e. Current date of Job)
	from datetime import date
	##date = datetime.strptime("2023-02-01", "%Y-%m-%d")	# For demo purpose only
	date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")

	# Format Time
	start_time = datetime.strptime(start_time, "%H:%M:%S").time()
	end_time = datetime.strptime(end_time, "%H:%M:%S").time()

	"""Initiate FTP for Data Transfer Process"""
	success, file_dict = windows_ftp_initiate(data_source, meters)
	if not success:
		print("Cron unable to initiate FTP: {}".format(file_dict))

	"""Filter Files for Data Transfer Process"""
	success, file_dict = windows_ftp_filter_datetime(date, start_time, end_time, file_dict)
	if not success:
		print("Cron unable to download files: {}".format(file_dict))

	"""Download filtered files from file_dict via FTP"""
	success, message = windows_ftp_transfer(data_source, file_dict)
	print("Cron Job Success: {}".format(message))


########## END Data Transfer (Smart Meter): Schedule Transfer ##########
########## START Data Transfer (Smart Meter): Manage Schedules ##########

"""Retrieve Scheduled Jobs (Data Transfers)"""
def retrieve_cronjobs():
	# [{"id": "1", "name": "Job One", "data_source": "SmartMeterData", "meters": "['meter1', 'meter2']", "start_time": "12:00", "end_time": "12:30"}]

	cron_list = []
	job_id = 0

	"""Initialise Cron"""
	try:
		root_cron = CronTab(user=retrieve_glob_var()["cron_user"])
	except Exception as e:
		print("Cron User Error: {}".format(e))
		return "Cron User Error"

	"""Iterate every Cron Job and format jobs for display"""
	for job in root_cron:
		job_id += 1
		try:
			parameters = job.command.split(">>")[0].split("cronjob_process")[2].split("\", \"")
		except Exception as e:
			print("Cron Split Error (Job ID: {}): {}".format(job_id, e))
			continue
		job_enabled = str(job)[0]

		# Format Meters
		meters = parameters[1].strip("\"()' ")
		if meters == "[]":
			meters = "-"
		meter_list = ast.literal_eval(meters)
		meters = ", ".join(meter_list)

		# Retrieve Schedule
		sched = str(job).split(" cd ")[0].split(" ")
		if job_enabled == "#":
			sched.pop(0)
		minute = sched[0]
		hour = sched[1]
		day_of_month = sched[2]
		day_of_week = sched[4]

		# Format Time
		try:
			if int(minute) < 10:
				minute = "0{}".format(minute)
			if int(hour) < 10:
				hour = "0{}".format(hour)
		except:
			pass

		# Format Schedule
		if minute != "*" and hour != "*" and day_of_month != "*":
			sched_desc = "{}:{}H on every {} day of the month.".format(hour, minute, day_of_month)
		elif minute != "*" and hour != "*" and day_of_week != "*":
			sched_desc = "{}:{}H every {}.".format(hour, minute, ", ".join(day_of_week.split(",")))
		elif minute != "*" and hour != "*":
			sched_desc = "{}:{}H every day.".format(hour, minute)

		# Putting Schedule, Meters, Time, etc together
		cron_dict = {"id": job_id, "name": job.comment, "sched_desc": sched_desc, "data_source": parameters[0].strip("\"()' "), "meters": meters, "start_time": ":".join(parameters[2].strip("\"()' ").split(":")[0:2]), "end_time": ":".join(parameters[3].strip("\"()' ").split(":")[0:2]), "enabled": job_enabled}
		cron_list.append(cron_dict)

	return cron_list


"""Action to take on scheduled jobs: Enable, Disable, Delete"""
def action_cronjobs(action_jobid):
	action = action_jobid.split("_")[0]
	job_id = int(action_jobid.split("_")[1])
	job_cnt = 0

	"""Initialise Cron"""
	root_cron = CronTab(user=retrieve_glob_var()["cron_user"])

	"""Iterate every Cron Job and perform Action"""
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
		# Execute Action on the identified Cron Job
		root_cron.write()
	except Exception as e:
		# Action cannot be executed on the identified Cron Job
		print("Error Enabling/Disabling Cron job: {}\nJob: {}".format(e, job))
		root_cron.clear()


########## END Data Transfer (Smart Meter): Manage Schedules ##########
########## START App Launch ##########

"""Retrieve Local Applications"""
def list_of_local_apps():
	"""Blacklist system-installed local apps"""
	system_apps = ["pipewire", "enchant-2", "gnome-todo", "im-config", "man", "mousetweaks", "file-roller", "gnome-shell", "gnome-system-monitor", "unattended-upgrades", "m2300w", "totem", "ucf", "debconf", "os-prober", "libreoffice", "info", "update-manager", "orca", "gnome-control-center", "pnm2ppa", "eog", "system-config-printer", "gnome-session", "speech-dispatcher", "rygel", "apturl", "npm", "perl", "brltty", "evince", "file", "systemd", "dconf", "remmina", "rsync", "distro-info", "gcc", "gettext", "locale", "plymouth", "gedit", "gnome-logs", "ibus", "pulseaudio", "nodejs", "tracker3", "lftp", "nano", "groff", "seahorse", "foo2qpdl", "update-notifier", "aspell", "ghostscript", "p11-kit", "dpkg", "python3", "session-migration", "gdb", "foo2zjs", "rhythmbox", "zenity", "nautilus", "yelp"]

	"""Local apps are found in these two paths"""
	share_path = "/usr/share"
	bin_path = "/usr/bin"

	app_list = []
	# Return apps that are NOT found in both paths & NOT blacklisted local apps
	for path in os.listdir(share_path):
		if os.path.os.path.isfile(os.path.join(bin_path, path)) and path not in system_apps:
			app_list.append(path)

	return app_list


"""Retrieve Arkime Views' ID from /api/views"""
def retrieve_arkime_views():
	arkime_cred = retrieve_arkime_var()
	try:
		# Call https://<arkime>/api/views to return a dict similar to arkime_views
		from requests.auth import HTTPDigestAuth
		request_views = requests.get("http://{}:8005/api/views".format(request.remote_addr),
						auth=HTTPDigestAuth(arkime_cred["arkime_user"], arkime_cred["arkime_password"]),
						verify=False)
		"""request_views = requests.get("https://{}/api/views".format(request.remote_addr),
						auth=HTTPBasicAuth(arkime_cred["arkime_user"], arkime_cred["arkime_password"]),
						verify=False)"""

		# If Arkime is online but unable to fetch data, might be due to authentication issue
		if request_views.status_code != 200:
			message = "Unable to authenticate. Are the credentials correct?"
			print(message)
			return 0, message
		views_dict = ast.literal_eval(request_views.text)

	except Exception as e:
		# Arkime is not accessible/online
		print("Unable to GET /api/views: {}".format(e))
		return 0, str(e)

	return 1, views_dict["data"]


########## END App Launch ##########
########## START Spider ##########

# Code Here


########## END Spider ##########
########## START Help ##########
# Code Here
########## END Help ##########
