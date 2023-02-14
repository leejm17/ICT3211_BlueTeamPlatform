from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
import os

# Import Other Files
from main import windows_ftp_process
#from main import initiate_ftp, windows_ftp_transfer
from forms import DataTransfer_Form


# Global Variables
load_dotenv()   # Take environment variables from .env
windows_ip = os.getenv("windows_ip")
debian_ip = os.getenv("debian_ip")
ftp_user = os.getenv("ftp_user")
ftp_pw = os.getenv("ftp_pw")


# Create Flask App
app = Flask(__name__)


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
	  

@app.route('/submit', methods = ['POST', 'GET'])
def spyder_submission_detail_page():
        submissions =  request.form
        for k, v in submissions.items():
              print(k, v)
              
        # send POST requests to scrapyd in code below

		# display return values from scrapyd to submissiondetails.html
        return render_template('/spyder/submissiondetails.html', submissions=submissions.values())
