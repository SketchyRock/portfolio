from flask import Flask, abort, render_template
import datetime
import json
import markdown
import os
import posixpath
import re
from urllib.parse import urlsplit, quote

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
CACHE = os.path.join(DATA, "cache")

RAW = "https://raw.githubusercontent.com/SketchyRock/writeups/HEAD/"
BLOB = "https://github.com/SketchyRock/writeups/blob/HEAD/"

app = Flask(__name__)


def load(name, default=None, folder=DATA):
    try:
        with open(os.path.join(folder, name), "r", encoding="UTF-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is None:
            raise
        return default


def cached(name):
    return load(name, default=[], folder=CACHE)


@app.context_processor
def inject_globals():
    return {"has_photos": bool(load("photos.json", default=[])), "year": datetime.date.today().year}


# ---------- posts ----------

def all_writeups():
    return cached("writeups.json")


def rewrite_links(html, post, slugs_by_path):
    """Make relative image and link targets work from the site instead of the repo."""
    folder = posixpath.dirname(post["path"])

    def resolve(target):
        return posixpath.normpath(posixpath.join(folder, target))

    def is_relative(url):
        u = urlsplit(url)
        return not (u.scheme or u.netloc or url.startswith(("/", "#")))

    def img(m):
        src = m.group(2)
        if is_relative(src):
            src = RAW + quote(resolve(urlsplit(src).path))
        return f'{m.group(1)}{src}"'

    def link(m):
        href = m.group(2)
        if is_relative(href):
            u = urlsplit(href)
            path = resolve(u.path)
            if path == "README.md":
                href = "/competitions"
            elif path in slugs_by_path:
                href = "/competitions/" + slugs_by_path[path]
            else:
                href = BLOB + quote(path)
            if u.fragment:
                href += "#" + u.fragment
        return f'{m.group(1)}{href}"'

    html = re.sub(r'(<img\b[^>]*?\bsrc=")([^"]*)"', img, html)
    return re.sub(r'(<a\b[^>]*?\bhref=")([^"]*)"', link, html)


def render_post(post):
    html = markdown.markdown(post["markdown"], extensions=["extra", "sane_lists"])
    slugs_by_path = {p["path"]: p["slug"] for p in all_writeups()}
    return rewrite_links(html, post, slugs_by_path)


# ---------- competitions and projects ----------

def competition_list():
    """Every retrospective in the writeups repo, newest first. Other document types (project
    write-ups) still render at /competitions/<slug> but are not listed."""
    posts = [p for p in all_writeups() if p.get("type", "retrospective") == "retrospective"]
    return sorted(posts, key=lambda p: p.get("sort_key") or "", reverse=True)


def project_list():
    """Public repos from the GitHub cache, most recently pushed first."""
    repos = sorted(cached("repos.json"), key=lambda r: r.get("pushed_at") or "", reverse=True)
    return [{"name": r["name"], "description": r.get("description") or "", "repo": r["html_url"]} for r in repos]


# ---------- photos ----------

def photo_albums():
    albums, flat = {}, []
    for p in load("photos.json", default=[]):
        photo = {
            "src": f"/static/photos/{p['file']}-800.webp",
            "src_large": f"/static/photos/{p['file']}-1600.webp",
            "width": p.get("width"),
            "height": p.get("height"),
            "alt": p.get("alt", ""),
            "caption": p.get("caption", ""),
        }
        name = p.get("album", "")
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        albums.setdefault(name, {"name": name, "slug": slug, "photos": []})["photos"].append(photo)
        flat.append(photo)
    return list(albums.values()), flat


# ---------- routes ----------

@app.route("/")
def home():
    return render_template(
        "index.html",
        profile=load("profile.json"),
        competitions=competition_list(),
        projects=project_list(),
    )


@app.route("/about")
def about():
    return render_template("about.html", profile=load("profile.json"))


@app.route("/competitions")
def competitions():
    return render_template("competitions.html", competitions=competition_list())


@app.route("/projects")
def projects():
    return render_template("projects.html", projects=project_list())


@app.route("/competitions/<slug>")
def competition_post(slug):
    post = next((p for p in all_writeups() if p["slug"] == slug), None)
    if post is None:
        abort(404)
    meta = {k: v for k, v in post.items() if k != "markdown"}
    return render_template("competition_post.html", post=meta, title=post["title"], content=render_post(post))


@app.route("/photos")
def photos():
    albums, flat = photo_albums()
    return render_template("photos.html", albums=albums, photos=flat)


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run()
