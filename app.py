import os


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
from sell_helpers import sell_stock

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



@app.route("/")
@login_required
def index():
    username = get_user_name()
    data = get_holdings(username)
    data = [list(i) for i in data]
    total_value = 0
    for item in data:
        symbol = item[3]
        amount = item[4]
        current_price = lookup(symbol)['price']
        current_value = amount * current_price
        total_value += current_value
        item.append(current_price)
        item.append(current_value)
    cash = get_user_cash()
    total_value += cash
    return render_template('index.html', data=data, cash=cash, total_value=total_value)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == 'GET':
        return render_template('buy.html')

    symbol = request.form.get('symbol')
    num_shares = int(request.form.get('num_shares'))

    if not can_user_purchase(symbol, num_shares):
        flash('Not enough cash for this transaction.')
        return redirect('buy')

    add_buy_transaction(symbol, num_shares)
    update_holdings_buy(symbol, num_shares)
    deduct_user_cash(symbol, num_shares)
    return redirect('/')







@app.route("/history")
@login_required
def history():
    db = get_db()
    with db:
        sql = 'SELECT * FROM transactions'
        rows = db.cursor().execute(sql).fetchall()

    return render_template('history.html', data=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        rows = db.cursor().execute("SELECT * FROM users WHERE username = ?",(username,))
        user = rows.fetchone()

        if not user or not check_password_hash(user[2], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user[0]

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
    if request.method == 'GET':
        return render_template('quote.html')
    else:
        symbol = request.form.get('symbol')
        data = lookup(symbol)
        return render_template('quote.html', data=data)




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        if password != confirmation:
            flash('Password field and confirmation field do not match.')
            return redirect('/register')
        db = get_db()
        rows = db.cursor().execute('SELECT * FROM users WHERE username = ?',(username,))
        rows = rows.fetchall()

        if len(rows) > 0:
            flash('You already have an account. Try logging in.')
            return redirect('/login')

        hash = generate_password_hash(password)
        db.cursor().execute('INSERT INTO users (username, hash) VALUES (?, ?)', (username, hash))
        db.commit()
        flash('Account created.')
        return render_template('login.html')

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == 'GET':
        return render_template('sell.html')

    symbol = request.form.get('symbol')
    num_shares = int(request.form.get('num_shares'))
    username = get_user_name()
    data = get_holdings(username)
    for item in data:
        if item[3] == symbol and num_shares <= item[4]:
            sell_stock(username, symbol, num_shares)

    return render_template('sell.html')



def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

app.run(debug=True)
