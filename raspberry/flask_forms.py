from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class SessionForm(FlaskForm):
    session_name = StringField('New Session Name', validators=[DataRequired()])
    new_gnss = BooleanField('New Gnss File')
    submit = SubmitField('Send')