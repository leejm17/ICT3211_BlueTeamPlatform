from flask import Flask, render_template, redirect, url_for, request, flash
from dotenv import load_dotenv, find_dotenv
import os
import dotenv

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

dotenv_file = dotenv.find_dotenv('.env')
dotenv.load_dotenv(dotenv_file, override=False)

# Global Variables
load_dotenv(find_dotenv())   # Take environment variables from .env
windows_ip = os.getenv("windows_ip")
debian_ip = os.getenv("debian_ip")
ftp_user = os.getenv("ftp_user")
ftp_pw = os.getenv("ftp_pw")

db_pwd = os.environ["db_pwd"]
db_user = os.environ["db_user"]
database_db = os.environ["database_db"]
db_host = os.environ["db_host"]

# Create Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the random string'

PROJECT_NAME =  'yara_scrapy'
# Flask DB Config
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql:///' + os.path.join(basedir, 'scfami-spyder.db')
#db = SQLAlchemy(app)    
app.config['MYSQL_DATABASE_USER'] = db_user
app.config['MYSQL_DATABASE_PASSWORD'] = db_pwd
app.config['MYSQL_DATABASE_DB'] = database_db
app.config['MYSQL_DATABASE_HOST'] = db_host
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



@app.route('/spider', methods = ['POST', 'GET'])
def spyder_submission_page():      
    return render_template('/spyder/spyder.html')
	  

@app.route('/spidersubmission', methods = ['POST', 'GET'])
def spyder_submission_page_2():
	form = SpyderForm()
	if form.validate_on_submit():
		values = form.data
		for key, value in values.items():
			if key == "githubUrl":
				url = value
			if key == "scrapingDepth":
				depth = int(value)
			if key == "spiderChoice":
				spider = value
		
		conn = mysql.connect()
		cursor = conn.cursor()
		
		# for current url, check if its status is "running" in DB and get its jobid
		query = "SELECT jobid from spiderjobs WHERE url = %s AND spider = %s AND status = 'running'"
		cursor.execute(query, (url, spider))
		jobid = cursor.fetchone()
		print (jobid)

		# if url does not exist in DB and does not have a running job, allow user to submit job
		if jobid == None:
			print("URL does not exist in DB and does not have a running job")
			generatedJobid = scrapyd.schedule(PROJECT_NAME, spider, url=url, depth = depth)
			setStatus = 'running'
			# insert url, jobid and other details into the database
			query = "INSERT INTO `scfami_spider`.`spiderjobs` \
					(`project`,`spider`,`jobid`,`url`,`depth`,`status`)\
						VALUES (%s,%s,%s,%s, %s, %s);"
			cursor.execute(query, (PROJECT_NAME, spider, generatedJobid, url, depth, setStatus))
			conn.commit()
			print("Insert Query executed")

			flash(u'URL has been submitted for crawling', 'success')

		else:
			# if url is tagged as running in DB 
			# check if its still running  or finished in scrapyd
			if jobid is not None:
				jobid = jobid[0]
				jobstatus = scrapyd.job_status(PROJECT_NAME, jobid)
				# jobstatus = 'running'

				if jobstatus == 'running' or jobstatus == 'pending':
					flash(u'URL and its respective Spider is currently queued or running', 'danger')

				if jobstatus == 'finished':
					print("finished")
					print("Old Job ID is: " , jobid)
					query = "UPDATE spiderjobs SET status = 'finished' WHERE jobid = %s"
					cursor.execute(query, (jobid,))
					conn.commit()
					print("Update Query executed")

					generatedJobid = scrapyd.schedule(PROJECT_NAME, spider, url=url, depth = depth)
					print("New Job ID is: " , generatedJobid)
					query = "INSERT INTO `scfami_spider`.`spiderjobs` \
					(`project`,`spider`,`jobid`,`url`,`depth`,`status`)\
						VALUES (%s,%s,%s,%s, %s, %s);"
					setStatus = 'running'
					print(setStatus)
					cursor.execute(query, (PROJECT_NAME, spider, generatedJobid, url, depth, setStatus))
					conn.commit()
					print("Insert Query executed")
					flash(u'URL has been submitted for crawling', 'success')
			
		cursor.close()
		conn.close()
	
	statuses  = requests.get('http://localhost:6800/daemonstatus.json').json()
	runningJobs = 0
	finishedJobs = 0
	for status, value in statuses.items():
		if (status == "running") :
			runningJobs += value
		if (status == "pending"):
			runningJobs += value
		if (status == "finished") :
			finishedJobs += value
				
	return render_template('/spider/spidersubmission.html', form = form, runningJobs = runningJobs)


# @app.route('/schedulespyder', methods = ['POST', 'GET'])
# def scehdule_spyder_submission():
# 	form = SpyderForm() 
# 	if form.validate_on_submit():
# 		print (form.data)
				
# 	return render_template('/spyder/schedulespyder.html', form = form)


@app.route('/spiderjobs', methods = ['POST', 'GET'])
def spyder_jobs_deatails():
	conn = mysql.connect()
	cursor = conn.cursor()

	inputTuple_1 = ('project', 'spider', 'jobid', 'url', 'depth', 'status')

	# if status equal running 
	cursor.execute("SELECT * from spiderjobs WHERE status = 'running' ")
	runningDataTuple = cursor.fetchall()
	runningDict = []
	for rows in runningDataTuple:
		resultDictionary = {inputTuple_1[i] : rows[i] for i, _ in enumerate(rows)}
		runningDict.append(resultDictionary)
	print(runningDict)

	if request.method == "POST":
		print(request.form["filter"])

	# if status equal finished
	cursor.execute("SELECT DISTINCT URL from spiderjobs WHERE status = 'finished' ")
	finishedDataTuple = cursor.fetchall()
	finishedDict = []
	for rows in finishedDataTuple:
		resultDictionary = {inputTuple_1[i] : rows[i] for i, _ in enumerate(rows)}
		finishedDict.append(resultDictionary)

	print(finishedDict)
	cursor.close()
	conn.close()

	return render_template('/spider/spiderjobs.html', finishedDict=finishedDict, runningDict=runningDict)

	
@app.route('/submit', methods = ['POST', 'GET'])
def spyder_submission_detail_page():
	submissions =  request.form
	for k, v in submissions.items():
			print(k, v)
			
	# send POST requests to scrapyd in code below

	# display return values from scrapyd to submissiondetails.html
	return render_template('/spyder/submissiondetails.html', submissions=submissions.values())
