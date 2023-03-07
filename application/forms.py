from wtforms import Form, SelectField, SelectMultipleField, RadioField, DateField, TimeField, StringField, SubmitField, validators
from wtforms import StringField, SelectField, SubmitField, IntegerField, PasswordField, EmailField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, Regexp, InputRequired
from flask_wtf import FlaskForm

# Import Library for commmunication with scapyd scraper
from scrapyd_api import ScrapydAPI
scrapyd = ScrapydAPI('http://localhost:6800')

class DataTransfer_Form(Form):
	data_source = SelectField("Data Source", choices=["SmartMeterData", "Archive_SmartMeterData", "WiresharkData"])
	meters = SelectMultipleField("Meters", choices=["Meter1", "Meter2", "Meter3", "Meter4", "Meter5", "Meter6", "Meter7"])
	file_type = RadioField("File Type", choices=["CSV", "ZIP"])
	date = DateField("Date")
	start_time = TimeField("Start Time")
	end_time = TimeField("End Time")
	export_name = StringField("Export Name")
	submit = SubmitField("Data Transfer")


def url_check(form, field):
	if "https://github.com/" not in field.data:
		raise ValidationError('A github repository link must be provided')
	
	

class SpyderForm(FlaskForm):
    githubUrl = StringField(label='Github URL 1:', validators=[DataRequired(), url_check])
    submit = SubmitField(label='Submit URL')
    scrapingDepth = SelectField(u'Scraping Depth: ', choices=[('0', '0'), ('1', '1'), ('2', '2')])
    spiderChoice = SelectField(u'Spyder: ', choices=[('github', 'github')])
    

	
