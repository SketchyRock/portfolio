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

def _date_key(date, day_source=""):
    """(year, month, day) from a 'Nov 2026' label, with the day taken from an ISO date if given."""
    try:
        d = datetime.datetime.strptime(date, "%b %Y")
    except (TypeError, ValueError):
        return (0, 0, 0)
    day = int(day_source[8:10]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day_source or "") else 0
    return (d.year, d.month, day)


def competition_list():
    """Every competition, newest first. Curated rows come from competitions.json; any write-up
    not referenced there gets a row of its own, so a write-up is never hidden."""
    posts = {p["slug"]: p for p in all_writeups()}
    out, used = [], set()
    for c in load("competitions.json"):
        c = dict(c)
        c["post"] = c.get("post") if c.get("post") in posts else None
        c["also"] = [{"slug": s, "title": posts[s]["title"]} for s in c.get("also", []) if s in posts]
        used.update(x for x in [c["post"], *[a["slug"] for a in c["also"]]] if x)
        c["_key"] = _date_key(c["date"], posts[c["post"]]["sort_key"] if c["post"] else "")
        out.append(c)
    for slug, p in posts.items():
        if slug not in used:
            out.append({"date": p["date"], "type": None, "event": p["title"], "result": "", "note": "",
                        "post": slug, "also": [], "_key": _date_key(p["date"], p["sort_key"])})
    out.sort(key=lambda c: c["_key"], reverse=True)
    return out


def month_year(iso):
    try:
        d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return d.strftime("%b %Y")


def repo_name(url):
    return url.rstrip("/").split("/")[-1].lower() if url else None


def project_list():
    repos = cached("repos.json")
    by_name = {r["name"].lower(): r for r in repos}
    used = set()
    out = []
    for p in load("projects.json"):
        r = by_name.get(repo_name(p.get("repo")))
        entry = {
            "name": p["name"],
            "description": p.get("description", ""),
            "stack": list(p.get("stack", [])),
            "repo": p.get("repo"),
            "status": "public" if p.get("repo") else "private",
            "language": None,
            "updated": None,
            "live": False,
        }
        if r:
            used.add(r["name"].lower())
            entry["status"] = "archived" if r["archived"] else "public"
            entry["language"] = r["language"]
            entry["updated"] = month_year(r["pushed_at"])
            entry["live"] = True
        out.append(entry)
    rest = [r for r in repos if r["name"].lower() not in used]
    rest.sort(key=lambda r: r["pushed_at"] or "", reverse=True)
    for r in rest:
        out.append({
            "name": r["name"],
            "description": r["description"] or "",
            "stack": [r["language"]] if r["language"] else [],
            "repo": r["html_url"],
            "status": "archived" if r["archived"] else "public",
            "language": r["language"],
            "updated": month_year(r["pushed_at"]),
            "live": True,
        })
    return out


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
