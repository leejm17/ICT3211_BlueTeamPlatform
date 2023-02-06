from wtforms import Form, SelectField, SelectMultipleField, RadioField, DateField, TimeField, StringField, SubmitField, validators


class DataTransfer_Form(Form):
	data_source = SelectField("Data Source", choices=["SmartMeterData", "Archive_SmartMeterData", "WiresharkData"])
	meters = SelectMultipleField("Meters", choices=["Meter1", "Meter2", "Meter3", "Meter4", "Meter5", "Meter6", "Meter7"])
	file_type = RadioField("File Type", choices=["CSV", "ZIP"])
	date = DateField("Date")
	start_time = TimeField("Start Time")
	end_time = TimeField("End Time")
	export_name = StringField("Export Name")
	submit = SubmitField("Data Transfer")
