import requests
import urllib.parse
import sqlite3
from flask import redirect, render_template, request, session
from functools import wraps
from datetime import datetime


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""
    #use world trading api for stock price info
    #user alphavantage api for dropdown box of stock tickers
    # Contact API

        #WT API key#
        #ZU5ZSIIHUK5ROLW5
        #Alpha alphavantage
    ALPHA_VANTAGE_API_KEY = 'O02B0eboeRpJdEq4JSVO4E2lzC2F9HqldjIHd3QD1Z8E1U73DQlkLPLWUihP'

    alpha_vantage_api_request = f'https://api.worldtradingdata.com/api/v1/stock?symbol={symbol}&api_token={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(alpha_vantage_api_request)


    # Parse response
    data = response.json()['data'][0]
    return {
            "company": data["name"],
            "price": float(data["price"]),
            "symbol": data["symbol"]
        }


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def get_db():
    db = sqlite3.connect('finance.db')
    return db

def get_user_name():
    user_id = session.get('user_id')
    db = get_db()
    with db:
        sql = 'SELECT username FROM users WHERE id = ?'
        tuple = (user_id,)
        rows = db.cursor().execute(sql, tuple)
        user_name_tuple = rows.fetchone()
        return user_name_tuple[0]

def get_user_cash():
    sql = 'SELECT cash FROM users WHERE id = ?'
    id = session.get('user_id')
    db = get_db()
    with db:
        rows = db.cursor().execute(sql, (id,))
        rows = rows.fetchone()
        return rows[0]

def can_user_purchase(symbol, num_shares):
    data = lookup(symbol)
    price = data['price']
    cost_to_purchase = price * num_shares
    query = 'SELECT cash FROM users WHERE id = ?'
    db = get_db()
    with db:
        user_cash = db.cursor().execute(query, (session.get('user_id'),)).fetchone()[0]
        if cost_to_purchase >= user_cash:
            print('Transaction cost is', cost_to_purchase)
            print('User cash is', user_cash)
            return False
        else:
             return True

def add_buy_transaction(symbol, num_shares):
    date = str(datetime.now())
    sql = 'INSERT INTO transactions (username, company, symbol, price, amount, value, type, date) VALUES(?,?,?,?,?,?,?, ?)'
    data = lookup(symbol)
    value = data['price'] * num_shares
    username = get_user_name()

    tuple = (username, data['company'], data['symbol'], data['price'], num_shares, value, 'buy', date)
    db = get_db()
    with db:
        db.cursor().execute(sql, tuple)

def update_holdings_buy(symbol, num_shares):
    db = get_db()
    with db:
        sql = 'SELECT amount FROM holdings WHERE username = ? AND symbol = ?'
        rows = db.cursor().execute(sql, (get_user_name(), symbol))
        amount = rows.fetchone()

        if amount != None:
            sql = 'UPDATE holdings SET amount = ? WHERE username = ? AND symbol = ?'
            tuple = (num_shares + amount[0], get_user_name(), symbol)
            db.cursor().execute(sql, tuple)
        else:
            data = lookup(symbol)
            price = data['company']
            sql = 'INSERT INTO holdings (username, company, symbol, amount) VALUES(?,?,?,?)'
            tuple = (get_user_name(), data['company'], symbol, num_shares)
            db.cursor().execute(sql, tuple)

def get_holdings(username):
    db = get_db()
    with db:
        rows = db.cursor().execute('SELECT * FROM holdings WHERE username = ?', (username,)).fetchall()
        return rows

def deduct_user_cash(symbol, num_shares):
    data = lookup(symbol)
    price = data['price']
    total_cost = num_shares * price

    sql = 'UPDATE users SET cash = ? WHERE id = ?'
    db = get_db()
    with db:
        rows = db.cursor().execute('SELECT cash FROM users WHERE id = ?', (session.get('user_id'),))
        cash = rows.fetchone()[0]
        cash -= total_cost
        db.cursor().execute(sql, (cash, session.get('user_id'),))
