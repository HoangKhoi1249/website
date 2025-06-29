import os
import sqlite3
from jinja2 import Environment, FileSystemLoader
import shutil
import re

DB_PATH = "database.db"
OUTPUT_DIR = "../static_site"
POSTS_DIR = os.path.join(OUTPUT_DIR, "posts")
ASSETS_DIR = os.path.join(OUTPUT_DIR, "assets")
PER_PAGE = 5

# Slug hóa cho tên series
def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[\s_-]+', '-', text)

# Xóa thư mục static_site nếu tồn tại
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)

# Tạo thư mục mới
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Kết nối DB
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
posts = conn.execute("SELECT * FROM posts ORDER BY title").fetchall()
series_rows = conn.execute("SELECT DISTINCT series FROM posts WHERE series IS NOT NULL").fetchall()
conn.close()

# Chuẩn hóa danh sách series
series_list = []
for row in series_rows:
    name = row[0]
    slug = slugify(name)
    series_list.append({"name": name, "slug": slug})

# Nạp template
env = Environment(loader=FileSystemLoader("templates"))
index_template = env.get_template("index_static.html")
detail_template = env.get_template("post_detail_static.html")

# Tạo từng trang post riêng
for i, post in enumerate(posts):
    prev_post = posts[i - 1] if i > 0 else None
    next_post = posts[i + 1] if i < len(posts) - 1 else None

    output_path = os.path.join(POSTS_DIR, f"{post['slug']}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(detail_template.render(
            post=post,
            prev_post=prev_post,
            next_post=next_post
        ))


# Tạo index.html có phân trang
total_pages = (len(posts) + PER_PAGE - 1) // PER_PAGE
for page in range(1, total_pages + 1):
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_posts = posts[start:end]
    html = index_template.render(
        posts=page_posts,
        page=page,
        total_pages=total_pages,
        base_name="index" if page > 1 else "index",
        series_list=series_list,
        current_series=None
    )

    filename = "index.html" if page == 1 else f"index{page}.html"
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(html)

# Tạo trang lọc theo series
for series in series_list:
    filtered_posts = [p for p in posts if p['series'] == series['name']]
    total_pages = (len(filtered_posts) + PER_PAGE - 1) // PER_PAGE

    for page in range(1, total_pages + 1):
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        page_posts = filtered_posts[start:end]
        html = index_template.render(
            posts=page_posts,
            page=page,
            total_pages=total_pages,
            base_name=f"series_{series['slug']}_" if page > 1 else f"series_{series['slug']}",
            series_list=series_list,
            current_series=series['name']
        )

        filename = f"series_{series['slug']}.html" if page == 1 else f"series_{series['slug']}_{page}.html"
        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            f.write(html)

# Copy CSS
shutil.copyfile("static/style.css", os.path.join(ASSETS_DIR, "style.css"))

print("✅ Đã tạo lại toàn bộ website tĩnh trong thư mục static_site/")