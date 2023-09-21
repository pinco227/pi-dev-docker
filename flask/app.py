import json
import os
import re
from datetime import date
from functools import wraps

# import boto3
import cloudinary
from cloudinary.uploader import upload
from cloudinary.uploader import destroy
import pydf
import pymongo
import secure
from bson.objectid import ObjectId
from flask import (Flask, Markup, flash, jsonify, make_response, redirect,
                   render_template, request, send_from_directory, session,
                   url_for)
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from html5lib_truncation import truncate_html

from forms import (AddBlogForm, AddLinkForm, AddProjectForm, AddSkillForm,
                   ContactForm, EditBlogForm, EditProjectForm, EducationForm,
                   ExperienceForm, LoginForm, SettingsForm, UpdateForm,
                   WriteTestimonialForm)

if os.path.exists('env.py'):
    import env

# Initialize app
app = Flask(__name__)

# Config app
config = {
    'MONGO_DBNAME': os.environ.get('MONGO_DBNAME'),
    'MONGO_URI': os.environ.get('MONGO_URI'),
    'SECRET_KEY': os.environ.get('SECRET_KEY'),
    'RECAPTCHA_PUBLIC_KEY': os.environ.get('RC_SITE_KEY'),
    'RECAPTCHA_PRIVATE_KEY': os.environ.get('RC_SECRET_KEY'),
    'DB_COLLECTIONS': ["blogs", "testimonials", "links", "settings",
                       "experience", "education", "projects", "skills"],

}
app.config.update(config)

mail_settings = {
    'MAIL_SERVER': 'smtp.sendgrid.net',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': 'apikey',
    'MAIL_PASSWORD': os.environ.get('SENDGRID_API_KEY'),
    'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER')
}
app.config.update(mail_settings)

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_NAME'),
    api_key=os.environ.get('CLOUDINARY_KEY'),
    api_secret=os.environ.get('CLOUDINARY_SECRET')
)

# Initializations / Global vars
Breadcrumbs(app=app)
mongo = PyMongo(app)
mail = Mail(app)
secure_headers = secure.Secure()
settings = mongo.db.settings.find_one(
    {'_id': "1"})


@app.before_request
def check_installed():
    """Checks if collections are created and calls the install function if not

    Returns:
        function: redirects to settings page after installation
    """

    created = mongo.db.list_collection_names()
    if set(created) != (
            set(app.config.get('DB_COLLECTIONS'))
            or not mongo.db.settings.find_one({'_id': "1"})):
        install_app()
        return redirect(url_for('get_settings'))


def install_app():
    """Creates missing database collections and inserts the settings
    document with id 1"""

    # List of existing collections
    created = mongo.db.list_collection_names()

    if set(created) != set(app.config.get('DB_COLLECTIONS')):
        # Iterate through required collections that are not created
        expr = (coll for coll in app.config.get(
            'DB_COLLECTIONS') if coll not in created)
        for coll in expr:
            # Create collection
            try:
                mongo.db.create_collection(name=coll)
            except Exception as e:
                flash(f"{coll} creation error: {e}", "danger")
            else:
                flash(f"{coll} successfully created!", "success")

    # Create empty settings document with id 1
    if not mongo.db.settings.find_one({'_id': "1"}):
        mongo.db.settings.insert_one(
            {'_id': "1",
             'name': "",
             'title': "",
             'bio': "",
             'cover': "",
             'status': "",
             'availability': "",
             'email': "",
             'phone': "",
             'address': "",
             'photos': [],
             'meta_title': "",
             'meta_desc': "",
             'meta_keys': ""})
        flash("Settings document created!")


@app.after_request
def set_secure_headers(response):
    """Sets Secure HTTP Headers"""

    secure_headers.framework.flask(response)
    return response


@app.context_processor
def context_processor():
    """Inject settings and links variables to all templates

    Returns:
        dict: settings and links db collections
    """

    global settings
    settings = mongo.db.settings.find_one({'_id': "1"})

    links = list(mongo.db.links.find())
    return dict(settings=settings, links=links)


@app.errorhandler(404)
def page_not_found(e):
    """Error handler for error 404 NOT FOUND

    Args:
        e (obj): error obj

    Returns:
        function: redirect to home or dashboard
    """

    flash('Page not found!', 'danger')
    if request.path.split('/')[1] == 'admin':
        return redirect(url_for('admin'))

    return redirect(url_for('home'))


@app.route('/browserconfig.xml')
def sendfile():
    """Route to access browserconfig.xml file from static folder"""

    return send_from_directory('static', 'browserconfig.xml')


@app.route('/cv')
def get_cv():
    """Route that generates pdf file from html jinja template"""

    root = request.url_root
    jobs = list(mongo.db.experience.find().sort('order', 1))
    schools = list(mongo.db.education.find().sort('order', 1))
    skills = list(mongo.db.skills.find().sort('percentage', -1))
    projects = list(mongo.db.projects.aggregate(
        [
            {"$project": {
                "title": 1,
                "year": 1,
                "tech": 1,
                "brief": 1,
                "repo": 1,
                "live_url": 1,
                "photos": 1,
                "featured": 1,
                "tech_length": {"$strLenCP": "$tech"}
            }},
            {"$sort": {
                "featured": -1,
                "year": -1,
                "tech_length": -1
            }},
            {'$limit': 5},
            {"$project": {"tech_length": 0}}
        ]
    ))
    testimonials = list(mongo.db.testimonials.find(
        {'approved': True}).limit(5))
    html = render_template('cv.html', jobs=jobs, schools=schools,
                           skills=skills, projects=projects,
                           testimonials=testimonials, root=root)
    filename = settings['name'].replace(' ', '-').lower()
    pdf = pydf.generate_pdf(html, page_size='A4', margin_bottom='0.75in',
                            margin_top='0.75in', margin_left='0.5in',
                            margin_right='0.5in', image_dpi='300')
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=' + \
        filename+'.pdf'

    return response


@app.route('/')
@app.route('/home')
@register_breadcrumb(app, '.', 'Home')
def home():
    """Landing page route"""

    skills = list(mongo.db.skills.find().sort(
        [('percentage', pymongo.DESCENDING), ('name', pymongo.ASCENDING)]))
    education = list(mongo.db.education.find().sort('order', 1))
    experience = list(mongo.db.experience.find().sort('order', 1))
    testimonials = list(mongo.db.testimonials.find({'approved': True}))

    return render_template('landing.html', skills=skills, education=education,
                           experience=experience, testimonials=testimonials)


@app.route('/write-testimonial', methods=['GET', 'POST'])
@register_breadcrumb(app, '.write-testimonial', 'Write Testimonial')
def add_testimonial():
    """Write testimonial page route"""

    form = WriteTestimonialForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            testimonial = {
                'author': form.name.data,
                'role': form.role.data,
                'text': form.text.data,
                'approved': False
            }
            mongo.db.testimonials.insert_one(testimonial)
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('home'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    return render_template('write-testimonial.html', form=form)


@app.route('/portfolio')
@register_breadcrumb(app, '.portfolio', 'Portfolio')
def portfolio():
    """Portfolio page route"""

    projects = list(mongo.db.projects.aggregate(
        [
            {"$project": {
                "title": 1,
                "slug": 1,
                "year": 1,
                "tech": 1,
                "brief": 1,
                "repo": 1,
                "live_url": 1,
                "photos": 1,
                "featured": 1,
                "tech_length": {"$strLenCP": "$tech"}
            }},
            {"$sort": {
                "featured": -1,
                "year": -1,
                "tech_length": -1
            }},
            {"$project": {"tech_length": 0}}
        ]
    ))

    return render_template('portfolio.html', projects=projects)


def view_project_dlc(*args, **kwargs):
    """Get project details from requested url args"""

    slug = request.view_args['project']
    project = mongo.db.projects.find_one({'slug': slug})

    if project and project['title']:
        return [{'text': project['title']}]
    else:
        return [{'text': 'Not found'}]


@app.route('/portfolio/<project>')
@register_breadcrumb(app, '.portfolio.project', '',
                     dynamic_list_constructor=view_project_dlc)
def get_project(project):
    """Project page route"""

    project = mongo.db.projects.find_one({'slug': project})

    return render_template('project.html', project=project)


@app.route('/blog')
@register_breadcrumb(app, '.blog', 'Blog')
def blog():
    """Blogs page route"""

    blogs = list(mongo.db.blogs.find())

    for i, blog in enumerate(blogs):
        blog['body'] = truncate_html(
            blog['body'], 200, end=' ...', break_words=True)
        blogs[i] = blog

    return render_template('blog.html', blogs=blogs)


def view_blog_dlc(*args, **kwargs):
    """Get blog post details from requested url args

    Returns:
        dict: text to be displayed into breadcrumb (Blog title)
    """

    slug = request.view_args['post']
    post = mongo.db.blogs.find_one({'slug': slug})

    if post and post['title']:
        return [{'text': post['title']}]
    else:
        return [{'text': 'Not found'}]


@app.route('/blog/<post>')
@register_breadcrumb(app, '.blog.post', '',
                     dynamic_list_constructor=view_blog_dlc)
def get_post(post):
    """Blog post page route"""

    post = mongo.db.blogs.find_one({'slug': post})

    return render_template('blog-post.html', post=post)


@app.route('/contact', methods=['GET', 'POST'])
@register_breadcrumb(app, '.contact', 'Contact')
def contact():
    """Conact page route"""

    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            msg = Message(subject='[Dev.PI] ' + form.subject.data,
                          recipients=[app.config.get('MAIL_DEFAULT_SENDER')],
                          reply_to=form.email.data)
            msg.body = (form.name.data +
                        '(' + form.email.data + '): ' + form.message.data)
            msg.html = (render_template(
                'mail.html', subject=form.subject.data, name=form.name.data,
                message=form.message.data))
            try:
                mail.send(msg)
            except Exception:
                flash(
                    'Error sending email!', 'danger')
            else:
                flash(
                    'Thank you for your message! I will get back to you \
                        shortly.',
                    'success')
            return redirect(url_for('contact'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    return render_template('contact.html', form=form)


# ADMIN PANEL
def login_required(flash_message=False):
    """Function decorator to check for login

    Args:
        flash_message (bool, optional): Message to be sent via Flash. If left
        empty then no message is sent. Defaults to False.
    """

    def inner_function(f):
        """Wrapper function in order to get argument into decorator

        Args:
            f (function): Decorated function

        Returns:
            function: Function after being decorated
        """

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user'):
                flash(flash_message, 'danger') if flash_message else None
                return redirect(url_for('login', path=request.path))
            else:
                return f(*args, **kwargs)

        return decorated_function

    return inner_function


@app.route('/admin/upload_photo', methods=['POST'])
@login_required()
def upload_photo():
    upload_result = None

    file_to_upload = request.files['file']

    if file_to_upload:
        try:
            upload_result = upload(file_to_upload,
                                   folder="dev-pi/")

        except Exception:
            return make_response(
                jsonify({
                    'message': 'Error uploading file',
                    'result': upload_result}), 500)
        else:
            return make_response(
                jsonify({
                    'message': 'Photo was successfully added to database',
                    'data': upload_result}), 200)
    else:
        return make_response(jsonify({'message': 'Bad request'}), 400)


@app.route('/admin/save_photo', methods=["PUT"])
@login_required()
def save_photo():
    """Route to be called (API call with PUT method) for adding photo to
    database"""

    collection = request.form.get('coll')
    document_id = request.form.get('docid')
    photo = json.loads(request.form.get('photo_data'))

    if collection == "settings":
        id = "1"
    else:
        id = ObjectId(document_id)

    try:
        mongo.db[collection].update_one(
            {'_id': id},
            {'$push': {'photos': photo}}
        )
    except Exception:
        return make_response(
            jsonify({'message': 'Error updating database'}), 500)
    else:
        return make_response(
            jsonify({'message': 'Photo was successfully added to database'}),
            200)


@app.route('/admin/delete_from_cloud')
@login_required()
def delete_from_cloud(file_id=None):
    """Route to be called (API call) for removing photo from database"""

    if not file_id:
        file_id = request.args.get('file_id')

    if file_id:
        try:
            destroy_result = destroy(file_id)

        except Exception:
            return make_response(
                jsonify({
                    'message': 'Error uploading file',
                    'result': destroy_result}), 500)
        else:
            return make_response(
                jsonify({
                    'message': 'Photo was successfully added to database',
                    'result': destroy_result}), 200)
    else:
        return make_response(jsonify({'message': 'Bad request'}), 400)


@app.route('/admin/delete_photo')
@login_required()
def delete_photo():
    """Route to be called (API call) for removing photo from database"""

    collection = request.args.get('coll')
    document_id = request.args.get('docid')
    file_id = request.args.get('file_id')

    if collection == "settings":
        id = "1"
    else:
        id = ObjectId(document_id)

    try:
        mongo.db[collection].update_one(
            {'_id': id},
            {'$pull': {'photos': {'public_id': file_id}}}
        )
    except Exception:
        return make_response(
            jsonify({'message': 'Error updating database'}), 500)
    else:
        return make_response(
            jsonify({
                'message': 'Photo was successfully removed from database'
            }), 200)


# @app.route('/admin/sign_s3')
# @login_required()
# def sign_s3():
#     """Route to be called (API call) for getting a signed S3 post"""

#     S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
#     file_name = request.args.get('file_name')
#     file_type = request.args.get('file_type')
#     s3 = boto3.client('s3')

#     presigned_post = s3.generate_presigned_post(
#         Bucket=S3_BUCKET,
#         Key=file_name,
#         Fields={"acl": "public-read", "Content-Type": file_type},
#         Conditions=[
#             {"acl": "public-read"},
#             {"Content-Type": file_type}
#         ],
#         ExpiresIn=3600
#     )

#     return json.dumps({
#         'data': presigned_post,
#         'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)
#     })


# def s3_delete_call(file_name):
#     """Function to delete file from S3

#     Args:
#         file_name (string): Name of file to be deleted

#     Returns:
#         obj: Response in json format
#     """

#     S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
#     s3 = boto3.client('s3')

#     response = s3.delete_object(
#         Bucket=S3_BUCKET,
#         Key=file_name
#     )

#     return json.dumps({
#         'data': response
#     })


# @app.route('/admin/delete_s3')
# @login_required()
# def delete_s3():
#     """Route to be called (API call) for deleting photo from S3"""

#     file_name = request.args.get('file_name')

#     return s3_delete_call(file_name)


@app.route('/admin/')
@app.route('/admin')
@login_required()
def admin():
    """ADMIN Dashboard page route"""

    testimonials = mongo.db.testimonials.count_documents({})
    blogs = mongo.db.blogs.count_documents({})
    projects = mongo.db.projects.count_documents({})
    skills = mongo.db.skills.count_documents({})
    education = mongo.db.education.count_documents({})
    experience = mongo.db.experience.count_documents({})
    unapproved_testimonials = mongo.db.testimonials.count_documents({
                                                                    'approved':
                                                                        False})

    return render_template('admin/dashboard.html', blogs=blogs,
                           projects=projects, skills=skills,
                           education=education, experience=experience,
                           testimonials=testimonials,
                           unapproved_testimonials=unapproved_testimonials)


@app.route('/admin/testimonials', methods=['GET', 'POST'])
@login_required("You don't have the user privileges to access this section.")
def get_testimonials():
    """ADMIN Testimonials page route"""

    form = UpdateForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            testimonials = list(mongo.db.testimonials.find())

            for testimonial in testimonials:
                if request.form.get(f"approved[{testimonial['_id']}]"):
                    is_approved = True
                else:
                    is_approved = False
                mongo.db.testimonials.update_one(
                    {'_id': ObjectId(testimonial['_id'])},
                    {'$set': {'approved': is_approved}})
            flash('Testimonials were successfully updated!', 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_testimonials'))
        else:
            flash('Error submitting the changes!', 'danger')

    approved = list(mongo.db.testimonials.find({'approved': True}))
    unapproved = list(mongo.db.testimonials.find({'approved': False}))

    return render_template('admin/testimonials.html', approved=approved,
                           unapproved=unapproved, form=form)


@app.route('/admin/delete_testimonial/<id>')
@login_required("You don't have the user privileges to access this section.")
def delete_testimonial(id):
    """ADMIN Delete testimonial page route"""

    mongo.db.testimonials.delete_one({'_id': ObjectId(id)})
    flash('Testimonial was successfully deleted', 'warning')

    return redirect(url_for('get_testimonials'))


@app.route('/admin/blogs')
@login_required("You don't have the user privileges to access this section.")
def get_blogs():
    """ADMIN Blogs page route"""

    blogs = list(mongo.db.blogs.find())

    for i, blog in enumerate(blogs):
        blog['body'] = truncate_html(
            blog['body'], 200, end=' [...] ', break_words=True)
        blogs[i] = blog

    return render_template('admin/blogs.html', blogs=blogs)


@app.route('/admin/add_blog', methods=['GET', 'POST'])
@login_required("You don't have the user privileges to access this section.")
def add_blog():
    """ADMIN Add Blog page route"""

    form = AddBlogForm()

    if request.method == 'POST':
        slug_exists = mongo.db.blogs.find_one({'slug': form.slug.data})
        if form.validate_on_submit() and not slug_exists:
            photos = json.loads(f"[{form.photo_list.data}]")
            blog = {
                'title': form.title.data,
                'slug': form.slug.data,
                'photos': photos,
                'body': form.body.data,
                'added_on': date.today().strftime('%B %d, %Y')
            }
            mongo.db.blogs.insert_one(blog)
            flash(Markup(
                f"Blog <strong>{blog['title']}</strong> was successfully \
                    Added!"), 'success')

            return redirect(url_for('get_blogs'))
        else:
            if slug_exists:
                flash('This title/slug already exists!', 'danger')

            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    return render_template('admin/add_blog.html', form=form)


@ app.route('/admin/edit_blog/<id>', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def edit_blog(id):
    """ADMIN Edit Blog page route"""

    form = EditBlogForm()
    if ObjectId.is_valid(id):
        post = mongo.db.blogs.find_one({'_id': ObjectId(id)})
    else:
        post = None

    if request.method == 'POST':
        if form.validate_on_submit():
            updated = {
                'title': form.title.data,
                'slug': form.slug.data,
                'body': form.body.data
            }
            flash(Markup(
                f"Blog <strong>{updated['title']}</strong> was successfully \
                    edited!"), 'success')

            mongo.db.blogs.update_one({'_id': ObjectId(id)}, {
                '$set': updated})

            # Redirect to avoid re-submission
            return redirect(url_for('get_blogs'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    form.body.data = post.get('body') if post else ""

    return render_template('admin/edit_blog.html', post=post, form=form)


@ app.route('/admin/delete_blog/<id>')
@ login_required("You don't have the user privileges to access this section.")
def delete_blog(id):
    """ADMIN Delete Blog page route"""

    post = mongo.db.blogs.find_one({'_id': ObjectId(id)})

    for photo in post['photos']:
        if 'public_id' in photo:
            file_id = photo['public_id']
            try:
                delete_from_cloud(file_id)
            except Exception:
                flash(f"Photo {file_id} couldn't be deleted from server!")
            else:
                flash(f"Photo {file_id} was successfully deleted from server!")

    mongo.db.blogs.delete_one({'_id': ObjectId(id)})
    flash('Blog was successfully deleted', 'warning')

    return redirect(url_for('get_blogs'))


@ app.route('/admin/skills', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def get_skills():
    """ADMIN Skills page route"""

    skills = list(mongo.db.skills.find())
    form = UpdateForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            for skill in skills:
                updated = {
                    'name': request.form.get(f"name[{skill['_id']}]"),
                    'percentage': int(
                        request.form.get(f"percentage[{skill['_id']}]"))
                }
                mongo.db.skills.update_one({'_id': ObjectId(skill['_id'])}, {
                    '$set': updated})

            flash('Skills were successfully updated!', 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_skills'))
        else:
            flash('Error submitting the changes!', 'danger')

    return render_template('admin/skills.html', skills=skills, form=form)


@ app.route('/admin/delete_skill/<id>')
@ login_required("You don't have the user privileges to access this section.")
def delete_skill(id):
    """ADMIN Delete Skill page route"""

    mongo.db.skills.delete_one({'_id': ObjectId(id)})
    flash('Skill was successfully deleted', 'warning')

    return redirect(url_for('get_skills'))


@ app.route('/admin/add_skill', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def add_skill():
    """ADMIN Add Skill page route"""

    form = AddSkillForm()

    if request.method == 'POST':
        skill_exists = mongo.db.skills.find_one({'name': form.name.data})
        if form.validate_on_submit() and not skill_exists:
            skill = {
                'name': form.name.data,
                'percentage': int(form.percentage.data)
            }
            mongo.db.skills.insert_one(skill)
            flash(Markup(
                f"Skill <strong>{skill['name']}</strong> was successfully \
                    Added!"), 'success')

            return redirect(url_for('get_skills'))
        else:
            if skill_exists:
                flash('This skill already exists!', 'danger')
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    return render_template('admin/add_skill.html', form=form)


@ app.route('/admin/education', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def get_education():
    """ADMIN Education page route"""

    education = list(mongo.db.education.find().sort('order', 1))
    form = UpdateForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            for school in education:
                order = request.form.get(f"order[{school['_id']}]")
                if order and (isinstance(order, int) or order.isdigit()):
                    mongo.db.education.update_one({'_id': ObjectId(school['_id'])},
                                                  {'$set': {'order': int(order)}})
                else:
                    flash(Markup(
                        f"School <strong>{school['school']}</strong>: Invalid \
                            Order!"), 'danger')

            flash('Education successfully updated!', 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_education'))
        else:
            flash('Error submitting the changes!', 'danger')

    return render_template('admin/education.html', education=education,
                           form=form)


@ app.route('/admin/add_education', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def add_education():
    """ADMIN Add Education page route"""

    form = EducationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            school = {
                'school': form.school.data,
                'period': form.period.data,
                'title': form.title.data,
                'department': form.department.data,
                'description': form.description.data,
                'order': int(form.order.data)
            }
            mongo.db.education.insert_one(school)
            flash(Markup(
                f"School <strong>{school['school']}</strong> was successfully \
                    Added!"), 'success')

            return redirect(url_for('get_education'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    if mongo.db.education.find_one(sort=[('order', pymongo.DESCENDING)]):
        form.order.data = str(
            mongo.db.education.find_one(
                sort=[('order', pymongo.DESCENDING)])['order'] + 1)
    form.submit.label.text = 'Add'

    return render_template('admin/add_education.html', form=form)


@ app.route('/admin/edit_education/<id>', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def edit_education(id):
    """ADMIN Edit Education page route"""

    form = EducationForm()
    if ObjectId.is_valid(id):
        school = mongo.db.education.find_one({'_id': ObjectId(id)})
    else:
        school = None

    if request.method == 'POST':
        if form.validate_on_submit():
            updated = {
                'school': form.school.data,
                'period': form.period.data,
                'title': form.title.data,
                'department': form.department.data,
                'description': form.description.data,
                'order': int(form.order.data)
            }
            mongo.db.education.update_one({'_id': ObjectId(id)},
                                          {'$set': updated})
            flash(Markup(
                f"School <strong>{updated['school']}</strong> was successfully \
                    edited!"), 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_education'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    form.description.data = school.get('description') if school else ""
    form.submit.label.text = 'Edit'

    return render_template('admin/edit_education.html', school=school,
                           form=form)


@ app.route('/admin/delete_education/<id>')
@ login_required("You don't have the user privileges to access this section.")
def delete_education(id):
    """ADMIN Delete Education page route"""

    mongo.db.education.delete_one({'_id': ObjectId(id)})
    flash('School was successfully deleted')

    return redirect(url_for('get_education'))


@ app.route('/admin/experience', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def get_experience():
    """ADMIN Experience page route"""

    experience = list(mongo.db.experience.find().sort('order', 1))
    form = UpdateForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            for job in experience:
                order = request.form.get(f"order[{job['_id']}]")
                if order and (isinstance(order, int) or order.isdigit()):
                    mongo.db.experience.update_one({'_id': ObjectId(job['_id'])}, {
                        '$set': {'order': int(order)}})
                else:
                    flash(Markup(
                        f"Job at <strong>{job['company']}</strong>: Invalid \
                            Order"), 'danger')

            flash('Work Experience successfully updated!', 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_experience'))
        else:
            flash('Error submitting the changes!', 'danger')

    return render_template('admin/experience.html', experience=experience,
                           form=form)


@ app.route('/admin/add_experience', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def add_experience():
    """ADMIN Add Experience page route"""

    form = ExperienceForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            job = {
                'company': form.company.data,
                'period': form.period.data,
                'role': form.role.data,
                'description': form.description.data,
                'order': int(form.order.data)
            }
            mongo.db.experience.insert_one(job)
            flash(Markup(
                f"Job at <strong>{job['company']}</strong> was successfully \
                    Added!"), 'success')

            return redirect(url_for('get_experience'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    if mongo.db.experience.find_one(sort=[('order', pymongo.DESCENDING)]):
        form.order.data = str(
            mongo.db.experience.find_one(
                sort=[('order', pymongo.DESCENDING)])['order'] + 1)
    form.submit.label.text = 'Add'

    return render_template('admin/add_experience.html', form=form)


@ app.route('/admin/edit_experience/<id>', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def edit_experience(id):
    """ADMIN Edit Experience page route"""

    form = ExperienceForm()
    if ObjectId.is_valid(id):
        job = mongo.db.experience.find_one({'_id': ObjectId(id)})
    else:
        job = None

    if request.method == 'POST':
        if form.validate_on_submit():
            updated = {
                'company': form.company.data,
                'period': form.period.data,
                'role': form.role.data,
                'description': form.description.data,
                'order': int(form.order.data)
            }
            mongo.db.experience.update_one({'_id': ObjectId(id)}, {
                '$set': updated})
            flash(Markup(
                f"Job at <strong>{updated['company']}</strong> was \
                    successfully edited!"), 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_experience'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    form.description.data = job.get('description') if job else ""
    form.submit.label.text = 'Edit'

    return render_template('admin/edit_experience.html', job=job, form=form)


@ app.route('/admin/delete_experience/<id>')
@ login_required("You don't have the user privileges to access this section.")
def delete_experience(id):
    """ADMIN Delete Experience page route"""

    mongo.db.experience.delete_one({'_id': ObjectId(id)})
    flash('Job was successfully deleted')

    return redirect(url_for('get_experience'))


@ app.route('/admin/projects')
@ login_required("You don't have the user privileges to access this section.")
def get_projects():
    """ADMIN Projects page route"""

    projects = list(mongo.db.projects.aggregate(
        [
            {"$project": {
                "title": 1,
                "slug": 1,
                "year": 1,
                "tech": 1,
                "brief": 1,
                "repo": 1,
                "live_url": 1,
                "photos": 1,
                "featured": 1,
                "tech_length": {"$strLenCP": "$tech"}
            }},
            {"$sort": {
                "featured": -1,
                "year": -1,
                "tech_length": -1
            }},
            {"$project": {"tech_length": 0}}
        ]
    ))

    return render_template('admin/projects.html', projects=projects)


@ app.route('/admin/add_project', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def add_project():
    """ADMIN Add Project page route"""

    form = AddProjectForm()

    if request.method == 'POST':
        slug_exists = mongo.db.projects.find_one({'slug': form.slug.data})
        if form.validate_on_submit() and not slug_exists:
            photos = json.loads(f"[{form.photo_list.data}]")
            project = {
                'title': form.title.data,
                'slug': form.slug.data,
                'year': form.year.data,
                'tech': form.tech.data,
                'brief': form.brief.data,
                'description': form.description.data,
                'repo': form.repo.data,
                'live_url': form.live_url.data,
                'photos': photos,
                'featured': form.featured.data
            }
            mongo.db.projects.insert_one(project)
            flash(Markup(
                f"Project <strong>{project['title']}</strong> was \
                    successfully Added!"), 'success')

            return redirect(url_for('get_projects'))
        else:
            if slug_exists:
                flash('This title/slug already exists!', 'danger')
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    return render_template('admin/add_project.html', form=form)


@ app.route('/admin/edit_project/<id>', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def edit_project(id):
    """ADMIN Edit Project page route"""

    form = EditProjectForm()
    if ObjectId.is_valid(id):
        project = mongo.db.projects.find_one({'_id': ObjectId(id)})
    else:
        project = None

    if request.method == 'POST':
        if form.validate_on_submit():
            updated = {
                'title': form.title.data,
                'slug': form.slug.data,
                'year': form.year.data,
                'tech': form.tech.data,
                'brief': form.brief.data,
                'description': form.description.data,
                'repo': form.repo.data,
                'live_url': form.live_url.data,
                'featured': form.featured.data
            }
            mongo.db.projects.update_one({'_id': ObjectId(id)}, {
                '$set': updated})
            flash(Markup(
                f"Project <strong>{updated['title']}</strong> was \
                    successfully edited!"), 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_projects'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    if project:
        form.description.data = project.get('description')
        form.brief.data = project.get('brief')
        form.featured.data = project.get('featured')

    return render_template('admin/edit_project.html', project=project,
                           form=form)


@ app.route('/admin/delete_project/<id>')
@ login_required("You don't have the user privileges to access this section.")
def delete_project(id):
    """ADMIN Delete Project page route"""

    project = mongo.db.projects.find_one({'_id': ObjectId(id)})

    for photo in project['photos']:
        if 'public_id' in photo:
            file_id = photo['public_id']
            try:
                delete_from_cloud(file_id)
            except Exception:
                flash(f"Photo {file_id} couldn't be deleted from server!")
            else:
                flash(f"Photo {file_id} was successfully deleted from server!")

    mongo.db.projects.delete_one({'_id': ObjectId(id)})
    flash('Project was successfully deleted', 'warning')

    return redirect(url_for('get_projects'))


@ app.route('/admin/links', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def get_links():
    """ADMIN Links page route"""

    links = list(mongo.db.links.find())
    form = UpdateForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            for link in links:
                name = request.form.get(f"name[{link['_id']}]")
                icon = request.form.get(f"icon[{link['_id']}]")
                url = request.form.get(f"url[{link['_id']}]")
                url_regex = (
                    r'^[a-z]+://'
                    r'(?P<host>[^\/\?:]+)'
                    r'(?P<port>:[0-9]+)?'
                    r'(?P<path>\/.*?)?'
                    r'(?P<query>\?.*)?$'
                )
                if name and icon and url and re.search(url_regex, url):
                    updated = {
                        'name': name,
                        'icon': icon,
                        'url': url
                    }
                    mongo.db.links.update_one({'_id': ObjectId(link['_id'])}, {
                        '$set': updated})
                else:
                    if not name:
                        flash(Markup(
                            f"Link <strong>{link['name']}</strong>: Name \
                                required"), 'danger')
                    if not icon:
                        flash(Markup(
                            f"Link <strong>{link['name']}</strong>: Icon \
                                required"), 'danger')
                    if not url:
                        flash(Markup(
                            f"Link <strong>{link['name']}</strong>: URL \
                                required"), 'danger')
                    if not re.search(url_regex, url):
                        flash(Markup(
                            f"Link <strong>{link['name']}</strong>: Invalid \
                                RL"), 'danger')

            flash('Links were successfully updated!', 'success')

            # Redirect to avoid re-submission
            return redirect(url_for('get_links'))
        else:
            flash('Error submitting the changes!', 'danger')

    return render_template('admin/links.html', links=links, form=form)


@ app.route('/admin/delete_link/<id>')
@ login_required("You don't have the user privileges to access this section.")
def delete_link(id):
    """ADMIN Delete Link page route"""

    mongo.db.links.delete_one({'_id': ObjectId(id)})
    flash('Link was successfully deleted', 'warning')

    return redirect(url_for('get_links'))


@ app.route('/admin/add_link', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def add_link():
    """ADMIN Add Link page route"""

    form = AddLinkForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            link = {
                'name': form.name.data,
                'icon': form.icon.data,
                'url': form.url.data
            }
            mongo.db.links.insert_one(link)
            flash(Markup(
                f"Link <strong>{link['name']}</strong> was successfully \
                    Added!"), 'success')

            return redirect(url_for('get_links'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    return render_template('admin/add_link.html', form=form)


@ app.route('/admin/settings', methods=['GET', 'POST'])
@ login_required("You don't have the user privileges to access this section.")
def get_settings():
    """ADMIN Settins page route"""

    form = SettingsForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            updated = {
                'name': form.name.data,
                'title': form.title.data,
                'bio': form.bio.data,
                'cover': form.cover.data,
                'status': form.status.data,
                'availability': form.availability.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'address': form.address.data,
                'meta_title': form.meta_title.data,
                'meta_desc': form.meta_desc.data,
                'meta_keys': form.meta_keys.data
            }
            mongo.db.settings.update_one({'_id': "1"}, {
                '$set': updated})
            flash('Settings were successfully updated!', 'success')

            global settings
            settings = mongo.db.settings.find_one({'_id': "1"})

            # Redirect to avoid re-submission
            return redirect(url_for('get_settings'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    form.bio.data = settings.get('bio')
    form.cover.data = settings.get('cover')
    form.availability.data = settings.get('availability')
    form.meta_desc.data = settings.get('meta_desc')

    return render_template('admin/settings.html', form=form)


@ app.route('/admin/login', defaults={'path': None}, methods=['GET', 'POST'])
@ app.route('/<path:path>/login', methods=['GET', 'POST'])
def login(path):
    """ADMIN Login page route"""

    form = LoginForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if (form.username.data.lower() == os.environ.get(
                'ADMIN_USERNAME').lower() and
                    form.password.data == os.environ.get('ADMIN_PASSWORD')):
                session['user'] = form.username.data.lower()
                flash(f"Welcome, {form.username.data}")

                if path:
                    return redirect("/"+path)
                else:
                    return redirect(url_for('admin'))
            else:
                # username doesn't exist
                flash('Incorrect Username or Password!', 'danger')

                return redirect(url_for('login'))
        else:
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(err, 'danger')

    return render_template('admin/login.html', form=form)


@ app.route('/admin/logout')
def logout():
    """ADMIN Logout page route"""

    if session.get('user'):
        session.pop('user')

    flash('You have been logged out', 'danger')

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)
