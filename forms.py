from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, IntegerField
from wtforms.validators import InputRequired, Length, Regexp, DataRequired, EqualTo, NumberRange
from flask_wtf.file import FileField, FileAllowed

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

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[
        InputRequired(),
        Length(min=4, max=20),
        Regexp(r'^[a-zA-Z0-9_]+$', message='영문자, 숫자, 밑줄(_)만 가능합니다.')
    ])
    password = PasswordField('Password', validators=[
        # InputRequired(),
        Length(min=8, message='8자 이상 입력해야 합니다.')
    ])
    bio = TextAreaField('Bio', validators=[Length(max=200)])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class BioForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Length(max=200)])

class ProductForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()])
    price = DecimalField('Price', validators=[InputRequired(), NumberRange(min=0, message='가격은 0 이상의 숫자여야 합니다.')])
    image = FileField('상품 이미지', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '이미지 파일(jpg, jpeg, png, gif)만 업로드할 수 있습니다.')
    ])

class ReportForm(FlaskForm):
    target_id = StringField('Target ID', validators=[InputRequired()])
    reason = TextAreaField('Reason', validators=[InputRequired()])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('현재 비밀번호', validators=[DataRequired()])
    new_password = PasswordField(
        '새 비밀번호',
        validators=[
            DataRequired(),
            EqualTo('confirm_new_password', message='비밀번호가 일치하지 않습니다.')
        ]
    )
    confirm_new_password = PasswordField('비밀번호 확인', validators=[DataRequired()])

class TransferForm(FlaskForm):
    recipient_id = StringField('수신인 ID', render_kw={"placeholder": "UUID 입력"}, validators=[
        InputRequired(),
        Length(min=36, max=36, message='유효한 사용자 ID를 입력하세요.')
    ])
    amount = IntegerField('금액', render_kw={"placeholder": "금액 입력"}, validators=[
        InputRequired(),
        NumberRange(min=1, message='송금액은 1원 이상이어야 합니다.')
    ])


# 포인트 충전 요청 폼
class DepositRequestForm(FlaskForm):
    amount = IntegerField(
        '충전 요청 금액(원)',
        render_kw={"placeholder": "충전할 금액을 입력하세요"},
        validators=[
            InputRequired(message='충전할 금액을 입력해주세요.'),
            NumberRange(min=1, message='충전 금액은 1원 이상이어야 합니다.')
        ]
    )
