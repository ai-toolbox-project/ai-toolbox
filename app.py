from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

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

    categories = [
        "Education",
        "Business & Marketing",
        "Coding & Development",
        "Healthcare",
        "Design"
    ]

    for cat in categories:
        cursor.execute(
            "INSERT OR IGNORE INTO CAT_TB (category_name) VALUES (?)",
            (cat,)
        )


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

         # -------------------- DEFAULT ADMIN --------------------
    cursor.execute(
        "SELECT * FROM ADMIN_TB WHERE username = ?", ("admin",)
    )
    admin = cursor.fetchone()

    if not admin:
        cursor.execute(
            "INSERT INTO ADMIN_TB (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123"))
        )



    conn.commit()
    conn.close()


# -------------------- BASIC ROUTES --------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------- USER REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO USER_TB (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already exists"
        
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# -------------------- ADMIN LOGIN --------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        admin = conn.execute(
            "SELECT * FROM ADMIN_TB WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["admin_id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid admin credentials"

    return render_template("admin_login.html")

# -------------------- USER LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM USER_TB WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


# -------------------- ADMIN DASHBOARD --------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    tools = conn.execute("""
        SELECT TOOL_TB.*, CAT_TB.category_name
        FROM TOOL_TB
        LEFT JOIN CAT_TB ON TOOL_TB.category_id = CAT_TB.category_id
    """).fetchall()
    conn.close()

    return render_template("admin_dashboard.html", tools=tools)

# -------------------- ADMIN ADD TOOL --------------------
@app.route("/admin/add-tool", methods=["GET", "POST"])
def add_tool():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()

    if request.method == "POST":
        tool_name = request.form["tool_name"]
        description = request.form["description"]
        benefits = request.form["benefits"]
        limitations = request.form["limitations"]
        usability_score = request.form["usability_score"]
        access_link = request.form["access_link"]
        category_id = request.form["category_id"]

        conn.execute("""
            INSERT INTO TOOL_TB
            (tool_name, description, benefits, limitations, usability_score, access_link, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tool_name, description, benefits, limitations,
            usability_score, access_link, category_id
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("admin_dashboard"))

    categories = conn.execute("SELECT * FROM CAT_TB").fetchall()
    conn.close()

    return render_template("add_tool.html", categories=categories)

# -------------------- ADMIN DELETE TOOL --------------------
@app.route("/admin/delete-tool/<int:tool_id>")
def delete_tool(tool_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM TOOL_TB WHERE tool_id = ?", (tool_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- USER TOOL LIST --------------------
@app.route("/tools")
def tools():
    conn = get_db_connection()

    category = request.args.get("category")
    search = request.args.get("search")

    query = """
        SELECT TOOL_TB.*, CAT_TB.category_name
        FROM TOOL_TB
        JOIN CAT_TB ON TOOL_TB.category_id = CAT_TB.category_id
    """
    params = []

    if category:
        query += " WHERE CAT_TB.category_name = ?"
        params.append(category)

    if search:
        query += " AND tool_name LIKE ?" if category else " WHERE tool_name LIKE ?"
        params.append(f"%{search}%")

    tools = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT * FROM CAT_TB").fetchall()
    conn.close()

    return render_template("tools.html", tools=tools, categories=categories)


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    if not os.path.exists("database"):
        os.makedirs("database")

    init_db()
    app.run(debug=True)
