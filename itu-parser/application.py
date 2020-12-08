import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, get_departments, get_course_table

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///students.db")

# Get department list as a global list
department_list = get_departments()

@app.route("/")
@login_required
def index():
    department_raw = db.execute("SELECT department FROM users WHERE id = :id", id=session['user_id'])
    dep_code = department_raw[0]['department']

    dep_name = department_list[dep_code]

    tables_list = get_course_table(dep_code)

    return render_template("index.html", dep_code=dep_code, dep_name=dep_name,
                            tables_list=tables_list, headers=tables_list[0][1].columns)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["USERNAME"] = request.form.get('username')

        # Redirect user to home page
        flash(f"Welcome back, {request.form.get('username')}")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":

        if not request.form.get("old_password"):
            return apology("must provide old password", 403)

        # Ensure password was submitted twice
        elif not request.form.get("new_password") or not request.form.get("new_password_second"):
            return apology("must provide new password", 403)

        # Ensure passwords do match
        elif not request.form.get("new_password") == request.form.get("new_password_second"):
            return apology("new passwords must match", 403)


        # Check for old password
        old_hash = db.execute("SELECT hash FROM users WHERE id = :id",
                                id=session['user_id'])

        if not check_password_hash(old_hash[0]['hash'], request.form.get("old_password")):
            return apology("old password is incorrect", 403)

        new_hash = generate_password_hash(request.form.get("new_password_second"))

        db.execute("UPDATE users SET hash = :new_hash WHERE id = :id",
                    new_hash=new_hash, id=session['user_id'])

        flash('Password changed successfully!')
        # Redirect to mainpage
        return redirect("/")

    # Render register page if the method is GET
    else:
        return render_template("change-password.html")





@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted twice
        elif not request.form.get("password_first") or not request.form.get("password_second"):
            return apology("must provide password", 403)

        # Ensure passwords do match
        elif not request.form.get("password_first") == request.form.get("password_second"):
            return apology("passwords must match", 403)

        # Query database for checking username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username is unique
        if len(rows) != 0:
            return apology("username already taken", 403)

        # Hash user password
        hashpwd = generate_password_hash(request.form.get("password_second"))

        # Get department info
        department_code = request.form.get("department")

        if not department_code:
            return apology("must provide department code", 403)

        # Insert new user into database
        db.execute("INSERT INTO users (username, hash, department) VALUES (:username, :hash, :department_code)",
                    username=request.form.get("username"),
                    hash=hashpwd,
                    department_code=department_code)

        flash('Registered successfully! Sign in to continue.')
        # Redirect to mainpage
        return redirect("/")

    # Render register page if the method is GET
    else:
        return render_template("register.html", departments=department_list)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
