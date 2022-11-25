import requests

from datetime import datetime

from flask import (
    Flask, 
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    login_required,
    login_manager,
    logout_user,
    UserMixin,
)
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'very secret key'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    finished = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Project %r>' % self.title


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

@app.route("/")
def home():
    my_projects = Project.query.all()
    weather_mood = get_weather_mood()
    return render_template(
        'index.html',
        user=current_user,
        my_projects=my_projects, 
        weather_mood=weather_mood,
    )


def get_weather_data():
    weather_data = requests.get(
        url='https://danepubliczne.imgw.pl/api/data/synop/station/warszawa'
    ).json()

    temperature = float(weather_data['temperatura'])
    pressure = float(weather_data['cisnienie'])
    rainfall = float(weather_data['suma_opadu'])

    return temperature, pressure, rainfall


def get_weather_mood():
    temperature, pressure, rainfall = get_weather_data()
    work_mood = 'sprzyja'
    comment = 'więc prawdopodobnie pracuję nad którymś z projektów'

    if pressure < 1010 or pressure > 1020:  # niekorzystne cisnienie
        work_mood = 'nie sprzyja'
        comment = 'warto poczekać na lepszy biomet'
    else: # cisnienie sprzyja
        if rainfall < 10:  # deszcz nie pada
            if temperature > 20:  # jest ciepło
                work_mood = 'nie sprzyja'
                comment = 'jest ciepło i nie pada, więc zapewnie jestem offline :)'
            else:  # temperatura nie za wysoka 
                comment = 'sprzyja'
                comment = 'ale sprzyja również spacerom'

    if rainfall < 1:
        rain_info = 'Dziś nie pada :)'
    elif rainfall < 10:
        rain_info = 'Może lekko popadać.'
    else:
        rain_info = 'Weź parasol!'

    return f'Pogoda {work_mood} programowaniu, {comment}. PS. {rain_info}'


@app.route("/projects", methods=["POST"])
@login_required
def add_project():
    title = request.form.get("title")
    category = request.form.get("category")
    link = request.form.get("link")

    new_project = Project(
        title=title, 
        category=category,
        link=link,
    )

    db.session.add(new_project)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/projects/<int:id>/change_status")
@login_required
def change_status(id):
    project = Project.query.get_or_404(id)
    project.finished = not project.finished
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/projects/<int:id>/delete")
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/projects/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(id):
    project = Project.query.get_or_404(id)

    if request.method == "GET":
        return render_template('edit_project.html', project=project)

    project.title = request.form.get("title")
    project.category = request.form.get("category")
    project.link = request.form.get("link")
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == password:
                login_user(user, remember=True)
                return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
