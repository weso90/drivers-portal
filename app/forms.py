from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField, DecimalField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import date, timedelta

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

class AddExpenseForm(FlaskForm):
    """
    Formularz dodawania faktury kosztowej
    """
    driver_id = SelectField('Kierowca', coerce=int, validators=[DataRequired()])
    document_number = StringField('Numer dokumentu', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Za co faktura', validators=[DataRequired(), Length(max=256)])
    issue_date = DateField('Data wystawienia', format='%Y-%m-%d', validators=[DataRequired()])
    net_amount = DecimalField('Kwota netto (PLN)', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    vat_amount = DecimalField('Kwota VAT (PLN)', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    image = FileField('Zdjęcie faktury (opcjonalnie)', validators=[Optional()])
    submit = SubmitField('Dodaj fakturę')

    def validate_issue_date(self, field):
        """
        Walidacja: data wystawienia nie może być starsza niż 30 dni.
        """
        max_past_date = date.today() - timedelta(days=30)
        if field.data < max_past_date:
            raise ValidationError(f'Data wystawienia nie może być starsza niż {max_past_date.strftime("%y-%m-%d")}')
        if field.data > date.today():
            raise ValidationError('Data wystawienia nie może być w przyszłości')