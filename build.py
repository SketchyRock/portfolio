"""Sync GitHub content, then render the Flask site to static files in dist/.

    python build.py            sync from GitHub first
    python build.py --offline  use data/cache as is (also PORTFOLIO_OFFLINE=1)

Set SITE_BASE=/portfolio to build for a subpath (GitHub Pages project site).
Leave it unset, or set it to /, for a root deploy (custom domain).
"""
import os
import shutil
import sys

import sync
from app import app, all_writeups, BASE

OUT = os.path.join(BASE, "dist")

PAGES = {
    "/": "index.html",
    "/about": "about.html",
    "/competitions": "competitions.html",
    "/projects": "projects.html",
    "/photos": "photos.html",
}


def write(path, body):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(body)


def main():
    offline = "--offline" in sys.argv or os.environ.get("PORTFOLIO_OFFLINE") == "1"
    sync.run(offline=offline)
    shutil.rmtree(OUT, ignore_errors=True)
    base = os.environ.get("SITE_BASE", "").rstrip("/")
    client = app.test_client()
    root = f"http://localhost{base}/"
    routes = dict(PAGES)
    posts = all_writeups()
    for post in posts:
        routes[f"/competitions/{post['slug']}"] = f"competitions/{post['slug']}.html"
    for url, path in routes.items():
        r = client.get(url, base_url=root)
        assert r.status_code == 200, f"{url} -> {r.status_code}"
        write(path, r.data)
    write("404.html", client.get("/does-not-exist", base_url=root).data)
    shutil.copytree(os.path.join(BASE, "static"), os.path.join(OUT, "static"))
    print(f"built {len(routes) + 1} pages ({len(posts)} posts) into {OUT}")


if __name__ == "__main__":
    main()
