from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.recaptcha.validators import Recaptcha
from wtforms import StringField, TextAreaField, SubmitField, HiddenField, IntegerField, SelectField, PasswordField, BooleanField
from wtforms.fields.html5 import EmailField, IntegerRangeField, IntegerField, TelField
from wtforms.validators import DataRequired, Email, NumberRange, Regexp, URL, Optional, InputRequired, AnyOf, Length


class LoginForm(FlaskForm):
    """Login Form"""
    username = StringField('Username', id='floatingInput', validators=[
        DataRequired(message='Please enter Username!')])
    password = PasswordField('Password', id='floatingPassword', validators=[
        DataRequired(message='Please enter Password!')])
    submit = SubmitField('Sign In')


class UpdateForm(FlaskForm):
    """CSRF only validation"""
    submit = SubmitField('Update')


class WriteTestimonialForm(FlaskForm):
    """Write Testimonial Form"""
    name = StringField('Your Name', validators=[
                       DataRequired(message='Please fill in your name!')])
    role = StringField('[Role name] at [Company name]', validators=[
                       DataRequired(message='Please fill in your role!')])
    text = TextAreaField('Your message', validators=[
        DataRequired(message='Please type your message!')])
    recaptcha = RecaptchaField(
        validators=[Recaptcha(message='Please check the security Recaptcha field!')])
    submit = SubmitField('Submit')


class ContactForm(FlaskForm):
    """Contact Form"""
    name = StringField('Your Name', validators=[
                       DataRequired(message='Please fill in your name!')])
    email = EmailField('Email Address', validators=[
        DataRequired(message='Please fill in your email address!'),
        Email(message='Invalid email address!')])
    subject = StringField('Subject', validators=[
        DataRequired(message='Please type a subject!')])
    message = TextAreaField('Your Message', validators=[
        DataRequired(message='Please type a message!')])
    recaptcha = RecaptchaField(
        validators=[Recaptcha(message='Please check the security Recaptcha field!')])
    submit = SubmitField('Send')


class AddBlogForm(FlaskForm):
    """Add Blog Form"""
    title = StringField('Title', validators=[
        DataRequired(message='Please fill in Title field!')])
    slug = StringField('Slug', validators=[
                       DataRequired(message='Slug is required!')])
    # url_for_sign_s3 = HiddenField(id='url-for-signs3')
    # url_for_delete_s3 = HiddenField(id='url-for-deletes3')
    collection = HiddenField()
    photo_list = HiddenField()
    body = TextAreaField('Text')
    submit = SubmitField('Add')


class EditBlogForm(FlaskForm):
    """Edit Blog Form"""
    title = StringField('Title', validators=[
        DataRequired(message='Please fill in Title field!')])
    slug = StringField('Slug', validators=[
                       DataRequired(message='Slug is required!')])
    body = TextAreaField('Text')
    submit = SubmitField('Update')


class AddProjectForm(FlaskForm):
    """Add Project Form"""
    title = StringField('Title', validators=[
        DataRequired(message='Please fill in Title field!')])
    slug = StringField('Slug', validators=[
                       DataRequired(message='Slug is required!')])
    year = IntegerField('Year', validators=[
        NumberRange(message='Year should be a number!'),
        InputRequired(message='Please enter Year!')])
    tech = StringField('Technologies Used')
    repo = StringField('Source Code (repository URL)', validators=[Optional(),
                       URL(message='Invalid URL for Source Code!')])
    live_url = StringField('Live URL', validators=[Optional(),
                           URL(message='Invalid URL for Live Project!')])
    brief = TextAreaField('Brief', validators=[Length(
        max=100, message='Brief is %(max)d characters max!')])
    description = TextAreaField('Description', id='body')
    featured = BooleanField('Featured')
    # url_for_sign_s3 = HiddenField(id='url-for-signs3')
    # url_for_delete_s3 = HiddenField(id='url-for-deletes3')
    collection = HiddenField()
    photo_list = HiddenField()
    submit = SubmitField('Add')


class EditProjectForm(FlaskForm):
    """Edit Project Form"""
    title = StringField('Title', validators=[
        DataRequired(message='Please fill in Title field!')])
    slug = StringField('Slug', validators=[
                       DataRequired(message='Slug is required!')])
    year = IntegerField('Year', validators=[
        NumberRange(message='Year should be a number!'),
        InputRequired(message='Please enter Year!')])
    tech = StringField('Technologies Used')
    repo = StringField('Source Code (repository URL)', validators=[Optional(),
                       URL(message='Invalid URL for Source Code!')])
    live_url = StringField('Live URL', validators=[Optional(),
                           URL(message='Invalid URL for Live Project!')])
    brief = TextAreaField('Brief', validators=[Length(
        max=100, message='Brief is %(max)d characters max!')])
    description = TextAreaField('Description', id='body')
    featured = BooleanField('Featured')
    submit = SubmitField('Update')


class AddSkillForm(FlaskForm):
    """Add Skill Form"""
    name = StringField('Skill name', validators=[
        DataRequired(message='Please fill in the Skill name!')])
    percentage = IntegerRangeField(
        'Percentage', default=50, validators=[NumberRange(min=0, max=100, message='Percentage should be between 0 and 100!')])
    submit = SubmitField('Add')


class EducationForm(FlaskForm):
    """Education Form (both add and edit)"""
    school = StringField('Institution', validators=[
        DataRequired(message='Please fill in the Institution name!')])
    period = StringField('Period of study', validators=[
        DataRequired(message='Please enter the Period of study!')])
    title = StringField('Title/Award', validators=[
        DataRequired(message='Please fill in the Title/Award!')])
    department = StringField('Department', validators=[
        DataRequired(message='Please fill in the Department!')])
    description = TextAreaField('Description')
    order = IntegerField('Sort Order', validators=[
                         NumberRange(message='Order should be a number!'),
                         InputRequired(message='Please enter Order!')])
    submit = SubmitField('Submit')


class ExperienceForm(FlaskForm):
    """Experience Form (both add and edit)"""
    company = StringField('Company Name', validators=[
        DataRequired(message='Please fill in the Company name!')])
    period = StringField('Period of work', validators=[
        DataRequired(message='Please enter the Period of work!')])
    role = StringField('Role/Title', validators=[
        DataRequired(message='Please fill in youre Role at this company!')])
    description = TextAreaField('Description')
    order = IntegerField('Sort Order', validators=[
                         NumberRange(message='Order should be a number!'),
                         InputRequired(message='Please enter Order!')])
    submit = SubmitField('Submit')


class AddLinkForm(FlaskForm):
    """Add Link Form"""
    name = StringField('Link name', validators=[
        DataRequired(message='Please fill in the Link name!')])
    url = StringField('Live URL', validators=[DataRequired(message='Please fill in the Link URL!'),
                                              URL(message='Invalid URL for Live Project!')])
    icon = StringField('Icon', validators=[
        DataRequired(message='Please fill in the Icon!')])
    submit = SubmitField('Add')


class SettingsForm(FlaskForm):
    """Settings Update Form"""
    name = StringField('Dev Name', validators=[
        DataRequired(message="Please fill in the Developer's name!")])
    title = StringField('Title/Position', validators=[
        DataRequired(message="Please fill in the Developer's title!")])
    bio = TextAreaField('Short Bio')
    cover = TextAreaField('Long Bio')
    status = StringField('Status', validators=[
        DataRequired(message='Please fill in the Status!')])
    availability = SelectField('Availability', choices=[('available', 'Available'), ('not available', 'Not Available')], validators=[
        AnyOf(values=['available', 'not available'], message='Invalid Availability!')])
    email = EmailField('Email Address', validators=[
        DataRequired(message='Please fill in the Email address!'),
        Email(message='Invalid email address!')])
    phone_regex = '^\+((?:9[679]|8[035789]|6[789]|5[90]|42|3[578]|2[1-689])|9[0-58]|8[1246]|6[0-6]|5[1-8]|4[013-9]|3[0-469]|2[70]|7|1)(?:\W*\d){0,13}\d$'
    phone = TelField('Phone Number', validators=[
        DataRequired(message='Please enter the Phone Number!'),
        Regexp(phone_regex, message='Invalid Phone Number')])
    address = StringField('Address', validators=[
        DataRequired(message='Please fill in the Address!')])
    meta_title = StringField('META Title', validators=[
        DataRequired(message='Please fill in the META Title!'),
        Length(max=60, message='META Title is %(max)d characters max!')])
    meta_keys = StringField('META Keywords', validators=[
        DataRequired(message='Please fill in the META Keywords!'),
        Length(max=255, message='META Keywords is %(max)d characters max!')])
    meta_desc = TextAreaField('META Description', validators=[
        DataRequired(message='Please fill in the META Description!'),
        Length(max=160, message='META Description is %(max)d characters max!')])
    submit = SubmitField('Update')
