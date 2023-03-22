from flask import request, flash
from datetime import datetime, timedelta
from crontab import CronTab
import time, os, ast
import requests
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor

# Import Local Files
from admin import retrieve_glob_var, retrieve_arkime_var
from config import init_ftps_conn, download_file, thread_datatransfer, start_db_conn, end_db_conn

# Import Library for commmunication with scapyd scraper
from scrapyd_api import ScrapydAPI
PROJECT_NAME =  "yara_scrapy"

########## START Data Transfer (Smart Meter): Initiate FTPS ##########

"""Initiate FTPS for Smart Meter"""
def windows_ftp_start(ftp_dir):
	print("Initiate FTPS for Smart Meter")

	# If SmartMeterData, then ftp_dir has two folders
	if ftp_dir == "SmartMeterData":
		ftp_dir = ["SmartMeterData", "Archive_SmartMeterData"]
	# Else WiresharkData / KEPServerEXData / WindowsEventData, then ftp_dir has only one root folder
	else:
		ftp_dir = [ftp_dir]

	# List to store Dir & corresponding Folder Names
	dir_list = []

	# Calculate Time taken to initialise 1st FTPS Connection
	start_dur = time.time()

	"""Iterate ftp_dir folders"""
	for root_dir in ftp_dir:
		try:
			"""Initialise FTPS Connection"""
			ftps = init_ftps_conn()
			root = ftps.mlsd(root_dir)	# FTPS Root directory

			# Return immediately if WiresharkData / KEPServerEXData / WindowsEventData is established
			if root_dir == "WiresharkData" or root_dir == "KEPServerEXData" or root_dir == "WindowsEventData":
				ftps.quit()
				return True, root_dir.split("Data")[0]
		except Exception as e:
			try:
				# Exit connection if any error
				ftps.close()
			except Exception as econn:
				# If unable to exit connection, then machine is NOT online
				print("Smart Meter Windows machine is NOT online.")
				return False, e
			print("FTPS Connection Error: {}".format(e))
			return False, e

		try:
			"""Iterate all files/folders in FTPS Root directory"""
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
			ftps.close()
		except Exception as e:
			# FTPS directory has Permissions Error iterating files
			ftps.close()
			print("File Permissions Error: {}".format(e))
			print("Dict: {}".format(dir_list))	# Print stored list so far
			return False, e

	end_dur = time.time()
	print("\tInitiated FTPS in {} seconds".format(end_dur-start_dur))

	return True, dir_list


########## END Data Transfer (Smart Meter): Initiate FTPS ##########
########## START Data Transfer (Smart Meter): Transfer Data ##########

"""Data Transfer Process"""
def windows_ftp_process(form):
	print("Smart Meter Data Transfer Process")

	"""
	Initiate FTPS for Data Transfer Process
	:return file_dict: Full list of {FTPS Directory: Filenames} based on data_source, meters
	"""
	print("\tdata_source: {}".format(form.data_source.data))
	print("\tmeters: {}".format(form.meters.data))
	success, file_dict = windows_ftp_initiate(form.data_source.data, form.meters.data, form.wireshark_source.data, form.windowsevent_source.data)
	if not success:
		return success, file_dict

	"""Filter Files for Data Transfer Process
	:return file_dict: Filtered list of {FTPS Directory: Filenames} based on date, start_time, end_time
	"""
	print("\tdate: {}".format(form.date.data))	
	timezone = int("{}{}".format(form.timezone_prefix.data, form.timezone_value.data))
	print("\ttimezone: GMT {}".format(timezone))
	print("\tstart_time: {} (gmt+8)".format(form.start_time.data))
	print("\tend_time: {} (gmt+8)".format(form.end_time.data))
	success, filtered_dict = windows_ftp_filter_datetime(form.data_source.data, form.date.data, timezone, form.start_time.data, form.end_time.data, file_dict)
	if not success:
		return success, filtered_dict

	"""Download filtered files from file_dict via FTP"""
	success, message = windows_ftp_transfer(form.data_source.data, filtered_dict)

	return success, message


"""Initiate FTPS for Data Transfer Process"""
def windows_ftp_initiate(ftp_dir, meters, wireshark_src="All", windowsevent_src="All"):
	print("Initiate FTPS for Data Transfer Process")

	# Dict to store Dir & corresponding File Names
	file_dict = {}

	# If SmartMeterData, then ftp_dir has two folders
	if ftp_dir == "SmartMeterData":
		ftp_dir = ["SmartMeterData", "Archive_SmartMeterData"]
	# Else WiresharkData / KEPServerEXData / WindowsEventData, then ftp_dir has only one folder
	else:
		ftp_dir = [ftp_dir]

	# Calculate Time taken to iterate and store FTPS Directories and Files
	start_dur = time.time()

	try:
		"""Initialise FTPS Connection"""
		ftps = init_ftps_conn()
	except Exception as e:
		try:
			# Exit connection if any error
			ftps.close()
		except Exception as econn:
			# If unable to exit connection, then machine is NOT online
			print("Smart Meter Windows machine is NOT online.")
			return False, e
		print("FTPS Connection Error: {}".format(e))
		return False, e

	"""Iterate ftp_dir folders and store files"""
	for root_dir in ftp_dir:
		try:
			root = ftps.mlsd(root_dir)	# FTPS Root directory
			# KEPServerEXData folder has no sub-directories
			if root_dir == "KEPServerEXData":
				file_dict[root_dir] = []
		except Exception as e:
			try:
				# Exit connection if any error
				ftps.close()
			except Exception as econn:
				# If unable to exit connection, then machine is NOT online
				print("Smart Meter Windows machine is NOT online.")
				return False, e
			print("FTPS Connection Error: {}".format(e))
			return False, e

		try:
			"""Iterate all files/folders in FTPS Root directory"""
			for dir_list in root:
				"""
				dir_list[0] = dir/filename
				dir_list[1] = dir/file's metadata
				##print("Dir: {}".format(dir_list[0]))		# Print Dir
				"""
				# WiresharkData folder contains filenames in a specific format
				if root_dir == "WiresharkData":
					if wireshark_src != "All":
						if wireshark_src == dir_list[0].split(".")[0].split("_")[-1]:
							print("\tWireshark File: {}".format(dir_list[0]))
							directory = "{}/{}".format(root_dir, wireshark_src)
							file_dict[directory] = []
							file_dict[directory] += [dir_list[0]]
					else:
						print("\tWireshark File: {}".format(dir_list[0]))
						directory = "{}/{}".format(root_dir, dir_list[0].split(".")[0].split("_")[-1])
						file_dict[directory] = []
						file_dict[directory] += [dir_list[0]]

				# KEPServerEXData folder
				elif root_dir == "KEPServerEXData":
					print("\tKEPServerEX File: {}".format(dir_list[0]))
					file_dict[root_dir] += [dir_list[0]]

				# WindowsEventData folder contains 2 sub-folders (Security / System)
				elif root_dir == "WindowsEventData":
					if dir_list[1]["type"] == "dir":
						if windowsevent_src != "All":
							directory = "{}/{}".format(root_dir, windowsevent_src)
						else:
							directory = "{}/{}".format(root_dir, dir_list[0])
					file_dict[directory] = windows_append_ftp_files(ftps, file_dict, directory)

				# If filename is a meter name folder
				elif dir_list[0] in meters:
					# If file's metadata reveals a folder, then it is a meter folder
					if dir_list[1]["type"] == "dir":
						directory = "{}/{}".format(root_dir, dir_list[0])
						file_dict[directory] = windows_append_ftp_files(ftps, file_dict, directory)

		except Exception as e:
			# FTPS directory has Permissions Error iterating files
			ftps.close()
			print("File Permissions Error: {}".format(e))
			##print("Dict: {}".format(file_dict))	# Print stored dictionary so far
			return False, e
	try:
		ftps.close()
	except Exception as e:
		print("Unable to end FTPS connection gracefully: {}".format(e))
		return False, e

	# Print Time taken to iterate and store FTPS Directories and Files
	end_dur = time.time()
	print("Storing of FTPS Directories and Files in {} seconds.".format(end_dur-start_dur))

	return True, file_dict


"""Iterate and append all files in meter / windows event folder"""
def windows_append_ftp_files(ftps, file_dict, directory):
	print("\tCurrently appending {}: {}".format(directory.split("/")[0], directory.split("/")[1]))
	file_list = ftps.mlsd(directory)
	file_dict[directory] = []
	for data in file_list:
		##print("File: {}".format(data[0]))	# Print Filename
		file_dict[directory] += [data[0]]

	return file_dict[directory]


"""Filter Files for Data Transfer Process"""
def windows_ftp_filter_datetime(data_source, date, timezone, start_time, end_time, file_dict):
	# Dict to store Dir & filtered File Names based on date, start_time, end_time
	filtered_dict = {}
	data_source_list = ["WiresharkData", "KEPServerEXData", "WindowsEventData"]

	# Format date and time
	start_datetime = datetime.combine(date, start_time) - timedelta(hours=timezone)
	start_date = start_datetime.strftime("%Y%m%d")
	start_time = int(start_datetime.strftime("%H%M%S"))
	end_datetime = datetime.combine(date, end_time) - timedelta(hours=timezone)
	end_date = end_datetime.strftime("%Y%m%d")
	end_time = int(end_datetime.strftime("%H%M%S"))

	# Return user input error
	if end_datetime < start_datetime:
		return False, "Start Datetime cannot be later than End Datetime"

	print("Filtering Files for Data Transfer Process")
	print("\ttimezone: GMT {}".format(timezone))
	print("\tstart_date: {}".format(start_date))
	print("\tstart_time (utc): {}".format(start_time))
	print("\tend_date: {}".format(end_date))
	print("\tend_time (utc): {}".format(end_time))

	"""Iterate folders in file_dict"""
	for meter in file_dict:
		filtered_dict[meter] = []
		
		"""Iterate all files in folder"""
		for csv_file in file_dict[meter]:
			filtered_date_file = csv_file.split("_")[0]
			##print(start_date, filtered_date_file)	# Print Filtered Date & Date of selected .csv file

			# WiresharkData / KEPServerEXData / WindowsEventData filenames are of a specific time format
			if data_source in data_source_list:
				filtered_time_file = int("{}00".format(csv_file.split("_")[1].split(".")[0]))
			# SmartMeterData filenames are of a different time format
			else:
				filtered_time_file = int(csv_file.split("_")[1].split(".")[0])

			"""Filter filenames based on user-specified date/time"""
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

	# Return filtered_dict, but remove empty keys
	filtered_dict = {meter: files for meter, files in filtered_dict.items() if files}
	
	# Print Filtered Meters
	if data_source == "SmartMeterData":
		meter_dict = {}
		for folder_path in filtered_dict:
			folder_path = folder_path.split("/")
			if folder_path[0] not in meter_dict:
				meter_dict[folder_path[0]] = []
			meter_dict[folder_path[0]] += [folder_path[1]]
		for meter in meter_dict:
			print("\t{}: {}".format(meter, meter_dict[meter]))

	return True, filtered_dict


"""Download filtered files from filtered_dict via FTP"""
def windows_ftp_transfer(data_source, filtered_dict, job_name="default"):
	data_source_list = ["SmartMeterData", "WiresharkData", "WindowsEventData"]
	download_dir = ""
	download_cnt = 0	# Count number of files downloaded
	files_cnt = 0		# Count number of files in total
	print("Downloading files from filtered_dict via FTPS (MAX Supported Workers: {})".format(retrieve_glob_var()["workers"]))
	##print("filtered_dict: {}".format(filtered_dict))

	# Store and change Download directory
	current_dir = os.getcwd()

	current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	# Calculate Time taken to iterate and download all files
	start_all = time.time()

	"""Initialise FTPS Connection (Ignore; handled by Multi-thread)"""
	#ftps = init_ftps_conn()

	"""Iterate folders in filtered_dict"""
	from __main__ import app
	for directory in filtered_dict:
		dir_cnt = len(filtered_dict[directory])
		files_cnt += dir_cnt
		print("\tNo. of Files in {}: {}".format(directory, dir_cnt))

		"""Set up Download Directory"""
		if data_source in data_source_list:	# SmartMeterData / WiresharkData / WindowsEventData root folder
			download_dir = "{}/FTP_Downloads/Smart_Meter/{}/{}/{}/{}".format(
							"/".join(app.config["APP_DIR"].split("/")[:-2]),
							data_source,
							job_name,
							current_datetime,
							directory.split("/")[1])
		else:								# KEPServerEXData root folder
			download_dir = "{}/FTP_Downloads/Smart_Meter/{}/{}/{}".format(
							"/".join(app.config["APP_DIR"].split("/")[:-2]),
							data_source,
							job_name,
							current_datetime)

		# Mkdir if Download directory does NOT exist
		if not os.path.isdir(download_dir):
			os.makedirs(download_dir)
		os.chdir(download_dir)

		# Calculate Time taken to iterate and download files from this directory
		start_dur = time.time()

		"""Download 120 files at a time with multi-threaded workers"""
		directory_list = [filtered_dict[directory][i * 120:(i + 1) * 120] for i in range((len(filtered_dict[directory]) + 120 - 1) // 120 )]
		print("\t\tWorkers required: {}".format(len(directory_list)))

		# String formatting for WiresharkData folder
		if "WiresharkData" in directory:
			directory = directory.split("/")[0]

		with ThreadPoolExecutor(max_workers=int(retrieve_glob_var()["workers"])) as executor:
			for mini_list in directory_list:
				future = executor.submit(thread_datatransfer, directory, mini_list, directory_list.index(mini_list))

		# Print Time taken to iterate and download files from this directory
		end_dur = time.time()
		print("\t\t... in {} seconds.".format(end_dur-start_dur))


	# Print Time taken to iterate and download all files
	end_all = time.time()
	print("{} files in {} seconds.\n".format(files_cnt, end_all-start_all))

	# Revert to CWD
	os.chdir(current_dir)

	# Return message containing files downloaded & download directory
	if data_source in data_source_list:
		message = [files_cnt, "/".join(download_dir.split("/")[:-1])]
	else:
		message = [files_cnt, download_dir]

	return True, message


########## END Data Transfer (Smart Meter): Transfer Data ##########
########## START Data Transfer (Smart Meter): Schedule Transfer ##########

"""Initialise the Scheduling of Data Transfer Process"""
def windows_ftp_automate(form):
	timezone = int("{}{}".format(form.timezone_prefix.data, form.timezone_value.data))
	print("Initialise the Scheduling of Data Transfer Process")
	print("\tdata_source: {}".format(form.data_source.data))
	print("\tmeters: {}".format(form.meters.data))
	print("\ttimezone: GMT {}".format(timezone))
	print("\tstart_time: {}".format(form.start_time.data))
	print("\ttransfer_dur: +{} minutes".format(form.transfer_dur.data))	# end_time = start_time + transfer_dur
	end_time = (datetime.combine(form.date.data, form.start_time.data) + timedelta(minutes=int(form.transfer_dur.data))).strftime("%H:%M:%S")
	print("\tend_time: {}".format(end_time))
	print("\tjob_name: {}".format(form.job_name.data))
	print("\ttransfer_freq: {}".format(form.transfer_freq.data))	# For Cron

	if form.data_source.data == "SmartMeterData":
		sub_folders = form.meters.data
	elif form.data_source.data == "WiresharkData":
		sub_folders = form.wireshark_source.data
	elif form.data_source.data == "KEPServerEXData":
		sub_folders = []
	elif form.data_source.data == "WindowsEventData":
		sub_folders = form.windowsevent_source.data

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
			form.data_source.data, sub_folders, timezone, form.start_time.data, end_time)

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
			form.data_source.data, sub_folders, timezone, form.start_time.data, end_time)

	elif form.transfer_freq.data == "Monthly":
		"""
		:param week_month: month
		:param sched_time: month_time
		"""
		print("\ttransfer_freq_month: {}".format(form.transfer_freq_month.data))
		print("\ttransfer_freq_month_time: {}\n".format(form.transfer_freq_month_time.data))
		success, cron, job = cronjob_format(
			"monthly", form.transfer_freq_month.data, form.transfer_freq_month_time.data, form.job_name.data,
			form.data_source.data, sub_folders, timezone, form.start_time.data, end_time)

	else:
		"""Frequency is NOT recognised"""
		return False, "Unspecified Parameters", "Please ensure your parameters are selected."

	return success, cron, "{}^Duration of Data To Collect: {} minutes".format(job, form.transfer_dur.data)


""" References:
https://pypi.org/project/python-crontab/
https://crontab.guru/
sudo cat /var/spool/cron/crontabs/user
date
crontab -l"""
"""Schedule Job (Data Transfer Process)"""
def cronjob_format(freq, week_month, sched_time, job_name, data_source, sub_folders, timezone, start_time, end_time):
	# Every job requires: frequency, week/month, scheduled_time, job_name, data_source, sub_folders, timezone, start_time, end_time
	sched_time = str(sched_time)

	"""Initialise Cron"""
	root_cron = CronTab(user=retrieve_glob_var()["cron_user"])

	"""Create New Job"""
	from __main__ import app
	job = root_cron.new(command="cd {} && /usr/bin/python3 -c 'from app import app; from main import cronjob_process; cronjob_process(\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\")' >> {}/jobs_log.txt".format(app.config["APP_DIR"], data_source, sub_folders, timezone, start_time, end_time, job_name, app.config["APP_DIR"]), comment=job_name)

	"""Craft Display Message"""
	if timezone >= 0:
		timezone = "+{}".format(timezone)
	if data_source == "SmartMeterData":
		job_message = "Job Name: {}^Data Source: {}^Meters: {}^Data Start Time: {}^Data End Time: {}^Timezone (GMT): {}".format(job_name, data_source, sub_folders, start_time, end_time, timezone)
	elif data_source == "WiresharkData" or data_source == "WindowsEventData":
		job_message = "Job Name: {}^Data Source: {}^Sub-folders: {}^Data Start Time: {}^Data End Time: {}^Timezone (GMT): {}".format(job_name, data_source, sub_folders, start_time, end_time, timezone)
	else:
		job_message = "Job Name: {}^Data Source: {}^Data Start Time: {}^Data End Time: {}^Timezone (GMT): {}".format(job_name, data_source, start_time, end_time, timezone)

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


"""Method to call for scheduled jobs (Data Transfer process)
	To view jobs: sudo cat /var/spool/cron/crontabs/$(whoami)"""
def cronjob_process(data_source, sub_folders, timezone, start_time, end_time, job_name):	
	print("\nInitiating Scheduled Job for \"{}\"".format(job_name))
	print("Job Start Time: {} (Local Timezone)\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

	# Today's date (i.e. Current date of Job)
	from datetime import date
	##date = datetime.strptime("2023-02-01", "%Y-%m-%d")	# For demo purpose only
	date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")

	# Format Time
	start_time = datetime.strptime(start_time, "%H:%M:%S").time()
	end_time = datetime.strptime(end_time, "%H:%M:%S").time()

	"""Initiate FTPS for Data Transfer Process"""
	success, file_dict = windows_ftp_initiate(data_source, sub_folders, sub_folders, sub_folders)
	if not success:
		print("Cron unable to initiate FTP: {}\n".format(file_dict))
		print("########## ########## ########## ##########")
		return 1

	"""Filter Files for Data Transfer Process"""
	success, filtered_dict = windows_ftp_filter_datetime(data_source, date, int(timezone), start_time, end_time, file_dict)
	if not success:
		print("Cron unable to download files: {}\n".format(filtered_dict))
		print("########## ########## ########## ##########")
		return 1

	"""Download filtered files from filtered_dict via FTP"""
	success, message = windows_ftp_transfer(data_source, filtered_dict, job_name)
	print("Job End Time: {} (Local Timezone)".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
	print("Cron Job Success: {} files downloaded".format(message[0]))
	print("Download Path: \"{}\"\n".format(message[1]))
	print("########## ########## ########## ##########")
	return 0


########## END Data Transfer (Smart Meter): Schedule Transfer ##########
########## START Data Transfer (Smart Meter): Manage Schedules ##########

"""Retrieve Scheduled Jobs (Data Transfers)"""
def retrieve_cronjobs():
	# [{"id": "1", "name": "Job One", "data_source": "SmartMeterData", "sub_folders": "['meter1', 'meter2']", "timezone": "8", "start_time": "12:00", "end_time": "12:30"}]
	# [{"id": "2", "name": "Job Two", "data_source": "WiresharkData", "sub_folders": "All", "timezone": "8", "start_time": "12:00", "end_time": "12:30"}]
	# [{"id": "3", "name": "Job Two", "data_source": "KEPServerEXData", "sub_folders": "[]", "timezone": "8", "start_time": "12:00", "end_time": "12:30"}]
	# [{"id": "4", "name": "Job Four", "data_source": "WindowsEventData", "sub_folders": "All", "timezone": "8", "start_time": "12:00", "end_time": "12:30"}]

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

		# Format Sub-folders
		sub_folders = parameters[1].strip("\"()' ")
		if sub_folders == "[]":
			sub_folders = "-"
		else:
			try:
				sub_folder_list = ast.literal_eval(sub_folders)
				sub_folders = ", ".join(sub_folder_list)
			except:
				pass

		# Format Timezone
		timezone = int(parameters[2].strip("\"()' "))
		if timezone >= 0:
			timezone = "+{}".format(timezone)

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

		# Putting Schedule, Sub-folders, Time, etc together
		cron_dict = {
			"id": job_id,
			"name": job.comment,
			"sched_desc": sched_desc,
			"data_source": parameters[0].strip("\"()' "),
			"sub_folders": sub_folders,
			"timezone": timezone,
			"start_time": ":".join(parameters[3].strip("\"()' ").split(":")[0:2]),
			"end_time": ":".join(parameters[4].strip("\"()' ").split(":")[0:2]),
			"enabled": job_enabled}
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
	"""Whitelist relevant local apps"""
	app_list = ["filezilla", "wireshark", "zui", "dbeaver", "remmina"]

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

"""Initialise ScrapydAPI per-use"""
def init_scrapyd():
	from __main__ import app
	return ScrapydAPI("http://{}:6800".format(app.config["APP_IP"]))


"""Update DB based on Spider's Job statuses"""
def update_spider_db(mysql):
	scrapyd = init_scrapyd()

	# Query for jobs that are "pending" or "running"
	query = "SELECT jobid from spiderjobs WHERE status='pending' OR status='running';"
	conn, cursor = start_db_conn(mysql)
	cursor.execute(query)
	jobs = cursor.fetchall()

	"""Iterate all jobs"""
	for job in jobs:
		# Get current job status
		job_status = scrapyd.job_status(PROJECT_NAME, job[0])

		# Update DB based on new job status
		query = "UPDATE spiderjobs SET status=%s WHERE jobid=%s;"
		cursor.execute(query, (job_status, job[0]))
		conn.commit()

	end_db_conn(conn, cursor)


"""Return a list of available Spiders from Scrapyd"""
def retrieve_spiders():
	from __main__ import app
	list_spiders = requests.get("http://{}:6800/listspiders.json?project={}".format(app.config["APP_IP"], PROJECT_NAME))
	return ast.literal_eval(list_spiders.text)["spiders"]


"""Submit a Job to a user-defined Spider"""
def submit_job(mysql, form):
	scrapyd = init_scrapyd()

	"""
	Retrieve JobID from DB to query against Scrapyd
	- Based on user-input URL & Spider, and status is Pending/Running
	"""
	query = "SELECT jobid from spiderjobs WHERE url=%s AND spider=%s AND (status='pending' OR status='running');"
	conn, cursor = start_db_conn(mysql)
	cursor.execute(query, (form.url.data, form.spiderChoice.data))
	job_id = cursor.fetchone()
	end_db_conn(conn, cursor)
	print("job_id: {}".format(job_id))

	if job_id == None:
		"""If JobID does NOT exist, create a new Scrapyd Job"""
		print("URL & Spider do NOT exist in DB / have not completed")
		insert_job(form, scrapyd, mysql, conn, cursor)

	else:
		"""Else JobID exists, query Scrapyd for Job status"""
		job_status = scrapyd.job_status(PROJECT_NAME, job_id[0])
		print("job_status: {}".format(job_status))

		# If status is finished, create a new Scrapyd Job
		if job_status == "finished":
			insert_job(form, scrapyd, mysql, conn, cursor)

		# Else the Job exists and is not yet completed; aka Duplicated Job
		elif job_status == "pending" or job_status == "running":
			flash(u"This URL is currently queued/running by the {} Spider".format(form.spiderChoice.data.capitalize()), "danger")


"""Schedule new Scrapyd Job & Insert in Database"""
def insert_job(form, scrapyd, mysql, conn, cursor):
	new_job_id = scrapyd.schedule(
					PROJECT_NAME,
					spider=form.spiderChoice.data,
					url=form.url.data,
					depth=form.scrapingDepth.data)

	# Insert new Job's details into DB
	query = "INSERT INTO `scfami_spider`.`spiderjobs` \
			(`project`,`spider`,`jobid`,`url`,`depth`,`status`)\
			VALUES (%s, %s, %s, %s, %s, %s);"
	conn, cursor = start_db_conn(mysql)
	cursor.execute(query, (
					PROJECT_NAME,
					form.spiderChoice.data,
					new_job_id,
					form.url.data,
					form.scrapingDepth.data,
					scrapyd.job_status(PROJECT_NAME, new_job_id)))
	conn.commit()
	end_db_conn(conn, cursor)
	print("New Job executed")
	flash(u"URL has been submitted for crawling", "success")


"""Retrieve all Jobs from all Spiders"""
def retrieve_spider_jobs(mysql, filter_url="unique"):
	db_columns = ("project", "spider", "jobid", "url", "depth", "status", "datetime")

	"""Retrieve Jobs that are pending/running from DB"""
	conn, cursor = start_db_conn(mysql)
	cursor.execute("SELECT * from spiderjobs WHERE (status='pending' OR status='running');")
	running_data_tuple = cursor.fetchall()

	"""Retrieve Jobs that are completed from DB"""
	query = "SELECT ANY_VALUE(datetime), ANY_VALUE(spider), ANY_VALUE(jobid), ANY_VALUE(url), ANY_VALUE(depth), ANY_VALUE(status), MAX(datetime) FROM spiderjobs WHERE status='finished' GROUP BY url ORDER BY MAX(datetime) DESC;"

	if filter_url == "unique":
		cursor.execute(query)
		unique_data_tuple = None
	else:
		cursor.execute(query)
		unique_data_tuple = cursor.fetchall()

		query = "SELECT * FROM spiderjobs WHERE (status='finished' AND url=%s) ORDER BY datetime DESC;"
		cursor.execute(query, (filter_url))

	finished_data_tuple = cursor.fetchall()
	end_db_conn(conn, cursor)

	"""Format & Append pending/running Jobs into a list"""
	running_list = []
	for rows in running_data_tuple:
		formatted_row = {db_columns[i] : rows[i] for i, _ in enumerate(rows)}
		running_list.append(formatted_row)

	"""Format & Append completed Jobs into a list"""
	finished_list = []
	for rows in finished_data_tuple:
		formatted_row = {db_columns[i] : rows[i] for i, _ in enumerate(rows)}
		finished_list.append(formatted_row)

	"""Format & Append completed unique Jobs into a list"""
	if unique_data_tuple is not None:
		unique_list = []
		for rows in unique_data_tuple:
			formatted_row = {db_columns[i] : rows[i] for i, _ in enumerate(rows)}
			unique_list.append(formatted_row)
	else:
		unique_list = finished_list

	return running_list, finished_list, unique_list


########## END Spider ##########
########## START Help ##########
# Code Here
########## END Help ##########
