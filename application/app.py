from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv, find_dotenv
import os

# Import Other Files
from main import windows_ftp_process
#from main import initiate_ftp, windows_ftp_transfer
from forms import DataTransfer_Form, SpyderForm


# Import Library for commmunication with scapyd scraper
from scrapyd_api import ScrapydAPI
scrapyd = ScrapydAPI('http://localhost:6800')
import requests,json

# SQLAlchemy for intrecatiung with DB to keep track of submitted URLs, JobIDs and status
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flaskext.mysql import MySQL


# Global Variables
load_dotenv(find_dotenv())   # Take environment variables from .env
windows_ip = os.getenv("windows_ip")
debian_ip = os.getenv("debian_ip")
ftp_user = os.getenv("ftp_user")
ftp_pw = os.getenv("ftp_pw")

# Create Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the random string'

PROJECT_NAME =  'yara_scrapy'
# Flask DB Config
# db_user = os.environ.get("db_user")
# db_pw = os.getenv("db_pw")
# db_key = os.getenv("db_key")

# db_key = "JLKJJJO3IURYoiouolnojojouuoo=5y9y9youjuy952oohhbafdnoglhoho"
# db_username = "mysql+pymysql://root:@localhost:3306/scfami-spyder"
# db_pwd = "P@ssw0rdpsBenU7Wka"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql:///' + os.path.join(basedir, 'scfami-spyder.db')
#db = SQLAlchemy(app)    
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'P@ssw0rdpsBenU7Wka'
app.config['MYSQL_DATABASE_DB'] = 'scfami_spyder'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql = MySQL(app)


# App routes
@app.route("/", methods=["GET"], endpoint="home")
def home_page():
    return render_template("/home.html")


@app.route("/admin", methods=["GET"], endpoint="admin")
def admin_page():
    return render_template("/admin/admin_config.html")


@app.route("/admin/honeypot", methods=["GET"], endpoint="honeypot")
def admin_honeypot_page():
    return render_template("/admin/honeypot.html")


# @app.route("/admin/spyder", methods=["GET"], endpoint="spyder")
# def admin_spyder_page():
#     return render_template("/admin/spyder.html")


@app.route("/admin/pcap_files", methods=["GET"], endpoint="pcap_files")
def admin_pcapfiles_page():
    return render_template("/admin/pcap_files.html")


@app.route("/admin/machine_learning", methods=["GET"], endpoint="machine_learning")
def admin_machinelearning_page():
    return render_template("/admin/machine_learning.html")


@app.route("/data_transfer", methods=["GET"], endpoint="data_transfer")
def datatransfer_page():
    return render_template("/data_transfer/data_transfer.html")


@app.route("/data_transfer/smart_meter", methods=["GET", "POST"], endpoint="data_transfer.smart_meter")
def datatransfer_smartmeter_page():
	form = DataTransfer_Form()
	if request.method == "POST":
		if request.form:
			#"""
			success, message = windows_ftp_process(request.form)
			if success:
				return render_template("/data_transfer/download_success.html", message=message)
			else:
				return render_template("/data_transfer/download_failure.html", message=message)
			"""
			ftp_dir = ["SmartMeterData", "Archive_SmartMeterData", "WiresharkData"]
			if request.form["smart_meter_form"] in ftp_dir:
				success, files = initiate_ftp(request.form["smart_meter_form"])
				if success:
					return render_template("/data_transfer/smart_meter.html", ip=windows_ip, file_dict=files, data_source=request.form["smart_meter_form"], form=form)
				else:
					return render_template("/data_transfer/connection_failure.html", ip=windows_ip, message=files)
			else:
				success, message = windows_ftp_transfer(request.form.getlist("data_source"), request.form.getlist("smart_meter_form"))
				if success:
					return render_template("/data_transfer/download_success.html", message=message)
				else:
					return render_template("/data_transfer/download_failure.html", message=message)
			"""
	return render_template("/data_transfer/smart_meter.html", ip=windows_ip, form=form)


@app.route("/data_transfer/t_pot", methods=["GET"], endpoint="data_transfer.t_pot")
def datatransfer_tpot_page():
    return render_template("/data_transfer/t_pot.html", ip=debian_ip)


@app.route("/app_launch", methods=["GET"], endpoint="app_launch")
def applaunch_page():
    return render_template("/app_launch.html")


@app.route("/help", methods=["GET"], endpoint="help")
def help_page():
    return render_template("/help.html")



@app.route('/spyder', methods = ['POST', 'GET'])
def spyder_submission_page():      
    return render_template('/spyder/spyder.html')
	  

@app.route('/spydersubmission', methods = ['POST', 'GET'])
def spyder_submission_page_2():
	form = SpyderForm() 
	if form.validate_on_submit():
		values = form.data
		for key, value in values.items():
			if key == "githubUrl":
				url = value
			if key == "scrapingDepth":
				depth = int(value)
			if key == "spyderChoice":
				spyder = value
		
		# check if more than 5 curent running spiders 
		# do not allow user to continue with submission and return error message  
		statuses  = requests.get('http://localhost:6800/daemonstatus.json').json()
		for status, value in statuses.items():
			if (status == "running") and (value >= 5):
				print(status, value)
				print(type(status), type(value))

				return render_template('/spyder/spyder2.html', form = form)
	
		# for current url, check if its status is "running" in DB and get its jobid
		conn = mysql.connect()
		cursor = conn.cursor()
		
		query = "SELECT jobid from spyderjobs WHERE url = %s AND spyder = %s AND status = 'running'"
		cursor.execute(query, (url, spyder))
		jobid = cursor.fetchone()
		print (jobid)
		# if url does not have a running job, allow user to submit job
		if jobid == None:
			print("Empty")
			# if url does not have a running job, allow user to submit job
			generatedJobid = scrapyd.schedule(PROJECT_NAME, spyder, url=url, depth = depth)
			setStatus = 'running'
			
			# insert url, jobid and other details into the database
			query = "INSERT INTO `scfami_spyder`.`spyderjobs` \
					(`project`,`spyder`,`jobid`,`url`,`depth`,`status`)\
						VALUES (%s,%s,%s,%s, %s, %s);"
			cursor.execute(query, (PROJECT_NAME, spyder, generatedJobid, url, depth, setStatus))
			conn.commit()
			print("Insert Query executed")

		else:
			# if url is tagged as running in DB 
			# check if its still running in scrapyd
			if jobid is not None:
				jobid = jobid[0]
				jobstatus = scrapyd.job_status(PROJECT_NAME, jobid)
				if jobstatus == 'running':
					# return render_template('/spyder/spyder2.html', form = form)
					print("")

				if jobstatus == 'finished':
					print("finished")
					print("Old Job ID is: " , jobid)
					query = "UPDATE spyderjobs SET status = 'finished' WHERE jobid = %s"
					cursor.execute(query, (jobid,))
					conn.commit()
					print("Update Query executed")

					generatedJobid = scrapyd.schedule(PROJECT_NAME, spyder, url=url, depth = depth)
					print("New Job ID is: " , generatedJobid)
					query = "INSERT INTO `scfami_spyder`.`spyderjobs` \
					(`project`,`spyder`,`jobid`,`url`,`depth`,`status`)\
						VALUES (%s,%s,%s,%s, %s, %s);"
					setStatus = 'running'
					print(setStatus)
					cursor.execute(query, (PROJECT_NAME, spyder, generatedJobid, url, depth, setStatus))
					conn.commit()
					print("Insert Query executed")
			
		cursor.close()
		conn.close()
				
	return render_template('/spyder/spydersubmission.html', form = form)


# @app.route('/schedulespyder', methods = ['POST', 'GET'])
# def scehdule_spyder_submission():
# 	form = SpyderForm() 
# 	if form.validate_on_submit():
# 		print (form.data)
				
# 	return render_template('/spyder/schedulespyder.html', form = form)


@app.route('/spyderjobs', methods = ['POST', 'GET'])
def spyder_jobs_deatails():
	
	# conn = mysql.connect()
	# cursor = conn.cursor()
	# cursor.execute("SELECT * from spyderjobs")
	# data = cursor.fetchone()
	# print(data)
	jobs = scrapyd.list_jobs(PROJECT_NAME)
	status  = requests.get('http://localhost:6800/daemonstatus.json').json()

	print (status)

	for status, v  in jobs.items():
		if status == "pending":
			pendingDict = v
			for values in v:
				print (values)

		if status == "running":
			runningDict = v
			for values in v:
				print (values)
		
		if status == "finished":
			finishedDict = v
			for values in v:
				# print (values)
				print ("\n")

	return render_template('/spyder/spyderjobs.html', finishedDict=finishedDict, runningDict=runningDict, pendingDict=pendingDict)
	
@app.route('/submit', methods = ['POST', 'GET'])
def spyder_submission_detail_page():
	submissions =  request.form
	for k, v in submissions.items():
			print(k, v)
			
	# send POST requests to scrapyd in code below

	# display return values from scrapyd to submissiondetails.html
	return render_template('/spyder/submissiondetails.html', submissions=submissions.values())
