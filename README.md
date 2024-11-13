# Portfolio Management Web App

This project is a web application designed to help users manage their stock portfolios, including functionalities for registering, logging in, checking stock quotes, viewing portfolio value, and executing transactions. The app allows users to track their investments, monitor stock prices, and simulate stock trades in a secure environment.

This project is a web application designed to manage stock portfolios, allowing users to register, login, and track their stock investments. Built as part of the **CS50's Introduction to Computer Science** course, the application implements key functionalities for managing a portfolio, such as adding stocks, checking stock prices, and viewing portfolio value.

## Features

- **User Registration and Authentication:** Users can create an account, securely log in, and log out. Passwords are hashed for security.
- **Portfolio Management:** Users can add stocks to their portfolio, view current values, and calculate their total holdings.
- **Real-Time Stock Quotes:** Users can check the latest stock prices and values in their portfolios.
- **Transactions:** Users can simulate buying and selling stocks, with changes reflected in their portfolio.
- **Error Handling and Data Validation:** The app handles potential errors like duplicate usernames or password mismatches during registration.

## Technologies Used

- **Python & Flask**: Backend server and routes for handling requests.
- **SQLite**: Database for managing user and portfolio data.
- **Jinja Templates**: HTML templates to dynamically render pages.
- **JavaScript**: Used for front-end enhancements, including data visualization with Chart.js.
- **Chart.js**: Visualizes portfolio data for intuitive tracking of stock values.

## Project Structure

- **app.py**: Main application file containing route definitions and request handling.
- **templates/**: HTML templates for rendering pages, including `register.html`, `login.html`, and portfolio visualization pages.
- **helpers.py**: Contains utility functions for user authentication, error handling, and database queries.

## How to Use

1. Register a new user account.
2. Log in to access the portfolio dashboard.
3. Add stocks to your portfolio by entering the stock symbol and the quantity.
4. Check real-time quotes and view changes in portfolio value.
5. Simulate buying or selling stocks and track the updated portfolio value.