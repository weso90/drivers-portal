from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class AddDriverForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Hasło', validators=[DataRequired(), Length(min=6)])
    uber_id = StringField('Uber driver ID')
    bolt_id = StringField('Bolt driver ID')
    submit = SubmitField('Dodaj kierowcę')

class DriverLoginForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj')