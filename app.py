import os

from dotenv import load_dotenv

load_dotenv()

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import datetime

from helpers import apology, login_required, lookup, usd

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


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
print(db.execute("SELECT * FROM users"))

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user_id = session['user_id']

    rows = db.execute("SELECT * FROM stock WHERE user_id=?;", user_id)
    stocks = []


    for row in rows:
        api_response = lookup(row['symbol'])
        stocks.append({
            'symbol': api_response['symbol'],
            'name': api_response['name'],
            'shares_amount': row['shares_amount'],
            'price': api_response['price'],
            'total_price': api_response['price'] * row['shares_amount']
        })

    user_cash = db.execute("SELECT cash FROM users WHERE id=?;", user_id)[0]['cash']
    total = sum([stock['total_price'] for stock in stocks]) + user_cash
    return render_template("index.html", stocks=stocks, user_cash=user_cash, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == 'GET':
        return render_template("buy.html")

    user_id = session["user_id"]

    try:
        shares_number = int(request.form.get("shares"))
    except:
        return apology("You must type a valid number")

    symbol = request.form.get("symbol")
    user = db.execute("SELECT * FROM users WHERE id=?;", user_id)[0]
    quote = lookup(symbol)

    try:
        total_value = quote['price'] * shares_number
    except:
        return apology("Quote not found")

    if shares_number <= 0:
        return apology("You must buy at least one share")

    if total_value > user['cash']:
        return apology("Insufficient cash")

    db.execute("INSERT INTO transactions (symbol, shares, price, date, user_id) VALUES (?, ?, ?, ?, ?)", quote['symbol'], shares_number, quote['price'], datetime.now(), user_id)
    db.execute("UPDATE users SET cash=? WHERE id=?;", user['cash'] - total_value, user_id)

    stock = db.execute("SELECT * FROM stock WHERE symbol=? AND user_id=?;", quote['symbol'], user_id)
    if len(stock) > 0:
        amount = stock[0]['shares_amount']
        db.execute("UPDATE stock SET shares_amount=? WHERE user_id=? AND symbol=?;", amount + shares_number, user_id, quote['symbol'])
    else:
        db.execute("INSERT INTO stock (symbol, shares_amount, user_id) VALUES (?, ?, ?);", quote['symbol'], shares_number, user_id)
    return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    user_id = session["user_id"]
    transactions = db.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC;", user_id)

    return render_template("history.html", transactions=transactions)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        data = lookup(symbol)

        if not data:
            return apology("Symbol not found")

        return render_template("quote.html", price=data['price'], company_name=data['name'], symbol=data['symbol'])
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == 'GET':
        return render_template("register.html")

    username = request.form.get('username')
    password = request.form.get('password')
    password_confirmation = request.form.get('confirmation')

    errors = []

    check_username = db.execute("SELECT * FROM users WHERE username=?;", username)
    # Checking if the data is valid
    if len(check_username) > 0:
        errors.append("That username is already being used")
    if len(password) < 5:
        errors.append("Password must have at least 5 characters")
    if username == '':
        errors.append("You must provide an username")
    if password != password_confirmation:
        errors.append("The passwords aren't matching")

    if len(errors) > 0:
        return apology(", ".join(errors))

    hash_password = generate_password_hash(password)

    db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", username, hash_password)

    return redirect("/login")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id=?;", user_id)[0]
    stocks = db.execute("SELECT * FROM stock WHERE user_id=?;", user_id)

    if request.method == "GET":
        return render_template("sell.html", stocks=stocks)

    symbol = request.form.get("symbol")
    try:
        shares = int(request.form.get("shares"))
    except:
        return apology("Provide a valid number")

    api_response = lookup(symbol)
    stock = db.execute("SELECT * FROM stock WHERE user_id=? AND symbol=?;", user_id, api_response["symbol"])[0]
    if shares <= 0:
        return apology("Invalid number of shares")

    if shares > stock['shares_amount']:
        return apology("Not enough shares")

    if shares == stock['shares_amount']:
        db.execute("DELETE FROM stock WHERE user_id=? AND symbol=?;", user_id, api_response["symbol"])
    else:
        db.execute("UPDATE stock SET shares_amount=? WHERE user_id=? AND symbol=?;", stock['shares_amount'] - shares, user_id, api_response["symbol"])

    db.execute("INSERT INTO transactions (symbol, shares, price, date, user_id) VALUES (?, ?, ?, ?, ?)", api_response['symbol'], - 1 * shares, api_response['price'], datetime.now(), user_id)
    db.execute("UPDATE users SET cash=? WHERE id=?;", user['cash'] + (shares * api_response['price']), user_id)
    return redirect('/')

@app.route('/my-account')
@login_required
def my_account():
    user = db.execute("SELECT * FROM users WHERE id=?;", session["user_id"])[0]
    return render_template('my-account.html', user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'GET':
        return render_template("change-password.html")

    old_password = request.form.get("old-password")
    new_password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if len(new_password) < 5:
        return apology("Password must have at least 5 characters")
    if new_password != confirmation:
        return apology("Passwords don't match")

    user = db.execute("SELECT * FROM users WHERE id=?;", session["user_id"])[0]

    if not check_password_hash(user['hash'], old_password):
        return apology("Old password is incorrect")

    db.execute("UPDATE users SET hash=? WHERE id=?;", generate_password_hash(new_password), user["id"])
    return redirect('/my-account')

@app.route("/add-cash", methods=['GET', 'POST'])
def add_cash():
    user = db.execute("SELECT * FROM users WHERE id=?;", session["user_id"])[0]
    if request.method == 'GET':
        return render_template("add-cash.html", user=user)

    cash = request.form.get("cash")
    card = request.form.get("card")

    if int(cash) < 1:
        return apology("You must add at least 1 dollar")

    if len(card) < 10:
        return apology("You must provide a valid card number")

    db.execute("UPDATE users SET cash=? WHERE id=?;", int(cash) + user['cash'], user['id'])
    return redirect("/my-account")

@app.route("/withdraw-cash", methods=['GET', 'POST'])
def withdraw_cash():
    user = db.execute("SELECT * FROM users WHERE id=?;", session["user_id"])[0]
    if request.method == 'GET':
        return render_template("withdraw-cash.html", user=user)

    bank_name = request.form.get("bank")
    cash = request.form.get("cash")
    account = request.form.get("account")

    if len(account) < 0:
        return apology("You must provide a valid account number")

    if len(bank_name) < 0:
        return apology("You must type in a valid bank")

    if int(cash) < 1:
        return apology("You must withdraw at least 1 dollar")

    if int(cash) > user['cash']:
        return apology("Insufficient cash")

    db.execute("UPDATE users SET cash=? WHERE id=?;", user['cash'] - int(cash), user['id'])
    return redirect("/my-account")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
