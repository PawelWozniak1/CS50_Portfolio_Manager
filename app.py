import os
import plotly.graph_objs as go

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Retrieve the user's portfolio from the database
    user_portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?", session["user_id"])

    # Initialize variables to calculate total values
    total_portfolio_value = 0

    # Calculate total value of each row in the portfolio
    for row in user_portfolio:
        total_portfolio_value += row["shares"] * row["price"]

    # Retrieve user's cash balance
    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

    # Calculate total worth (cash + portfolio value)
    total_worth = user_cash + total_portfolio_value

    return render_template("portfolio.html", portfolio=user_portfolio, total_worth=total_worth, user_cash=user_cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Retrieve form data
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Validate form data
        if not symbol:
            return apology("Stock symbol is required")
        if not shares:
            return apology("Number of shares is required")
        if not shares.isdigit() or int(shares) <= 0:
            return apology("Number of shares must be a positive integer")

        # Standardize the symbol to uppercase
        symbol = symbol.upper()

        # Query stock information using the standardized symbol
        stock_info = lookup(symbol)
        if not stock_info:
            return apology("Invalid stock symbol")

        # Calculate the total cost of the transaction
        total_cost = stock_info["price"] * int(shares)

        # Check if the user has enough cash to make the purchase
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        if total_cost > user_cash:
            return apology("Insufficient funds")

        # Update user's cash balance
        updated_cash = user_cash - total_cost
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, session["user_id"])

        # Update user's portfolio
        existing_shares = db.execute("SELECT shares FROM portfolio WHERE user_id = ? AND symbol = ?",
                                     session["user_id"], symbol)
        if existing_shares:
            updated_shares = existing_shares[0]["shares"] + int(shares)
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
                       updated_shares, session["user_id"], symbol)
        else:
            db.execute("INSERT INTO portfolio (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                       session["user_id"], symbol, shares, stock_info["price"])

        # Insert record into transactions table for buy transaction
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type) VALUES (?, ?, ?, ?, ?)",
                   session["user_id"], symbol, shares, stock_info["price"], "buy")

        # Return a success message
        flash("Purchase successful")
        return redirect("/")

    elif request.method == "GET":
        # Render the buy form for the user
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Query all transaction history for the logged-in user from the transactions table
    transactions = db.execute(
        "SELECT symbol, shares, price, transaction_type, timestamp FROM transactions WHERE user_id = ? ORDER BY id DESC", session["user_id"])

    # Render the transaction history template with the transactions data
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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
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
    """Get stock quote."""
    if request.method == "GET":
        # Render the quote form for the user
        return render_template("quote_form.html")
    elif request.method == "POST":
        # Retrieve the stock symbol from the form data
        symbol = request.form.get("symbol")

        # Validate the form data
        if not symbol:
            return apology("Stock symbol is required")

        # Fetch the stock quote using the provided symbol
        quote_info = lookup(symbol)

        # Check if the symbol is valid and a quote is retrieved
        if not quote_info:
            return apology("Invalid stock symbol")

        # Render a template to display the stock quote
        return render_template("quote_result.html", quote_info=quote_info)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 400)

        # Ensure password confirmation was submitted
        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("must confirm password", 400)

        # Check if password and confirmation match
        if password != confirmation:
            return apology("passwords must match", 400)

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert the new user into the database
        result = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                            username, hashed_password)

        # Check if the username already exists
        if not result:
            return apology("username already exists", 400)

        # Log in the newly registered user
        user_id = result
        session["user_id"] = user_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # Retrieve form data
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Validate form data
        if not symbol:
            return apology("Stock symbol is required")
        if not shares:
            return apology("Number of shares is required")
        if not shares.isdigit() or int(shares) <= 0:
            return apology("Number of shares must be a positive integer")

        # Query the user's portfolio to check if they own the specified stock
        portfolio_entry = db.execute(
            "SELECT * FROM portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)
        if not portfolio_entry:
            return apology("You don't own any shares of this stock")

        # Check if the user has enough shares to sell
        owned_shares = portfolio_entry[0]["shares"]
        if int(shares) > owned_shares:
            return apology("You don't own enough shares to sell")

        # Fetch the current stock price
        stock_info = lookup(symbol)
        if not stock_info:
            return apology("Failed to fetch stock information")

        # Calculate the total sale value
        total_sale_value = stock_info["price"] * int(shares)

        # Update the user's cash balance
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        updated_cash = user_cash + total_sale_value
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, session["user_id"])

        # Update the user's portfolio to reflect the sale
        updated_shares = owned_shares - int(shares)
        if updated_shares == 0:
            # If all shares are sold, remove the stock from the portfolio
            db.execute("DELETE FROM portfolio WHERE user_id = ? AND symbol = ?",
                       session["user_id"], symbol)
        else:
            # Otherwise, update the number of shares in the portfolio
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
                       updated_shares, session["user_id"], symbol)

        # Insert record into transactions table for sell transaction
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type) VALUES (?, ?, ?, ?, ?)",
                   session["user_id"], symbol, shares, stock_info["price"], "sell")

        # Redirect the user to a success page
        flash("Stock sold successfully")
        return redirect("/")

    elif request.method == "GET":
        # Query the user's portfolio to get the list of stocks they own
        portfolio = db.execute("SELECT symbol FROM portfolio WHERE user_id = ?", session["user_id"])

        # Render the sell form for the user, passing the list of stocks they own
        return render_template("sell_form.html", portfolio=portfolio)


@app.route("/portfolio_chart")
@login_required
def portfolio_chart():
    # Retrieve portfolio data from the database
    portfolio_data = db.execute(
        "SELECT timestamp, price, shares FROM portfolio WHERE user_id = ?", session["user_id"])

    # Extract timestamps from the portfolio data
    timestamps = [entry["timestamp"] for entry in portfolio_data]

    # Convert timestamps to the desired format
    formatted_timestamps = [datetime.strptime(
        entry["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S") for entry in portfolio_data]

    # Calculate the total value of each stock
    stock_values = [entry["price"] * entry["shares"] for entry in portfolio_data]
    total_value_values = [sum(stock_values[:i + 1]) for i in range(len(stock_values))]

    # Pass the formatted timestamps to the template
    return render_template("portfolio_chart.html", timestamps=formatted_timestamps, stock_value_values=stock_values,
                           total_value_values=total_value_values)
