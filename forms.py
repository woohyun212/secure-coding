from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Length, Regexp

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        InputRequired(),
        Length(min=4, max=20),
        Regexp(r'^[a-zA-Z0-9_]+$', message='영문자, 숫자, 밑줄(_)만 가능합니다.')
    ])
    password = PasswordField('Password', validators=[
        InputRequired(),
        Length(min=8, message='8자 이상 입력해야 합니다.')
    ])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class BioForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Length(max=200)])

class ProductForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()])
    price = StringField('Price', validators=[InputRequired()])

class ReportForm(FlaskForm):
    target_id = StringField('Target ID', validators=[InputRequired()])
    reason = TextAreaField('Reason', validators=[InputRequired()])
