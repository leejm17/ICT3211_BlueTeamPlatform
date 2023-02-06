from flask import request
from dotenv import load_dotenv
from zipfile import ZipFile
import os
import ftplib, ssl
import magic


# Global Variables
load_dotenv()   # Take environment variables from .env
windows_ip = os.getenv("windows_ip")
debian_ip = os.getenv("debian_ip")
ftp_user = os.getenv("ftp_user")
ftp_pw = os.getenv("ftp_pw")


########## START Data Transfer ##########

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

#"""
def windows_ftp_process(form):
	print("data_source:", form["data_source"])
	print("meters:", form.getlist("meters"))
	print("file_type:", form["file_type"])
	success, file_dict = windows_ftp_initiate(form["data_source"], form.getlist("meters"), form["file_type"])
	if not success:
		return success, file_dict

	print("date:", form["date"])
	print("start_time:", form["start_time"])
	print("end_time:", form["end_time"])
	file_dict = windows_ftp_filter_datetime(form["date"], form["start_time"], form["end_time"], file_dict)

	success, message = windows_ftp_transfer(form["data_source"], file_dict)

	#print("export_name:", form["export_name"])
	return success, message


def windows_ftp_initiate(ftp_dir, meters, file_type):
	try:
		ftps = MyFTP_TLS(host=windows_ip, user=ftp_user, passwd=ftp_pw)
		ftps.prot_p()		# Set up secure connection
		root = ftps.mlsd(ftp_dir)	# FTP Root directory
	except Exception as e:
		try:
			ftps.quit()
		except Exception as econn:
			print("Smart Meter Windows machine is NOT online.")
			return False, e
		print("FTP Connection Error:", e)
		return False, e
		
	file_dict = {}		# Store Dir & corresponding Filenames
	try:
		for dir_list in root:
			if dir_list[0] in meters:
				# dir_list[0] = dir/filename
				# dir_list[1] = dir/file data
				##print("Dir:", dir_list[0])		# Print Dir
				file_dict[dir_list[0]] = []
				if dir_list[1]["type"] == "dir":
					file_list = ftps.mlsd(ftp_dir+"/"+dir_list[0])
					for csv_file in file_list:
						if file_type.lower() == csv_file[0].split(".")[-1]:
							##print("File:", csv_file[0])	# Print Filename
							file_dict[dir_list[0]] += [csv_file[0]]
		ftps.quit()
		##print("Dict:", file_dict)	# Print stored dictionary
		return True, file_dict
	except Exception as e:
		ftps.quit()
		print("File Permissions Error:", e)
		##print("Dict:", file_dict)	# Print stored dictionary
		return False, e


def windows_ftp_filter_datetime(date, start_time, end_time, file_dict):
	filtered_dict = {}
	date = date.replace("-", "")
	# Convert Start-End times to int to compare filenames faster
	start_time = int(start_time.replace(":", "") + "00")
	end_time = int(end_time.replace(":", "") + "00")

	for meter in file_dict:
		filtered_dict[meter] = []
		for csv_file in file_dict[meter]:
			filtered_date_file = csv_file.split("_")[0]
			##print(date, filtered_date_file)	# Print Filtered Date & Date of selected .csv file

			# Filter .csv filename if date is same
			if filtered_date_file == date:
				filtered_time_file = int(csv_file.split("_")[1].split(".")[0])
				##print(start_time, filtered_time_file, end_time)	# Print Filtered Start-End times & Time of selected .csv file

				# Store .csv filename if Start-End times are within filtered range
				if (filtered_time_file >= start_time) and (filtered_time_file <= end_time):
					filtered_dict[meter] += [csv_file]
	return filtered_dict


# Download filtered files from file_dict via FTP
def windows_ftp_transfer(data_source, file_dict):
	download_dir = ""
	download_cnt = 0	# Count number of files downloaded
	directory_cnt = 0	# Count number of directories downloaded into
	##print("data_source file_dict:", data_source, file_dict)

	try:
		# Download files via FTPS
		ftps = MyFTP_TLS(host=windows_ip, user=ftp_user, passwd=ftp_pw)
		ftps.prot_p()		# Set up secure connection

		for meter in file_dict:
			if len(file_dict[meter]) == 0:
				continue
			download_path = "/" + data_source + "/" + meter
			ftps.cwd(download_path)		# Change FTP directory
			current_dir = os.getcwd()
			download_dir = "/".join(current_dir.split("/")[:-2]) + "/FTP_Downloads/Smart_Meter" + download_path
			if not os.path.isdir(download_dir):		# Mkdir if Download directory does not exist
				os.makedirs(download_dir)
			os.chdir(download_dir)		# Change Download directory

			print("Downloading files for", meter)
			for csv_file in file_dict[meter]:	# Download every selected file from this FTP directory
				with open(csv_file, "wb") as f:
					# Command for Downloading the file "RETR csv_file"
					ftps.retrbinary(f"RETR {csv_file}", f.write)
					download_cnt += 1
			print("Downloaded", download_cnt, "files so far")
			directory_cnt += 1
			os.chdir(current_dir)		# Revert to CWD

	except Exception as e:
		print("Error Downloading File:", e)
		return False, e

	ftps.quit()
	download_dir = "/".join(download_dir.split("/")[:-1])	# Re-store the Download directory
	message = [download_cnt, directory_cnt, download_dir]
	return True, message


"""
def initiate_ftp(ftp_dir):
	endpoint = request.referrer.split("/")[-1]
	if endpoint == "smart_meter":
		# Initiate FTP for Smart Meter
		print("Initiate FTP for Smart Meter")
		files = windows_ftp_start(ftp_dir)
	elif endpoint == "t_pot":
		# Initiate FTP for T-Pot
		files = ""
		print("Initiate FTP for T-Pot")
	else:
		files = ""
	return files


def windows_ftp_start(ftp_dir):
	try:
		ftps = MyFTP_TLS(host=windows_ip, user=ftp_user, passwd=ftp_pw)
		ftps.prot_p()		# Set up secure connection
		root = ftps.mlsd(ftp_dir)	# FTP Root directory
	except Exception as e:
		try:
			ftps.quit()
		except Exception as econn:
			print("Smart Meter Windows machine is NOT online.")
			return False, e
		print("FTP Connection Error:", e)
		return False, e
		
	file_dict = {}		# Store Dir & corresponding Filenames
	try:
		for dir_list in root:
			# dir_list[0] = dir/filename
			# dir_list[1] = dir/file data
			##print("Dir:", dir_list[0])		# Print Dir
			file_dict[dir_list[0]] = []
			if dir_list[1]["type"] == "dir":
				file_list = ftps.mlsd(ftp_dir+"/"+dir_list[0])
				for data in file_list:
					##print("File:", data[0])	# Print Filename
					file_dict[dir_list[0]] += [data[0]]
		ftps.quit()
		##print("Dict:", file_dict)	# Print stored dictionary
		return True, file_dict
	except Exception as e:
		ftps.quit()
		print("File Permissions Error:", e)
		##print("Dict:", file_dict)	# Print stored dictionary
		return False, e
	

def windows_ftp_transfer(source, form_data):
	file_dict = {}
	download_dir = ""
	download_cnt = 0	# Count number of files downloaded
	directory_cnt = 0	# Count number of directories downloaded into
	##print("form_data:",form_data)

	for selection in form_data:
		directory, filename = selection.split(":")
		if directory not in file_dict:
			file_dict[directory] = []
		file_dict[directory] += [filename]

	try:
		# Download files via FTPS
		ftps = MyFTP_TLS(host=windows_ip, user=ftp_user, passwd=ftp_pw)
		ftps.prot_p()		# Set up secure connection

		for directory in file_dict:
			if len(file_dict[directory]) == 0:
				continue
			##print("directory:",directory)
			# Write file in binary mode
			download_path = source[0] + "/" + directory
			ftps.cwd("/"+download_path)			# Change FTP directory
			current_dir = os.getcwd()
			download_dir = "/".join(current_dir.split("/")[:-2]) + "/FTP_Downloads/Smart_Meter/" + download_path
			if not os.path.isdir(download_dir):		# Mkdir if Download directory does not exist
				os.makedirs(download_dir)
			os.chdir(download_dir)		# Change Download directory

			print("Downloading files for", directory)
			for filename in file_dict[directory]:	# Download every selected file from this FTP directory
				with open(filename, "wb") as f:
					# Command for Downloading the file "RETR filename"
					ftps.retrbinary(f"RETR {filename}", f.write)
					download_cnt += 1

				# Unzip zipped files
				if magic.from_file(filename, mime=True) == "application/zip":
					with ZipFile(filename, "r") as zipped:
						zipped.extractall(".".join(filename.split(".")[:-1]))

			print("Downloaded", download_cnt, "files so far")
			directory_cnt += 1
			os.chdir(current_dir)		# Revert to CWD

	except Exception as e:
		print("Error Downloading File:", e)
		return False, e
	
	ftps.quit()

	download_dir = "/".join(download_dir.split("/")[:-1])	# Re-store the Download directory
	message = [download_cnt, directory_cnt, download_dir]
	return True, message
"""


########### END Data Transfer ###########


########## START App Launch ##########
# Code Here
########### END App Launch ###########


########## START Help ##########
# Code Here
########### END Help ###########
