from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import secrets
import os
import qrcode

import cloudinary
import cloudinary.uploader

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config['SECRET_KEY'] = secrets.token_hex(16)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db')

db = SQLAlchemy(app)

# CLOUDINARY

cloudinary.config(
    cloud_name="dzmnbpnlc",
    api_key="258492314228418",
    api_secret="yYX8OnKBIYBBB3Xz2dLtUc18DGw",
    secure=True
)

# USER

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(300))

# PROJECT

class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    slug = db.Column(db.String(200), unique=True)

    title = db.Column(db.String(300))

    person_name = db.Column(db.String(200))

    caption = db.Column(db.Text)

    event_date = db.Column(db.String(100))

    theme = db.Column(db.String(100))

    image = db.Column(db.Text)

    music = db.Column(db.String(500))

# HOME

@app.route('/')
def home():

    if 'user_id' in session:

        projects = Project.query.filter_by(
            user_id=session['user_id']
        ).all()

    else:

        projects = []

    return render_template(
        'index.html',
        projects=projects
    )

# REGISTER

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        existing = User.query.filter_by(
            username=username
        ).first()

        if existing:

            return "Username already exists"

        user = User(

            username=username,

            password=generate_password_hash(password)

        )

        db.session.add(user)

        db.session.commit()

        session['user_id'] = user.id

        return redirect('/')

    return render_template('register.html')

# LOGIN

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id

            return redirect('/')

        return "Wrong username or password"

    return render_template('login.html')

# DASHBOARD

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:

        return redirect('/login')

    projects = Project.query.filter_by(
        user_id=session['user_id']
    ).all()

    return render_template(
        'dashboard.html',
        projects=projects
    )

# CREATE

@app.route('/create', methods=['GET', 'POST'])
def create():

    if 'user_id' not in session:

        return redirect('/login')

    if request.method == 'POST':

        slug = secrets.token_hex(5)

        images = request.files.getlist('images')

        music = request.files['music']

        # MUSIC

        music_upload = cloudinary.uploader.upload(
            music,
            resource_type="video"
        )

        music_url = music_upload['secure_url']

        # IMAGES

        image_urls = []

        for image in images:

            if image.filename != "":

                upload = cloudinary.uploader.upload(image)

                image_urls.append(
                    upload['secure_url']
                )

        # SAVE PROJECT

        project = Project(

            user_id=session['user_id'],

            slug=slug,

            title=request.form['title'],

            person_name=request.form['person_name'],

            caption=request.form['caption'],

            event_date=request.form['event_date'],

            theme=request.form['theme'],

            image=",".join(image_urls),

            music=music_url

        )

        db.session.add(project)

        db.session.commit()

        # QR

        qr = qrcode.make(
            f"https://abdullahadel.pythonanywhere.com/m/{slug}"
        )

        qr.save(
            os.path.join(
                BASE_DIR,
                f"static/qrcodes/{slug}.png"
            )
        )

        return redirect('/dashboard')

    return render_template('create.html')

# VIEW

@app.route('/m/<slug>')
def view_project(slug):

    project = Project.query.filter_by(
        slug=slug
    ).first()

    if not project:

        return "Project Not Found"

    images = project.image.split(",")

    return render_template(
        'view_project.html',
        project=project,
        images=images
    )

# DELETE

@app.route('/delete/<int:id>')
def delete_project(id):

    if 'user_id' not in session:

        return redirect('/login')

    project = Project.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first()

    if not project:

        return redirect('/dashboard')

    db.session.delete(project)

    db.session.commit()

    return redirect('/dashboard')

# LOGOUT

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# RUN

if __name__ == '__main__':

    app.run(debug=True)
