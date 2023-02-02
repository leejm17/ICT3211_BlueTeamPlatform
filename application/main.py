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

def initiate_ftp():
	endpoint = request.referrer.split("/")[-1]
	if endpoint == "smart_meter":
		# Initiate FTP for Smart Meter
		print("Initiate FTP for Smart Meter")
		files = windows_ftp_start()
	elif endpoint == "t_pot":
		# Initiate FTP for T-Pot
		files = ""
		print("Initiate FTP for T-Pot")
	else:
		files = ""
	return files


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


def windows_ftp_start():
	ftps = MyFTP_TLS(host=windows_ip, user=ftp_user, passwd=ftp_pw)
	ftps.prot_p()		# Set up secure connection
	root = ftps.mlsd()	# FTP Root directory
	file_dict = {}		# Store Dir & corresponding Filenames
	for dir_list in root:
		# dir_list[0] = dir/filename
		# dir_list[1] = dir/file data
		#print(dir_list[0])		# Print Dir
		file_dict[dir_list[0]] = []
		if dir_list[1]["type"] == "dir":
			file_list = ftps.mlsd(dir_list[0])
			for data in file_list:
				#print(data[0])	# Print Filename
				file_dict[dir_list[0]] += [data[0]]
	ftps.quit()
	#print(file_dict)	# Print stored dictionary
	return file_dict


def windows_ftp_transfer(form_data):
	file_dict = {}
	download_dir = ""
	download_cnt = 0	# Count number of files downloaded

	for selection in form_data:
		directory, filename = selection.split("-")
		if directory not in file_dict:
			file_dict[directory] = []
		file_dict[directory] += [filename]

	# Download files via FTPS
	ftps = MyFTP_TLS(host=windows_ip, user=ftp_user, passwd=ftp_pw)
	ftps.prot_p()		# Set up secure connection

	for directory in file_dict:
		# Write file in binary mode
		try:
			ftps.cwd("/"+directory)			# Change FTP directory
			current_dir = os.getcwd()
			download_dir = "/".join(current_dir.split("/")[:-2]) + "/FTP_Downloads/Smart_Meter/" + directory
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

			os.chdir(current_dir)		# Revert to CWD

		except Exception as e:
			print("Error Downloading File:", e)
			return False, e
	
	ftps.quit()

	download_dir = "/".join(download_dir.split("/")[:-1])	# Re-store the Download directory
	message = [download_cnt, download_dir]
	return True, message


########### END Data Transfer ###########


########## START App Launch ##########
# Code Here
########### END App Launch ###########


########## START Help ##########
# Code Here
########### END Help ###########
