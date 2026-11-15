import pytest

import app as appmod

POST = {"slug": "a-retro", "path": "ICPC-2025/a-retro.md", "title": "A", "date": "", "sort_key": "",
        "event": "ICPC-2025", "source_url": "u", "markdown": ""}
OTHER = dict(POST, slug="b-over", path="ICPC-2025/b-over.md")


def render(md):
    return appmod.render_post(dict(POST, markdown=md))


@pytest.fixture
def cache(monkeypatch):
    def setup(writeups=(), repos=()):
        monkeypatch.setattr(appmod, "cached",
                            lambda name: list(writeups) if name == "writeups.json" else list(repos))
    return setup


def test_image_and_link_rewriting(cache):
    cache([POST, OTHER])
    html = render("![x](img/a.png)\n\n[o](b-over.md)\n\n[f](scripts/run.sh)\n\n"
                  "[up](../README.md)\n\n[abs](https://example.com/a)\n\n![r](https://example.com/i.png)")
    assert 'src="https://raw.githubusercontent.com/SketchyRock/writeups/HEAD/ICPC-2025/img/a.png"' in html
    assert 'href="/blog/b-over"' in html
    assert 'href="https://github.com/SketchyRock/writeups/blob/HEAD/ICPC-2025/scripts/run.sh"' in html
    assert 'href="/blog"' in html
    assert 'href="https://example.com/a"' in html
    assert 'src="https://example.com/i.png"' in html


def test_h1_kept(cache):
    cache([POST])
    assert "<h1>Title</h1>" in render("# Title\n\ntext")


def test_post_order(cache):
    ws = [dict(POST, slug="u", title="Zed", sort_key=""), dict(POST, slug="o", title="Old", sort_key="2025-01-01"),
          dict(POST, slug="n", title="New", sort_key="2026-01-01"), dict(POST, slug="a", title="Alpha", sort_key="")]
    cache(ws)
    assert [p["slug"] for p in appmod.post_list()] == ["n", "o", "a", "u"]


def test_competition_post_none_when_missing(cache):
    cache([POST])
    comps = appmod.competition_list()
    assert all(c["post"] is None or c["post"] == "a-retro" for c in comps)
    assert any(c["post"] is None for c in comps)


def test_projects_merge(cache):
    repos = [
        {"name": "Gvoid", "html_url": "https://github.com/SketchyRock/Gvoid", "description": "d",
         "language": "JavaScript", "pushed_at": "2026-02-03T00:00:00Z", "archived": True, "stargazers_count": 0},
        {"name": "newer", "html_url": "https://github.com/SketchyRock/newer", "description": "new",
         "language": "Go", "pushed_at": "2026-05-01T00:00:00Z", "archived": False, "stargazers_count": 0},
        {"name": "older", "html_url": "https://github.com/SketchyRock/older", "description": None,
         "language": None, "pushed_at": "2025-01-01T00:00:00Z", "archived": False, "stargazers_count": 0},
    ]
    cache([], repos)
    ps = appmod.project_list()
    names = [p["name"] for p in ps]
    curated = [p["name"] for p in appmod.load("projects.json")]
    assert names[:len(curated)] == curated
    assert names[len(curated):] == ["newer", "older"]
    g = next(p for p in ps if p["name"] == "Gvoid")
    assert (g["status"], g["language"], g["updated"], g["live"]) == ("archived", "JavaScript", "Feb 2026", True)
    assert next(p for p in ps if p["name"] == "newer")["stack"] == ["Go"]
    assert next(p for p in ps if p["name"] == "older")["stack"] == []
    assert len(set(p["repo"] or p["name"] for p in ps)) == len(ps)
    assert all(p["status"] == "private" for p in ps if p["repo"] is None)


@pytest.mark.parametrize("url", ["/", "/about", "/competitions", "/projects", "/blog", "/photos"])
def test_pages_ok(url):
    assert appmod.app.test_client().get(url).status_code == 200


def test_all_cached_posts_ok():
    c = appmod.app.test_client()
    posts = appmod.cached("writeups.json")
    assert len(posts) >= 1
    for p in posts:
        assert c.get(f"/blog/{p['slug']}").status_code == 200


def test_unknown_slug_404():
    r = appmod.app.test_client().get("/blog/nope")
    assert r.status_code == 404


def test_photos_grouping(monkeypatch):
    data = [{"file": "a", "album": "Trip One", "alt": "x", "caption": "", "width": 8, "height": 6},
            {"file": "b", "album": "Home", "alt": "", "caption": "", "width": 8, "height": 6},
            {"file": "c", "album": "Trip One", "alt": "", "caption": "", "width": 8, "height": 6}]
    monkeypatch.setattr(appmod, "load", lambda name, default=None, folder=None: data)
    albums, flat = appmod.photo_albums()
    assert [a["name"] for a in albums] == ["Trip One", "Home"]
    assert albums[0]["slug"] == "trip-one" and len(albums[0]["photos"]) == 2
    assert albums[0]["photos"][0]["src"] == "/static/photos/a-800.webp"
    assert len(flat) == 3
