import os
import sqlite3
import re
from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
DB_PATH = "database.db"
TXT_FOLDER = "txt_posts"

# -------------------- DB KẾT NỐI --------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- TẠO SLUG --------------------
def slugify(text):
    text = re.sub(r'[\W_]+', '-', text.lower())
    return text.strip('-')



# -------------------- IMPORT FILE TXT --------------------
def import_txt_files():
    conn = get_db_connection()
    cursor = conn.cursor()

    for root, _, files in os.walk(TXT_FOLDER):
        for filename in files:
            if not filename.endswith(".txt"):
                continue

            title = os.path.splitext(filename)[0]
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, TXT_FOLDER)
            parts = relative_path.split(os.sep)
            series = parts[0] if len(parts) > 1 else "Chưa phân loại"

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            slug = slugify(title)

            cursor.execute("SELECT id FROM posts WHERE slug = ?", (slug,))
            if cursor.fetchone():
                continue

            cursor.execute("""
                INSERT INTO posts (title, series, content, slug)
                VALUES (?, ?, ?, ?)
            """, (title, series, content, slug))

    conn.commit()
    conn.close()

# -------------------- ROUTE CHÍNH --------------------
@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    selected_series = request.args.get('series', '')
    keyword = request.args.get('q', '').strip()

    conn = get_db_connection()

    series_list = [row['series'] for row in conn.execute("SELECT DISTINCT series FROM posts")]

    # Xây dựng truy vấn
    base_query = "SELECT * FROM posts"
    where_clauses = []
    params = []

    if selected_series:
        where_clauses.append("series = ?")
        params.append(selected_series)

    if keyword:
        where_clauses.append("title LIKE ?")
        params.append(f"%{keyword}%")

    where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    full_query = f"{base_query}{where_clause} ORDER BY title LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    posts = conn.execute(full_query, params).fetchall()

    count_query = f"SELECT COUNT(*) FROM posts{where_clause}"
    total = conn.execute(count_query, params[:-2]).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page

    conn.close()

    return render_template("index.html",
                           posts=posts,
                           page=page,
                           total_pages=total_pages,
                           series_list=series_list,
                           selected_series=selected_series,
                           keyword=keyword,
                           max=max,
                           min=min)


# -------------------- ROUTE CHI TIẾT POST --------------------
@app.route('/post/<slug>')
def post_detail(slug):
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()

    if not post:
        abort(404)

    next_post = conn.execute("SELECT slug FROM posts WHERE id > ? ORDER BY id LIMIT 1", (post['id'],)).fetchone()
    prev_post = conn.execute("SELECT slug FROM posts WHERE id < ? ORDER BY id DESC LIMIT 1", (post['id'],)).fetchone()
    conn.close()

    return render_template("post_detail.html", post=post, next_post=next_post, prev_post=prev_post)

# -------------------- CHẠY IMPORT KHI KHỞI ĐỘNG --------------------
with app.app_context():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            series TEXT DEFAULT NULL,
            content TEXT DEFAULT '',
            slug TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    import_txt_files()

if __name__ == '__main__':
    app.run(debug=True)
