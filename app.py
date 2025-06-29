import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)
DB_PATH = "database.db"
TXT_FOLDER = "txt_posts"

# -------------------- DB KẾT NỐI --------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

            # Series = tên thư mục cha (so với TXT_FOLDER)
            relative_path = os.path.relpath(file_path, TXT_FOLDER)
            parts = relative_path.split(os.sep)
            series = parts[0] if len(parts) > 1 else "Chưa phân loại"

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Tránh trùng tên và series
            cursor.execute("SELECT id FROM posts WHERE title = ? AND series = ?", (title, series))
            if cursor.fetchone():
                continue

            cursor.execute("""
                INSERT INTO posts (title, series, content)
                VALUES (?, ?, ?)
            """, (title, series, content))

    conn.commit()
    conn.close()

# -------------------- ROUTE CHÍNH --------------------
@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page
    selected_series = request.args.get('series', '')

    conn = get_db_connection()

    series_list = [row['series'] for row in conn.execute("SELECT DISTINCT series FROM posts")]

    base_query = "SELECT * FROM posts"
    where_clause = ""
    params = []
    if selected_series:
        where_clause = " WHERE series = ?"
        params.append(selected_series)

    full_query = base_query + where_clause + " ORDER BY title LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    posts = conn.execute(full_query, params).fetchall()

    count_query = "SELECT COUNT(*) FROM posts" + where_clause
    total = conn.execute(count_query, params[:-2]).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page

    conn.close()

    return render_template("index.html", posts=posts, page=page, total_pages=total_pages,
                           series_list=series_list, selected_series=selected_series)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    next_post = conn.execute("SELECT id FROM posts WHERE id > ? ORDER BY id LIMIT 1", (post_id,)).fetchone()
    prev_post = conn.execute("SELECT id FROM posts WHERE id < ? ORDER BY id DESC LIMIT 1", (post_id,)).fetchone()
    conn.close()

    if not post:
        return "Bài viết không tồn tại", 404

    return render_template("post_detail.html", post=post, next_post=next_post, prev_post=prev_post)


# -------------------- CHẠY IMPORT KHI KHỞI ĐỘNG --------------------
with app.app_context():
    import_txt_files()

if __name__ == '__main__':
    app.run(debug=True)
