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
    assert 'href="/competitions/b-over"' in html
    assert 'href="https://github.com/SketchyRock/writeups/blob/HEAD/ICPC-2025/scripts/run.sh"' in html
    assert 'href="/competitions"' in html
    assert 'href="https://example.com/a"' in html
    assert 'src="https://example.com/i.png"' in html


def test_h1_kept(cache):
    cache([POST])
    assert "<h1>Title</h1>" in render("# Title\n\ntext")


def test_competition_list_only_retrospectives_newest_first(cache):
    ws = [dict(POST, slug="old", type="retrospective", sort_key="2025-01-02"),
          dict(POST, slug="new", type="retrospective", sort_key="2026-12-05"),
          dict(POST, slug="tool", type="project-writeup", sort_key="2026-12-31")]
    cache(ws)
    assert [c["slug"] for c in appmod.competition_list()] == ["new", "old"]


def test_competitions_page_lists_names_only(cache):
    cache([dict(POST, slug="new", title="Big CTF", type="retrospective", date="Dec 2026", sort_key="2026-12-05")])
    html = appmod.app.test_client().get("/competitions").get_data(as_text=True)
    assert '<a href="/competitions/new">Big CTF</a>' in html
    assert '<strong class="count">1</strong> event across capture the flag' in html


def test_project_list_sorted_by_name(cache):
    repos = [
        {"name": "zeta", "html_url": "https://github.com/SketchyRock/zeta", "description": None,
         "pushed_at": "2026-05-01T00:00:00Z"},
        {"name": "Gvoid", "html_url": "https://github.com/SketchyRock/Gvoid", "description": "g",
         "pushed_at": "2025-01-01T00:00:00Z"},
        {"name": "echoes", "html_url": "https://github.com/SketchyRock/echoes", "description": "e",
         "pushed_at": "2024-01-01T00:00:00Z"},
    ]
    cache([], repos)
    ps = appmod.project_list()
    assert [p["name"] for p in ps] == ["echoes", "Gvoid", "zeta"]
    assert ps[2] == {"name": "zeta", "description": "", "repo": "https://github.com/SketchyRock/zeta"}


def test_empty_lists_render(cache):
    cache([], [])
    c = appmod.app.test_client()
    assert "No write-ups yet." in c.get("/competitions").get_data(as_text=True)
    assert "No public repos yet." in c.get("/projects").get_data(as_text=True)


@pytest.mark.parametrize("url", ["/", "/about", "/competitions", "/projects", "/photos"])
def test_pages_ok(url):
    assert appmod.app.test_client().get(url).status_code == 200


def test_all_cached_posts_ok():
    c = appmod.app.test_client()
    posts = appmod.cached("writeups.json")
    assert len(posts) >= 1
    for p in posts:
        assert c.get(f"/competitions/{p['slug']}").status_code == 200


def test_old_blog_urls_gone():
    assert appmod.app.test_client().get("/blog").status_code == 404


def test_unknown_slug_404():
    r = appmod.app.test_client().get("/competitions/nope")
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


def test_port_135_page_hidden_from_nav():
    client = appmod.app.test_client()
    html = client.get("/port-135").get_data(as_text=True)
    assert "RPCSS" in html and "img/port-135.png" in html and 'content="noindex"' in html
    home = client.get("/").get_data(as_text=True)
    assert 'href="/port-135"' not in home and '"taskkill"' in home
