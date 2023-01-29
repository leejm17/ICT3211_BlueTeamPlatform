from flask import Flask, render_template, request

# Global Variables


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
def honeypot_page():
    return render_template("/admin/honeypot.html")


@app.route("/admin/spyder", methods=["GET"], endpoint="spyder")
def spyder_page():
    return render_template("/admin/spyder.html")


@app.route("/admin/pcap_files", methods=["GET"], endpoint="pcap_files")
def pcap_files_page():
    return render_template("/admin/pcap_files.html")


@app.route("/admin/machine_learning", methods=["GET"], endpoint="machine_learning")
def machine_learning_page():
    return render_template("/admin/machine_learning.html")


@app.route("/data_transfer", methods=["GET"], endpoint="data_transfer")
def data_transfer_page():
    return render_template("/data_transfer/data_transfer.html")


@app.route("/data_transfer/t_pot", methods=["GET"], endpoint="data_transfer.t_pot")
def data_transfer_page():
    return render_template("/data_transfer/t_pot.html")


@app.route("/data_transfer/smart_meter", methods=["GET"], endpoint="data_transfer.smart_meter")
def data_transfer_page():
    return render_template("/data_transfer/smart_meter.html")


@app.route("/app_launch", methods=["GET"], endpoint="app_launch")
def app_launch_page():
    return render_template("/app_launch.html")


@app.route("/help", methods=["GET"], endpoint="help")
def help_page():
    return render_template("/help.html")
