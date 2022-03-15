from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm
import os

app = Flask(__name__)

uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
    
app.config["SQLALCHEMY_DATABASE_URI"] = uri if uri else "postgresql:///flask-feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "58fd32s")
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()


@app.route("/")
def homepage():
    return redirect("/register")


# User Routes

@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, password, email, first_name, last_name)
        db.session.commit()
        session['username'] = user.username
        flash("Welcome! Your account has been created.")
        return redirect(f"/users/{user.username}")

    else:
        return render_template("users/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome back {user.first_name}!")
            session["username"] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ["Invalid username or password."]
            return render_template("users/login.html", form=form)

    return render_template("users/login.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("username")
    flash("Successfully logged out.")
    return redirect("/login")


@app.route("/users/<username>")
def show_user(username):
    if "username" not in session or username != session["username"]:
        return redirect("/unauthorized")

    user = User.query.get_or_404(username)
    form = DeleteForm()

    return render_template("users/show.html", user=user, form=form)


@app.route("/users/<username>/delete", methods=["POST"])
def remove_user(username):
    if "username" not in session or username != session["username"]:
        return redirect("/unauthorized")

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()

    session.pop("username")
    flash("Successfully deleted account.")

    return redirect("/login")


# Feedback Routes

@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    if "username" not in session or username != session["username"]:
        return redirect("/unauthorized")

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(title=title, content=content, username=username)
        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    else:
        return render_template("feedback/new.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return redirect("/not_found")


    if "username" not in session or feedback.username != session["username"]:
        return redirect("/unauthorized")

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("/feedback/edit.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return redirect("/not_found")

    if "username" not in session or feedback.username != session["username"]:
        return redirect("/unauthorized")

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")


# Error Routes

@app.route("/not_found")
def not_found():
    return render_template("not_found.html")


@app.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html")
