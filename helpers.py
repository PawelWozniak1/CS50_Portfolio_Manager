import csv
import datetime
import pytz
import requests
import urllib
import uuid
import yfinance as yf

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol using yfinance."""
    try:
        # Use yfinance to fetch data for the given symbol
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")  # Last trading day’s data
        if hist.empty:
            return None  # No data returned for the symbol

        # Retrieve the adjusted close price for the latest trading day
        price = round(hist['Close'].iloc[-1], 2)
        return {"price": price, "symbol": symbol}

    except Exception as e:
        print(f"Error fetching data for symbol {symbol}: {e}")
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
