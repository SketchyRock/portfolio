"""Pull public repos and allowlisted writeups from GitHub into data/cache/.

Stdlib only. Run at build time. Failures keep the existing cache.
"""
import datetime
import fnmatch
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
CACHE = os.path.join(DATA, "cache")
TIMEOUT = 15
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class SyncError(Exception):
    pass


def config():
    with open(os.path.join(DATA, "github.json"), encoding="UTF-8") as f:
        cfg = json.load(f)
    cfg.setdefault("include", ["**/*retrospective*.md", "**/*overview*.md"])
    cfg.setdefault("hide_repos", [])
    return cfg


def fetch(url, api=False):
    """GET with timeout and one retry. Returns bytes."""
    headers = {"User-Agent": "portfolio-sync"}
    token = os.environ.get("GITHUB_TOKEN")
    if api:
        headers["Accept"] = "application/vnd.github+json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
    last = None
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read()
        except (urllib.error.URLError, OSError) as e:
            last = e
    raise SyncError(f"{url}: {last}")


def fetch_json(url):
    return json.loads(fetch(url, api=True))


def read_cache(name):
    try:
        with open(os.path.join(CACHE, name), encoding="UTF-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_cache(name, data):
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, name), "w", encoding="UTF-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


# ---------- repos ----------

def clean_repos(raw, hide):
    hide = {h.lower() for h in hide}
    out = []
    for r in raw:
        if r.get("fork") or r["name"].lower() in hide:
            continue
        out.append({
            "name": r["name"],
            "html_url": r["html_url"],
            "description": r.get("description"),
            "language": r.get("language"),
            "pushed_at": r.get("pushed_at"),
            "archived": bool(r.get("archived")),
            "stargazers_count": r.get("stargazers_count", 0),
        })
    return out


def sync_repos():
    cfg = config()
    url = f"https://api.github.com/users/{cfg['user']}/repos?per_page=100&type=owner"
    repos = clean_repos(fetch_json(url), cfg["hide_repos"])
    write_cache("repos.json", repos)
    return repos


# ---------- writeups ----------

def glob_to_re(pattern):
    """Glob where ** crosses folders (and may match zero), * and ? stay inside one segment."""
    i, out = 0, ""
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$", re.I)


def is_allowed(path, patterns):
    if not path.lower().endswith(".md"):
        return False
    return any(glob_to_re(p).match(path) for p in patterns)


def is_draft(text):
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m and re.search(r"^draft:\s*true\s*$", m.group(1), re.M | re.I):
        return True
    return bool(re.search(r"<!--\s*draft\s*-->", text, re.I))


def slug_for(path):
    return os.path.splitext(os.path.basename(path))[0].lower()


def assign_slugs(paths):
    """Filename stem; on collision prefix with the parent folder."""
    stems = [slug_for(p) for p in paths]
    out = {}
    for p, s in zip(paths, stems):
        if stems.count(s) > 1:
            parent = os.path.basename(os.path.dirname(p)).lower()
            s = f"{parent}-{s}" if parent else s
        out[p] = s
    return out


def get_title(text, path):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return slug_for(path).replace("-", " ").title()


def parse_date(text):
    """Return (date_raw, display, sort_key) from a '**Date:** m/d/yyyy' line."""
    m = re.search(r"^\*\*Date:\*\*\s*(.+?)\s*$", text, re.M)
    if not m:
        return "", "", ""
    raw = m.group(1)
    d = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if d:
        try:
            dt = datetime.date(int(d.group(3)), int(d.group(1)), int(d.group(2)))
            return raw, f"{MONTHS[dt.month - 1]} {dt.year}", dt.isoformat()
        except ValueError:
            pass
    return raw, "", ""


def parse_month_year(s):
    """'Jan 2026' -> '2026-01-01', else ''."""
    m = re.match(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{4})$", (s or "").strip())
    if m and m.group(1).title() in MONTHS:
        return f"{m.group(2)}-{MONTHS.index(m.group(1).title()) + 1:02d}-01"
    return ""


def build_writeup(path, slug, text, competitions):
    raw, display, key = parse_date(text)
    if not key:
        for c in competitions:
            if c.get("post") == slug and c.get("date"):
                display, key = c["date"], parse_month_year(c["date"])
                break
    parent = os.path.dirname(path)
    return {
        "slug": slug,
        "path": path,
        "title": get_title(text, path),
        "date_raw": raw,
        "date": display,
        "sort_key": key,
        "event": os.path.basename(parent) if parent else "",
        "source_url": f"https://github.com/SketchyRock/writeups/blob/HEAD/{path}",
        "markdown": text,
    }


def build_writeups(tree, fetch_text, include, competitions):
    paths = sorted(t["path"] for t in tree
                   if t.get("type") == "blob" and is_allowed(t["path"], include))
    texts = {}
    for p in paths:
        text = fetch_text(p)
        if not text.strip() or is_draft(text):
            continue
        texts[p] = text
    slugs = assign_slugs(list(texts))
    return [build_writeup(p, slugs[p], texts[p], competitions) for p in texts]


def sync_writeups():
    cfg = config()
    repo = f"{cfg['user']}/{cfg['writeups_repo']}"
    tree = fetch_json(f"https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1")
    if tree.get("truncated"):
        raise SyncError("writeups tree was truncated")
    with open(os.path.join(DATA, "competitions.json"), encoding="UTF-8") as f:
        comps = json.load(f)

    def fetch_text(path):
        quoted = urllib.request.quote(path)
        return fetch(f"https://raw.githubusercontent.com/{repo}/HEAD/{quoted}").decode("utf-8")

    posts = build_writeups(tree.get("tree", []), fetch_text, cfg["include"], comps)
    write_cache("writeups.json", posts)
    return posts


# ---------- entry ----------

def run(offline=False):
    """Sync both caches. Returns True if everything is fresh. Exits if a cache is missing and sync failed."""
    if offline:
        print("sync: offline, using data/cache as is")
        return False
    ok = True
    for name, fn, label in (("repos.json", sync_repos, "repos"),
                            ("writeups.json", sync_writeups, "writeups")):
        try:
            print(f"sync: {len(fn())} {label}")
        except (SyncError, ValueError, KeyError) as e:
            ok = False
            print(f"WARNING: {label} sync failed ({e}); keeping existing cache", file=sys.stderr)
            if not os.path.exists(os.path.join(CACHE, name)):
                sys.exit(f"ERROR: {label} sync failed and data/cache/{name} does not exist")
    return ok


if __name__ == "__main__":
    run()
