import ftplib, ssl
from concurrent import futures
import queue

# Import Local Files
from admin import retrieve_glob_var, retrieve_database_var
import getpass


########## START Flask Configurations ##########

"""Global Configs"""
class Config:
	APP_IP = "localhost"	# "172.16.2.6"
	APP_PORT = 6065
	APP_DIR = "/home/{}/Documents/ICT3211_BlueTeamPlatform/application".format(getpass.getuser())

	# Flask DB Config
	db = retrieve_database_var()
	MYSQL_DATABASE_HOST = db["db_host"]
	MYSQL_DATABASE_DB = db["database_db"]
	MYSQL_DATABASE_USER = db["db_user"]
	MYSQL_DATABASE_PASSWORD = db["db_pwd"]
	SECRET_KEY = db["secret"]


"""Development Configuration"""
class DevConfig(Config):
	FLASK_ENV = "development"
	DEBUG = True
	TESTING = True


"""Production Configuration"""
class ProdConfig(Config):
	FLASK_ENV = "production"
	DEBUG = False
	TESTING = False


########## END Flask Configurations ##########
########## START FTP Methods ##########

"""
Explicit FTPS, with shared TLS session
- Using: https://stackoverflow.com/questions/14659154/ftps-with-python-ftplib-session-reuse-required/43301750#43301750
- Refer: https://stackoverflow.com/questions/48260616/python3-6-ftp-tls-and-session-reuse
"""
class MyFTP_TLS(ftplib.FTP_TLS):	
	def ntransfercmd(self, cmd, rest=None):
		conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
		if self._prot_p:
			conn = self.context.wrap_socket(conn, server_hostname=self.host, session=self.sock.session)
		return conn, size


"""Modular way to Initiate FTP Connection"""
def init_ftps_conn():
	global_dict = retrieve_glob_var()
	ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
	ftps.prot_p()		# Set up secure connection
	return ftps


"""Download File via FTP"""
def download_file(csv_file, ftps):
	with open(csv_file, "wb") as f:
		# Command for Downloading the file "RETR csv_file"
		ftps.retrbinary(f"RETR {csv_file}", f.write)


########## END FTP Methods ##########
########## START Threading: Data Transfer ##########

def thread_datatransfer(directory, mini_list, index):
	##print("\t\tWorker {} starting".format(index+1))

	"""Initialise FTP Connection"""
	ftps = init_ftps_conn()

	try:
		"""Download filtered files from this folder (FTP directory)"""
		ftps.cwd("/"+directory)		# Change FTP directory
		for csv_file in mini_list:
			try:
				download_file(csv_file, ftps)
			except Exception as e:
				""" Either of 1 or 2:
				1. EOF occurred in violation of protocol (_ssl.c: 2396)
				2. [SSL: Bad Length] bad length (_ssl.c: 2396)
				Both mean: FileZilla session authentication issue OR Transfer limit reached
				- FTP session terminated automatically
				"""
				ftps.close()		# Close the connection
				ftps = init_ftps_conn()	# Initialise a new FTPS connection to re-authenticate session & reset transfer limit
				ftps.cwd("/"+directory)		# Change FTP directory

				"""Attempt to download file again"""
				try:
					download_file(csv_file, ftps)
				except Exception as econn:
					print("\t\t{} {}".format(e, econn))
					print("\t\tFile name: {}".format(csv_file))

	except Exception as e:
		try:
			print("\t\tError Downloading File: {}".format(e))
		except Exception as econn:
			print(econn)
		return False, e

	ftps.close()

	##print("\t\tWorker {} finished".format(index+1))


########## END Threading: Data Transfer ##########
########## START MySQL Database ##########

# Source: https://stackoverflow.com/questions/5504340/python-mysqldb-connection-close-vs-cursor-close
"""Connect MySQL & Return cursor"""
def start_db_conn(mysql):
	conn = mysql.connect()
	return conn, conn.cursor()	# Create connection & cursor


"""Close MySQL Conn"""
def end_db_conn(conn, cursor):
	cursor.close()	# Close the cursor
	conn.close()	# Close the connection


########## END MySQL Database ##########
