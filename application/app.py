from flask import Flask, render_template, redirect, url_for, request, flash
import os, subprocess, ast
import requests, json

# Import Local Files
from main import windows_ftp_start, windows_ftp_process, windows_ftp_automate, retrieve_cronjobs, action_cronjobs
from main import list_of_local_apps, retrieve_arkime_views

from admin import retrieve_glob_var, retrieve_arkime_var, retrieve_networkcapture_var, update_env

from forms import DataTransfer_Form, Spider_Form
from forms import AdminConfig_DataTransfer_Form, AdminConfig_AppLaunch_Form, AdminConfig_NetworkCapture_Form

# Import Library for commmunication with scapyd scraper
from scrapyd_api import ScrapydAPI
scrapyd = ScrapydAPI("http://localhost:6800")
from flaskext.mysql import MySQL


# Create Flask App
app = Flask(__name__)
app.config.from_object("config.DevConfig")	# Using a development configuration
##app.config.from_object("config.ProdConfig")	# Using a production configuration

mysql = MySQL(app)	# Initialise MySQL Database
PROJECT_NAME =  "yara_scrapy"


# App routes
@app.route("/", methods=["GET"], endpoint="home")
def home_page():
	return render_template("/home.html")


########## START Admin Config Pages ##########

@app.route("/admin", methods=["GET"], endpoint="admin")
def admin_page():
	return render_template("/admin/admin_config.html")


@app.route("/admin/data_transfer", methods=["GET", "POST"], endpoint="admin.data_transfer")
def admin_datatransfer_page():
	form = AdminConfig_DataTransfer_Form(request.form)
	if request.method == "POST":
		"""Update .datatransfer with new values"""
		updated_configs = update_env("datatransfer", form)
		return render_template("/admin/config_success.html", form=form, configs=updated_configs)

	return render_template("/admin/config_data_transfer.html", form=form)


@app.route("/admin/app_launch", methods=["GET", "POST"], endpoint="admin.app_launch")
def admin_applaunch_page():
	form = AdminConfig_AppLaunch_Form(request.form)
	if request.method == "POST":
		"""Update .arkime with new values"""
		updated_configs = update_env("arkime", form)
		return render_template("/admin/config_success.html", form=form, configs=updated_configs)

	return render_template("/admin/config_app_launch.html", form=form)


@app.route("/admin/networkcapture", methods=["GET", "POST"], endpoint="admin.networkcapture")
def admin_networkcapture_page():
	form = AdminConfig_NetworkCapture_Form(request.form)
	if request.method == "POST":
		"""Update .networkcapture with new values"""
		updated_configs = update_env("networkcapture", form)
		return render_template("/admin/config_success.html", form=form, configs=updated_configs)

	return render_template("/admin/config_networkcapture.html", form=form)


########## END Admin Config Pages ##########
########## START Data Transfer Pages ##########

@app.route("/data_transfer", methods=["GET"], endpoint="data_transfer")
def datatransfer_page():
	return render_template("/data_transfer/data_transfer.html")


@app.route("/data_transfer/smart_meter", methods=["GET", "POST"], endpoint="data_transfer.smart_meter")
def datatransfer_smartmeter_page():
	form = DataTransfer_Form(request.form)
	if request.method == "POST" and request.form:
		ftp_dir = ["SmartMeterData", "WiresharkData"]

		if "browse" in request.form["submit"]:
			"""Open FTP_Downloads folder with Files application"""
			message = ast.literal_eval(request.form["submit"].split("--")[1])
			subprocess.Popen(["xdg-open", message[1]])
			return render_template("/data_transfer/smart_meter/download_success.html", message=message)

		elif request.form["submit"] in ftp_dir:
			"""Initiate FTP Process"""
			success, dir_list = windows_ftp_start(request.form["submit"])
			form.data_source.data = request.form["submit"]
			days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
			
			# If FTP Connection Established
			if success:
				return render_template("/data_transfer/smart_meter.html", ip=global_var()["windows_ip"], form=form, dir_list=dir_list, meters=dir_list, days_of_week=days_of_week)
			# Else FTP Connection NOT Established
			else:
				return render_template("/data_transfer/connection_failure.html", ip=global_var()["windows_ip"], message=dir_list)

		else:
			"""Data Transfer Process"""
			# If Transfer Type is Now
			if form.transfer_type.data == "Now":
				# Perform Data Transfer Now
				success, message = windows_ftp_process(form)
				if success:
					return render_template("/data_transfer/smart_meter/download_success.html", message=message)
				else:
					return render_template("/data_transfer/smart_meter/download_failure.html", message=message)

			# Else Transfer Type is Scheduled
			else:
				# Schedule Data Transfer based on Form Data
				success, cron, job = windows_ftp_automate(form)
				if success:
					return render_template("/data_transfer/jobs/cronjob_success.html", cron_message=cron, job_message=job)
				else:
					return render_template("/data_transfer/jobs/cronjob_failure.html", cron_message=cron, job_message=job)

	return render_template("/data_transfer/smart_meter.html", ip=global_var()["windows_ip"], form=form)


@app.route("/data_transfer/network", methods=["GET", "POST"], endpoint="data_transfer.network")
def datatransfer_network_page():
	if request.method == "POST" and request.form["action"] == "browse":
		"""Open Files application if filepath exists"""
		filepath = networkcapture_var()["capture_path"]
		if os.path.isdir(filepath):
			print(filepath)
			subprocess.Popen(["xdg-open", filepath])
		else:
			return render_template("/data_transfer/network_capture.html", message=filepath)

	return render_template("/data_transfer/network_capture.html")


@app.route("/data_transfer/manage_jobs", methods=["GET", "POST"], endpoint="data_transfer.manage_jobs")
def datatransfer_managejobs_page():
	if request.method == "POST":
		if request.form["action"]:
			# Perform one of Action: Enable, Disable, Delete job
			action_cronjobs(request.form["action"])

	# Return of dictionary-per-job from CronTab
	return render_template("/data_transfer/manage_jobs.html", job_list=retrieve_cronjobs())


########## END Data Transfer Pages ##########
########## START App Launch Pages ##########

@app.route("/app_launch", methods=["GET"], endpoint="app_launch")
def applaunch_page():
	return render_template("/app_launch/app_launch.html")


@app.route("/app_launch/local_apps", methods=["GET", "POST"], endpoint="app_launch.local_apps")
def applaunch_localapps_page():
	"""Retrieve list of user-installed local applications"""
	app_list = list_of_local_apps()
	button_style = ["info", "primary", "success", "danger", "warning"]

	if request.method == "POST":
		try:
			# Open local application
			subprocess.Popen([request.form["action"]])
		except Exception as e:
			# If local application does NOT exist
			print("Cannot find {}: {}".format(request.form["action"], e))
			return render_template("/app_launch/local_apps.html", message=request.form["action"], app_list=app_list, style=button_style)

	return render_template("/app_launch/local_apps.html", app_list=app_list, style=button_style)


@app.route("/app_launch/arkime", methods=["GET"], endpoint="app_launch.arkime")
def applaunch_arkimeviews_page():
	"""Retrieve list of dictionary-per-view from Arkime /api/views"""
	success, views = retrieve_arkime_views()
	
	# If /api/views returns a valid list
	if success:
		arkime_views = {}
		for view in views:
			# Append each view's ID to their view's label
			arkime_views[view["name"]] = "http://{}:8005/sessions?view={}".format(request.remote_addr, view["id"])
			#arkime_views[view["name"]] = "https://{}/sessions?view={}".format(request.remote_addr, view["id"])

	# Else /api/views returns an error
	else:
		return render_template("/app_launch/arkime.html", arkime_views=views)

	button_style = ["info", "primary", "success", "danger", "warning"]
	return render_template("/app_launch/arkime.html", arkime_views=arkime_views, style=button_style)


########## END App Launch Pages ##########
########## START Spider Pages ##########

@app.route("/spider", methods=["GET"], endpoint="spider")
def spider_page():
	return render_template("/spider/spider.html")


@app.route("/spider/submit_job", methods=["GET", "POST"], endpoint="spider.submit_job")
def spider_submitjob_page():
	form = Spider_Form(request.form)
	if request.method == "POST" and form.validate_on_submit():
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
		print(jobid)

		# if url does not exist in DB and does not have a running job, allow user to submit job
		if jobid == None:
			print("URL does not exist in DB and does not have a running job")
			generatedJobid = scrapyd.schedule(PROJECT_NAME, spider, url=url, depth=depth)
			setStatus = "running"
			# insert url, jobid and other details into the database
			query = "INSERT INTO `scfami_spider`.`spiderjobs` \
					(`project`,`spider`,`jobid`,`url`,`depth`,`status`)\
					VALUES (%s,%s,%s,%s, %s, %s);"
			cursor.execute(query, (PROJECT_NAME, spider, generatedJobid, url, depth, setStatus))
			conn.commit()
			print("Insert Query executed")

			flash(u"URL has been submitted for crawling", "success")

		else:
			# if url is tagged as running in DB 
			# check if its still running or finished in scrapyd
			if jobid is not None:
				jobid = jobid[0]
				jobstatus = scrapyd.job_status(PROJECT_NAME, jobid)
				# jobstatus = "running"

				if jobstatus == "running" or jobstatus == "pending":
					flash(u"URL and its respective Spider is currently queued or running", "danger")

				if jobstatus == "finished":
					print("finished")
					print("Old Job ID is: " , jobid)
					query = "UPDATE spiderjobs SET status = 'finished' WHERE jobid = %s"
					cursor.execute(query, (jobid,))
					conn.commit()
					print("Update Query executed")

					generatedJobid = scrapyd.schedule(PROJECT_NAME, spider, url=url, depth=depth)
					print("New Job ID is: " , generatedJobid)
					query = "INSERT INTO `scfami_spider`.`spiderjobs` \
							(`project`,`spider`,`jobid`,`url`,`depth`,`status`)\
							VALUES (%s,%s,%s,%s, %s, %s);"
					setStatus = "running"
					print(setStatus)
					cursor.execute(query, (PROJECT_NAME, spider, generatedJobid, url, depth, setStatus))
					conn.commit()
					print("Insert Query executed")
					flash(u"URL has been submitted for crawling", "success")

		cursor.close()
		conn.close()

	statuses = requests.get("http://localhost:6800/daemonstatus.json").json()
	runningJobs = 0
	finishedJobs = 0
	for status, value in statuses.items():
		if (status == "running") :
			runningJobs += value
		if (status == "pending"):
			runningJobs += value
		if (status == "finished"):
			finishedJobs += value

	return render_template("/spider/submit_job.html", form=form, runningJobs=runningJobs)


@app.route("/spider/manage_jobs", methods=["GET"], endpoint="spider.manage_jobs")
def spider_managejobs_page():
	conn = mysql.connect()
	cursor = conn.cursor()

	inputTuple_1 = ("project", "spider", "jobid", "url", "depth", "status")

	# if status equal running 
	cursor.execute("SELECT * from spiderjobs WHERE status = 'running'")
	runningDataTuple = cursor.fetchall()
	runningDict = []
	for rows in runningDataTuple:
		resultDictionary = {inputTuple_1[i] : rows[i] for i, _ in enumerate(rows)}
		runningDict.append(resultDictionary)

	print("runningDict: {}".format(runningDict))
	if request.method == "POST":
		print(request.form["filter"])

	# if status equal finished
	cursor.execute("SELECT DISTINCT * from spiderjobs WHERE status = 'finished'")
	finishedDataTuple = cursor.fetchall()
	finishedDict = []
	for rows in finishedDataTuple:
		resultDictionary = {inputTuple_1[i] : rows[i] for i, _ in enumerate(rows)}
		finishedDict.append(resultDictionary)

	print("finishedDict: {}".format(finishedDict))
	cursor.close()
	conn.close()

	return render_template("/spider/manage_jobs.html", finishedDict=finishedDict, runningDict=runningDict)


########## END Spider Pages ##########

@app.route("/help", methods=["GET"], endpoint="help")
def help_page():
	return render_template("/help.html")


########## START Variables ##########

@app.route("/global_var", methods=["GET"])
def global_var():
	return retrieve_glob_var()


@app.route("/arkime_var", methods=["GET"])
def arkime_var():
	return retrieve_arkime_var()


@app.route("/networkcapture_var", methods=["GET"])
def networkcapture_var():
	return retrieve_networkcapture_var()


########## END Variables ##########

if __name__ == "__main__":
	app.run(host=app.config["APP_IP"], port=app.config["APP_PORT"])
