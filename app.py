from flask import Flask, abort, render_template
import json
import markdown
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
BLOGS = os.path.join(DATA, "blogs")

app = Flask(__name__)


def load(name):
    with open(os.path.join(DATA, name), "r", encoding="UTF-8") as f:
        return json.load(f)


def post_meta(filename):
    """Title is the first '# ' heading, date is a '**Date:**' line if present."""
    title = filename.replace(".md", "").replace("-", " ").title()
    date = ""
    with open(os.path.join(BLOGS, filename), "r", encoding="UTF-8") as f:
        for line in f:
            if line.startswith("# "):
                title = line[2:].strip()
            m = re.match(r"\*\*Date:\*\*\s*(.+)", line)
            if m:
                date = m.group(1).strip()
                break
    return {"filename": filename, "title": title, "date": date}


def all_posts():
    files = sorted((f for f in os.listdir(BLOGS) if f.endswith(".md")), reverse=True)
    return [post_meta(f) for f in files]


@app.route("/")
def home():
    return render_template(
        "index.html",
        profile=load("profile.json"),
        projects=load("projects.json"),
        competitions=load("competitions.json"),
        posts=all_posts(),
    )


@app.route("/blog")
def blog():
    return render_template("blog_list.html", posts=all_posts())


@app.route("/blog/<filename>")
def blog_post(filename):
    # basename blocks path tricks like ../
    filename = os.path.basename(filename)
    path = os.path.join(BLOGS, filename)
    if not filename.endswith(".md") or not os.path.exists(path):
        abort(404)
    with open(path, "r", encoding="UTF-8") as f:
        html_content = markdown.markdown(f.read())
    return render_template("blog_post.html", content=html_content, title=post_meta(filename)["title"])


if __name__ == "__main__":
    app.run()
