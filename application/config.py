""" Flask Configurations """
import ftplib, ssl

# Import Local Files
from admin import retrieve_glob_var, retrieve_database_var
import getpass


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
def init_conn():
	global_dict = retrieve_glob_var()
	ftps = MyFTP_TLS(host=global_dict["windows_ip"], user=global_dict["ftp_user"], passwd=global_dict["ftp_pw"])
	ftps.prot_p()		# Set up secure connection
	return ftps


"""Download File via FTP"""
def download_file(csv_file, ftps):
	with open(csv_file, "wb") as f:
		# Command for Downloading the file "RETR csv_file"
		ftps.retrbinary(f"RETR {csv_file}", f.write) 
		return 1
	return 0


########## END FTP Methods ##########
