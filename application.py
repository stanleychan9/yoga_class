import os
import re

from cs50 import SQL
from datetime import date, datetime, timezone, timedelta
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message
from flask_session import Session
from functools import wraps
from random import randint
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


# Configure application (Ref: Finance)
app = Flask(__name__)

# Ensure templates are auto-reloaded (Ref: Finance)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure mail (Ref: CS50 Week 9 Notes)
# Use os.getenv() to avoid inserting sensitive info in the code (Ref: https://www.reddit.com/r/flask/comments/2v5j2y/question_about_osenvironget_when_using_flaskmail/)
app = Flask(__name__)
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
mail = Mail(app)

# Configure session to use filesystem (instead of signed cookies) (Ref: Finance)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///yogaclass.db")

# Define function for requiring login (Ref: Finance)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in first. If you do not have any account, create one first.")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["GET", "POST"])
def create():
    error = None

    # User reaches the route via GET: Go to the page for account creation
    if request.method == "GET":
        # Forget any user id (de facto log out)
        session.clear()
        return render_template("create.html")

    # User POST information
    else:
        # Get account creation data from the form
        nickname = request.form.get("nickname")
        if not nickname:
            error = "Please provide your nickname. How would you like to be addressed?"
        gender = request.form.get("gender")
        if not gender:
            error = "Please let us know your gender."
        birthyear = request.form.get("birthyear")
        if not birthyear:
            error = "Please let us know your year of birth."
        if len(birthyear) != 4 or birthyear.isnumeric() == False: # Ensure proper year of birth provided
            error = "Please provide your year of birth."
        username = request.form.get("username")
        if not username:
            error = "Please create a username for logging in."
        email = request.form.get("email")
        if not email:
            error = "Please provide a valid email address for communication."
        phone = request.form.get("phone")
        if not phone:
            error = "Please provide a valid local phone number for communication."
        if len(phone) != 8 or phone.isnumeric() == False: # Ensure phone number with 8 numbers provided
            error = "Please provide a valid local phone number for communication."

        # Avoid username / email / phone duplication
        rows = db.execute("SELECT * FROM accounts")
        for i in range(len(rows)):
            if username == rows[i]["username"]:
                error = "Username used already. Please use another username."
            if email == rows[i]["email"]:
                error = "Email address used already."
            if phone == rows[i]["phone"]:
                error = "Phone number used already."

        # Handle password
        password = request.form.get("password")
        if not password:
            error = "Creating a password is a must."
        # Ensure requirement fulfillment (only letters and numbers; at least one of each)
        counter_letter = 0
        counter_number = 0
        for i in range(len(password)):
            if password[i].isalpha() == True:
                counter_letter += 1
            if password[i].isdecimal() == True:
                counter_number += 1
        if (counter_letter == 0) or (counter_number == 0) or (password.isalnum() == False):
            error = "Password does not fulfill all the requirements. Please create another password."

        # Handle password confirmation
        confirm_pw = request.form.get("confirm_pw")
        if not confirm_pw:
            error = "Please confirm your password."
        if confirm_pw != password:
            error = "Password not matched. Please double-check your password."

        if error != None:
            return render_template("create.html", error=error)

        else:
            # Hash the password
            hashed_pw = generate_password_hash(confirm_pw, method='pbkdf2:sha256', salt_length=8)

            # Add information into users table of the database
            db.execute("INSERT INTO accounts (nickname, gender, birthyear, username, email, phone, hash) VALUES(?, ?, ?, ?, ?, ?, ?)",
                        nickname, gender, birthyear, username, email, phone, hashed_pw)

            flash("Account created! Please log in.")
            return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    # User reaches the route via GET: Go to the page for logging in
    if request.method == "GET":
        # Forget any user id (de facto log out)
        session.clear()
        return render_template("login.html")

    # User POST information
    else:
        # Handle username
        username = request.form.get("username")
        if not username:
            flash("Please provide username.")
            return render_template("login.html")
        # Query database for account information of the username
        rows = db.execute("SELECT * FROM accounts WHERE username = ?", username)

        # Ensure valid username and password
        password = request.form.get("password")
        if len(rows) != 1 or check_password_hash(rows[0]["hash"], password) == False:
            flash("Invalid username and / or password.")
            return render_template("login.html")

        else:
            # Remember which user has logged in (Ref: Finance)
            session["user_id"] = rows[0]["id"]
            flash("Login successful. Welcome back!")
            return redirect(url_for("index"))


@app.route("/myaccount", methods=["GET", "POST"])
@login_required
def myaccount():
    # User reaches the route via GET: Go to the page of account info
    if request.method == "GET":

        # Ensure that the user has logged in
        if session.get("user_id") is None:
            flash("Please login before you manage your account.")
            return render_template("login.html")

        else:
            user_id = session["user_id"]
            user = db.execute("SELECT * FROM accounts WHERE id = ?", user_id)
            return render_template("myaccount.html", user=user)

    # User POST new account info
    else:
        # Get info from the form
        user_id = request.form.get("user_id", type=int)
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        confirm_pw = request.form.get("confirm_pw")

        user = db.execute("SELECT * FROM accounts WHERE id = ?", user_id)

        if email:
            db.execute("UPDATE accounts SET email = ? WHERE id = ?", email, user_id)
            flash("Email address updated!")

        if phone:
            if len(phone) != 8 or phone.isnumeric() == False: # Ensure phone number with 8 numbers provided
                flash("Please provide a valid local phone number for communication.")
                return render_template("myaccount.html", user=user)
            else:
                db.execute("UPDATE accounts SET phone = ? WHERE id = ?", phone, user_id)
                flash("Phone number updated!")

        if password:
            # Ensure requirement fulfillment (only letters and numbers; at least one of each)
            counter_letter = 0
            counter_number = 0
            for i in range(len(password)):
                if password[i].isalpha() == True:
                    counter_letter += 1
                if password[i].isdecimal() == True:
                    counter_number += 1
            if (counter_letter == 0) or (counter_number == 0) or (password.isalnum() == False):
                flash("Password does not fulfill all the requirements. Please create another password.")
                return render_template("myaccount.html", user=user)

            # Handle password confirmation
            confirm_pw = request.form.get("confirm_pw")
            if not confirm_pw:
                flash("Please confirm your password.")
                return render_template("myaccount.html", user=user)
            if confirm_pw != password:
                flash("Password not matched. Please double-check your password.")
                return render_template("myaccount.html", user=user)

            else:
                # Hash the password
                hashed_pw = generate_password_hash(confirm_pw, method='pbkdf2:sha256', salt_length=8)
                # Update information into users table of the database
                db.execute("UPDATE accounts SET hash = ? WHERE id = ?", hashed_pw, user_id)
                flash("Password updated!")

        return redirect(url_for("myaccount"))


@app.route("/forgetpw", methods=["GET", "POST"])
def forgetpw():
    # User reaches the route via GET: Go to the page of forgetpw
    if request.method == "GET":
        session.clear()
        return render_template("forgetpw.html")

    # USER post email info
    else:
        error = None
        email = request.form.get("email")
        check_user = db.execute("SELECT * FROM accounts WHERE email = ?", email)

        # Check if the email is used for registration
        if len(check_user) != 1:
            error = "Sorry, wrong email."
            return render_template("forgetpw.html", error=error)

        else:
            nickname = check_user[0]["nickname"]
            username = check_user[0]["username"]
            security_code = randint(10000, 99999)
            now = datetime.now(timezone(timedelta(hours=8)))

            # Create a table for comparing username and security code
            db.execute("CREATE TABLE IF NOT EXISTS resetpw (resetpw_id INTEGER NOT NULL, username TEXT NOT NULL, security_code NUMERIC UNIQUE NOT NULL, time DATETIME NOT NULL, PRIMARY KEY(resetpw_id))")
            db.execute("INSERT INTO resetpw (username, security_code, time) VALUES (?, ?, ?)", username, security_code, now)

            # Send an email to the user (Ref: https://www.tutorialspoint.com/flask/flask_mail.htm | https://pythonprogramming.net/flask-email-tutorial/)
            resetpw_mail = Message("Yoga Class - Resetting your password", recipients=[email])
            resetpw_mail.html = render_template("/mails/resetpw_mail.html", nickname=nickname, username=username, security_code=security_code)
            mail.send(resetpw_mail)

            flash("An email has been sent to you. Please follow the instructions there to reset your password.")
            return redirect(url_for("index"))


@app.route("/resetpw", methods=["GET", "POST"])
def resetpw():
    # User reaches the route via GET (probably from the email): Go to the page of resetpw
    if request.method == "GET":
        session.clear()
        return render_template("resetpw.html")

    # USER post info for resetting pw
    else:
        # Check username and security code
        username = request.form.get("username")
        security_code = request.form.get("security_code", type=int)
        check_user = db.execute("SELECT username, security_code, resetpw_id FROM resetpw WHERE username = ? ORDER BY resetpw_id DESC", username)
        if security_code != check_user[0]["security_code"]:
            flash("Sorry, the username and / or security code is wrong.")
            return render_template("resetpw.html")

        else:
            # Handle password
            password = request.form.get("password")
            if not password:
                flash("Providing a password is a must.")
                return render_template("resetpw.html")
            # Ensure requirement fulfillment (only letters and numbers; at least one of each)
            counter_letter = 0
            counter_number = 0
            for i in range(len(password)):
                if password[i].isalpha() == True:
                    counter_letter += 1
                if password[i].isdecimal() == True:
                    counter_number += 1
            if (counter_letter == 0) or (counter_number == 0) or (password.isalnum() == False):
                flash("Password does not fulfill all the requirements. Please create another password.")
                return render_template("resetpw.html")

            # Handle password confirmation
            confirm_pw = request.form.get("confirm_pw")
            if not confirm_pw:
                flash("Please confirm your password.")
                return render_template("resetpw.html")
            if confirm_pw != password:
                flash("Password not matched. Please double-check your password.")
                return render_template("resetpw.html")

            else:
                # Hash the password
                hashed_pw = generate_password_hash(confirm_pw, method='pbkdf2:sha256', salt_length=8)
                # Update information into users table of the database
                db.execute("UPDATE accounts SET hash = ? WHERE username = ?", hashed_pw, username)
                # Remove user's info in the resetpw table (to avoid resetting the password again with the same security code)
                db.execute("DELETE FROM resetpw WHERE username = ?", username)

                flash("Password reset! Please log in.")
                return redirect(url_for("index"))


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()
    return redirect("/")


@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")


@app.route("/payment")
def payment():
    return render_template("payment.html")


@app.route("/timetable", methods=["GET", "POST"])
def timetable():
    # User reaches the route via GET: Go to the page of timetable
    if request.method == "GET":
        # Create timetable table if not yet created
        db.execute(
            "CREATE TABLE IF NOT EXISTS timetable (id INTEGER NOT NULL, date DATE NOT NULL, start_time TIME, end_time TIME, class_type TEXT NOT NULL, size NUMERIC, place_free NUMERIC, place_held NUMERIC, place_booked NUMERIC, location TEXT, price NUMERIC, remarks TEXT, PRIMARY KEY(id))")

        # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
        now = datetime.now(timezone(timedelta(hours=8)))
        today = now.strftime("%Y-%m-%d")

        timetable = db.execute("SELECT * FROM timetable WHERE date > ? ORDER BY date, start_time", today)
        return render_template("timetable.html", timetable=timetable)

    # User POST information for booking
    else:
        # Ensure that the user has logged in
        if session.get("user_id") is None:
            flash("Please log in before making booking. If you do not an account, create an account first.")
            return render_template("login.html")

        # Get data from the form
        class_id = request.form.get("class_id")
        to_book = request.form.get("to_book", type=int)

        # Query timetable table for booking confirmation
        target_class = db.execute("SELECT * FROM timetable WHERE id = ?", class_id)

        # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
        now = datetime.now(timezone(timedelta(hours=8)))
        today = now.strftime("%Y-%m-%d")

        # Review whether there are enough place(s) in the class
        if to_book > target_class[0]["place_free"]:
            flash("Sorry, there are not enough places in this class.")
            timetable = db.execute("SELECT * FROM timetable WHERE date > ? ORDER BY date, start_time", today)
            return render_template("timetable.html", timetable=timetable)
        else:
            return render_template("confirmbooking.html", to_book=to_book, target_class=target_class)


@app.route("/confirmbooking", methods=["GET", "POST"])
@login_required
def confirmbooking():
    # User reaches the route via GET: Go to class timetable
    if request.method == "GET":
        flash("Please select the class you want to book.")
        return redirect(url_for("timetable"))

    # User confirms booking information
    else:
        # Create table to keep booking info if not yet created
        db.execute(
            "CREATE TABLE IF NOT EXISTS bookings (booking_id INTEGER NOT NULL, user_id INTEGER NOT NULL, class_id INTEGER NOT NULL, places_booked NUMERIC, status TEXT, booking_time DATETIME NOT NULL, PRIMARY KEY(booking_id), FOREIGN KEY(user_id) REFERENCES accounts(id), FOREIGN KEY(class_id) REFERENCES timetable(id))")

        # Get data from confirm booking page
        user_id = session["user_id"]
        class_id = request.form.get("class_id")
        places_booked = request.form.get("to_book", type=int)
        status = "Pending"

        # Adjust booking time to be HK local time
        booking_time = datetime.now(timezone(timedelta(hours=8)))

        # Add booking information to the database
        db.execute("INSERT INTO bookings (user_id, class_id, places_booked, status, booking_time) VALUES (?, ?, ?, ?, ?)", user_id, class_id, places_booked, status, booking_time)

        # Change places available in timetable table
        class_booked = db.execute("SELECT place_free, place_held FROM timetable WHERE id = ?", class_id)
        place_free = class_booked[0]["place_free"] - places_booked
        place_held = class_booked[0]["place_held"] + places_booked
        db.execute("UPDATE timetable SET place_free = ?, place_held = ? WHERE id = ?", place_free, place_held, class_id)

        # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
        now = datetime.now(timezone(timedelta(hours=8)))
        today = now.strftime("%Y-%m-%d")

        # Query booking information for user to review
        past_bookings = db.execute(
            "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date < ? AND accounts.id = ? ORDER BY timetable.date, timetable.start_time", today, user_id)
        upcoming_bookings = db.execute(
            "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date >= ? AND accounts.id = ? ORDER BY timetable.date, timetable.start_time", today, user_id)

        flash("Place(s) being on hold. Please complete the payment procedures within ten hours to confirm the place(s).")
        return render_template("mybookings.html", past_bookings=past_bookings, upcoming_bookings=upcoming_bookings)


@app.route("/mybookings")
@login_required
def mybookings():
    db.execute(
        "CREATE TABLE IF NOT EXISTS bookings (booking_id INTEGER NOT NULL, user_id INTEGER NOT NULL, class_id INTEGER NOT NULL, places_booked NUMERIC, status TEXT, booking_time DATETIME NOT NULL, PRIMARY KEY(booking_id), FOREIGN KEY(user_id) REFERENCES accounts(id), FOREIGN KEY(class_id) REFERENCES timetable(id))")

    user_id = session["user_id"]

    # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")

    # Query booking information for user to review
    past_bookings = db.execute(
        "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date < ? AND accounts.id = ? ORDER BY timetable.date, timetable.start_time", today, user_id)
    upcoming_bookings = db.execute(
        "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date >= ? AND accounts.id = ? ORDER BY timetable.date, timetable.start_time", today, user_id)

    return render_template("mybookings.html", past_bookings=past_bookings, upcoming_bookings=upcoming_bookings)



@app.route("/admin/addclass", methods=["GET", "POST"])
@login_required
def addclass():
    # User reaches the route via GET: Go to the page for logging in
    if request.method == "GET":
        # Check whether the user is admin
        failed_login = None
        if session["user_id"] != 1:
            failed_login = "Please log in as administrator."
            return render_template("login.html", failed_login=failed_login)

        else:
            return render_template("admin/addclass.html")

    # Admin POST information for adding new class
    else:
        error = None

        # Get data from the form
        date = request.form.get("date")
        if not date:
            error = "Please provide class date."
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        class_type = request.form.get("class_type").title()
        if not class_type:
            error = "Please indicate class type."
        size = request.form.get("size")
        location = request.form.get("location").title()
        price = request.form.get("price")
        remarks = request.form.get("remarks")

        if error != None:
            return render_template("admin/addclass.html", error=error)

        else:
            db.execute("INSERT INTO timetable (date, start_time, end_time, class_type, size, place_free, place_held, place_booked, location, price, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    date, start_time, end_time, class_type, size, size, 0, 0, location, price, remarks)
            flash("New class successfully added!")
            return render_template("admin/addclass.html")


@app.route("/admin/manageclass", methods=["GET", "POST"])
@login_required
def manageclass():
    # User reaches the route via GET: Go to the page for logging in
    if request.method == "GET":
        # Check whether the user is admin
        failed_login = None
        if session["user_id"] != 1:
            failed_login = "Please log in as administrator."
            return render_template("login.html", failed_login=failed_login)

        else:
            # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
            now = datetime.now(timezone(timedelta(hours=8)))
            today = now.strftime("%Y-%m-%d")

            timetable = db.execute("SELECT * FROM timetable WHERE date > ? ORDER BY date, start_time", today)
            return render_template("/admin/manageclass.html", timetable=timetable)

    # Admin POST ID number for the class to manage
    else:
        # Get data from form
        class_id = request.form.get("class_id")
        date = request.form.get("date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        class_type = request.form.get("class_type").title()
        size = request.form.get("size")
        place_free = request.form.get("place_free")
        place_held = request.form.get("place_held")
        place_booked = request.form.get("place_booked")
        location = request.form.get("location").title()
        price = request.form.get("price")
        remarks = request.form.get("remarks")

        # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
        now = datetime.now(timezone(timedelta(hours=8)))
        today = now.strftime("%Y-%m-%d")

        # Update timetable table
        db.execute("UPDATE timetable SET date = ?, start_time = ?, end_time = ?, class_type = ?, size = ?, place_free = ?, place_held = ?, place_booked = ?, location = ?, price = ?, remarks = ? WHERE id = ?",
                date, start_time, end_time, class_type, size, place_free, place_held, place_booked, location, price, remarks, class_id)
        timetable = db.execute("SELECT * FROM timetable WHERE date > ? ORDER BY date, start_time", today)
        flash('Class information successfully changed!')
        return render_template("/admin/manageclass.html", timetable=timetable)


@app.route("/admin/managebookings", methods=["GET", "POST"])
@login_required
def managebookings():
    # User reaches the route via GET: Go to the page for logging in
    if request.method == "GET":
        # Check whether the user is admin
        failed_login = None
        if session["user_id"] != 1:
            failed_login = "Please log in as administrator."
            return render_template("login.html", failed_login=failed_login)

        else:
            # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
            now = datetime.now(timezone(timedelta(hours=8)))
            today = now.strftime("%Y-%m-%d")

            # Query booking information for admin to review
            past_bookings = db.execute(
                "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date < ? ORDER BY bookings.booking_id", today)
            upcoming_bookings = db.execute(
                "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date >= ? ORDER BY bookings.booking_id", today)

            return render_template("/admin/managebookings.html", past_bookings=past_bookings, upcoming_bookings=upcoming_bookings)

    # Admin POST info about status changes
    else:
        # Get info from form
        class_id = request.form.get("class_id")
        booking_id = request.form.get("booking_id")
        places_booked = request.form.get("places_booked", type=int) # No. of places booked in the booking; do not mix up with "place_booked" in the timetable table

        # Query place info in timetable table
        class_booked = db.execute("SELECT place_free, place_held, place_booked FROM timetable WHERE id = ?", class_id)
        place_free = class_booked[0]["place_free"]
        place_held = class_booked[0]["place_held"]
        place_booked = class_booked[0]["place_booked"]

        # Query status info in bookings table
        booking_handled = db.execute("SELECT status FROM bookings WHERE booking_id = ?", booking_id)
        status = booking_handled[0]["status"]

        # If status is pending
        if status == "Pending":
            # Get info about status changes
            new_status = request.form.get("new_status_from_pending").title()
            # If the booking is cancelled
            if request.form.get("new_status_from_pending") == "cancelled":
                place_held -= places_booked
                place_free += places_booked
                db.execute("UPDATE timetable SET place_held = ?, place_free = ? WHERE id = ?", place_held, place_free, class_id)
            # If the booking is confirmed
            else:
                place_held -= places_booked
                place_booked += places_booked
                db.execute("UPDATE timetable SET place_held = ?, place_booked = ? WHERE id = ?", place_held, place_booked, class_id)

        # If status is confirmed
        elif status == "Confirmed":
            # Get info about status changes
            new_status = request.form.get("new_status_from_confirmed").title()
            # If the booking is cancelled
            if request.form.get("new_status_from_confirmed") == "cancelled":
                place_booked -= places_booked
                place_free += places_booked
                db.execute("UPDATE timetable SET place_booked = ?, place_free = ? WHERE id = ?", place_booked, place_free, class_id)
            # If the booking is pending
            else:
                place_booked -= places_booked
                place_held += places_booked
                db.execute("UPDATE timetable SET place_booked = ?, place_held = ? WHERE id = ?", place_booked, place_held, class_id)

        # If status is cancelled
        else:
            # Get info about status changes
            new_status = request.form.get("new_status_from_cancelled").title()
            # If booking is pending
            if request.form.get("new_status_from_cancelled") == "pending":
                place_free -= places_booked
                place_held += places_booked
                db.execute("UPDATE timetable SET place_free = ?, place_held = ? WHERE id = ?", place_free, place_held, class_id)
            # If booking is confirmed
            else:
                place_free -= places_booked
                place_booked += places_booked
                db.execute("UPDATE timetable SET place_free = ?, place_booked = ? WHERE id = ?", place_free, place_booked, class_id)

        # Update the bookings timetable
        db.execute("UPDATE bookings SET status = ? WHERE booking_id = ?", new_status, booking_id)

        # Create string that represent today (YYYY-MM-DD) (Ref: https://www.programiz.com/python-programming/datetime/current-datetime)
        now = datetime.now(timezone(timedelta(hours=8)))
        today = now.strftime("%Y-%m-%d")

        # Query booking information for admin to review
        past_bookings = db.execute(
            "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date < ? ORDER BY bookings.booking_id", today)
        upcoming_bookings = db.execute(
            "SELECT * FROM ((bookings INNER JOIN accounts ON bookings.user_id = accounts.id) INNER JOIN timetable ON bookings.class_id = timetable.id) WHERE timetable.date >= ? ORDER BY bookings.booking_id", today)

        return render_template("/admin/managebookings.html", past_bookings=past_bookings, upcoming_bookings=upcoming_bookings)