from helpers import get_db, lookup, get_user_cash
from datetime import datetime
def sell_stock(username, symbol, amount):
    data = lookup(symbol)
    price = data['price']
    cash_to_add = price * amount


    db = get_db()
    with db:
        current_shares = db.cursor().execute('SELECT amount FROM holdings WHERE username = ? and symbol = ?', (username, symbol)).fetchone()
        current_shares = current_shares[0]

        if amount == current_shares:
            db.cursor().execute('DELETE FROM holdings WHERE symbol = ?', (symbol, ))
        else:
            remaining_shares = current_shares - amount
            db.cursor().execute('UPDATE holdings SET amount = ? WHERE username = ? AND symbol = ?', (remaining_shares, username, symbol))


        db.cursor().execute('UPDATE users SET cash = ? WHERE username = ?', (cash_to_add + get_user_cash(), username))
        sql = 'INSERT INTO transactions (username, company, symbol, price, amount, value, type, date) VALUES(?,?,?,?,?,?,?,?)'
        date = str(datetime.now())
        tuple = (username, data['company'], data['symbol'], data['price'], amount, cash_to_add, 'sell', date)
        db.cursor().execute(sql, tuple)
