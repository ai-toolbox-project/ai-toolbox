from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "ai_toolbox_secret_key"  # later you can change this

DB_PATH = os.path.join("database", "database.db")


# -------------------- DATABASE CONNECTION --------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------- DATABASE INITIALIZATION --------------------
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # User table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS USER_TB (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Admin table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ADMIN_TB (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Category table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CAT_TB (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    """)

    # Tool table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TOOL_TB (
            tool_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            description TEXT,
            benefits TEXT,
            limitations TEXT,
            usability_score INTEGER,
            access_link TEXT,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES CAT_TB (category_id)
        )
    """)

    conn.commit()
    conn.close()


# -------------------- BASIC ROUTES --------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    if not os.path.exists("database"):
        os.makedirs("database")

    init_db()
    app.run(debug=True)
