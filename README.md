# portfolio

Source for my personal site at https://portfolio.idalia.dev. It is a small Flask app that `build.py` renders to plain HTML files in `dist/`, which GitHub Pages serves.

## What feeds the site

- `data/profile.json` and `data/photos.json` hold the copy for Home, About and Photos.
- Competitions and Projects come only from GitHub. `sync.py` lists my public repos (name, link and About text) and reads the `retrospective` and `project-writeup` documents (by the `type` in their front matter) from [SketchyRock/writeups](https://github.com/SketchyRock/writeups), under the year folders. Filters are in `data/github.json`.
- The results are cached in `data/cache/`. If GitHub cannot be reached, or returns nothing, the build keeps the cached copy.

## Deploys

`.github/workflows/pages.yml` builds and deploys on every push to `main`, once a day at 09:17 UTC, and on demand from the Actions tab. The daily run is what picks up new write-ups, so nothing needs doing after pushing one to the writeups repo. GitHub pauses scheduled workflows after 60 days without repository activity; a push or a manual run turns them back on.

`SITE_BASE` is a repository variable that sets the URL prefix. It is `/` for the custom domain. Leave it unset only for a build served from `/portfolio/`.

## Working on it

```sh
pip install -r requirements-dev.txt
python build.py --offline     # use data/cache as is
python build.py               # sync from GitHub first; GITHUB_TOKEN is optional
pytest
```

`SITE_BASE=/portfolio python build.py` builds for a subpath. `flask --app app run` serves the live app for quick edits.

Photos: put originals in `photos/<album>/` (git-ignored), run `python photos.py`, then fill in alt text and captions in `data/photos.json`. The Photos link stays hidden until the list is not empty.
