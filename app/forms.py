from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Length

##########################
###   FORMULARZE ADMIN I DRIVER
##########################

class AddDriverForm(FlaskForm):
    """
    Formularz dodawania nowego kierowcy przez administratora
    """
    username = StringField('Nazwa użytkownika', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Hasło', validators=[DataRequired(), Length(min=6)])
    uber_id = StringField('Uber driver ID')
    bolt_id = StringField('Bolt driver ID')
    submit = SubmitField('Dodaj kierowcę')

class DriverLoginForm(FlaskForm):
    """
    Formularz logowania - dla admina i kierowcy
    """
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj')

class CSVUploadForm(FlaskForm):
    """
    Formularz uploadu pliku CSV z zarobkami kierowców - bolt
    """
    file = FileField("Plik CSV", validators=[DataRequired()])
    submit = SubmitField("Wyślij")