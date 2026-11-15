# Portfolio

Flask site rendered to static HTML and deployed to GitHub Pages at https://portfolio.idalia.dev (home, about, competitions, projects, photos). Copy lives in `data/*.json`. Public repos and writeups come from GitHub via `sync.py` into `data/cache/`; the Projects page lists every public repo with its GitHub description and link, and `data/projects.json` holds only private projects (no repo); write-ups are picked by the `type` in their front matter (filters in `data/github.json`). Build with `python build.py` (`--offline` skips the GitHub fetch; `GITHUB_TOKEN` is optional and only avoids the rate limit), test with `pytest` after `pip install -r requirements-dev.txt`. `SITE_BASE` (repo variable, `/` in production) sets the URL prefix. `.github/workflows/pages.yml` builds and deploys on push to `main`, daily, and on demand. Photos: originals in `photos/<album>/` (git-ignored), then `python photos.py`. The apex `idalia.dev` is a different site with mail records; only touch the `portfolio` subdomain.

Each write-up is a competition: they render at `/competitions/<slug>` and the Competitions page lists them (extra rows come from `data/competitions.json`, which adds result and note). There is no separate writeups page.

Docs and research: `~/Documents/Obsidian Vault/Claude/Projects/portfolio/`. Do not add docs to this repo.

Status: live; write-ups merged into Competitions (2026-11-15, PR #6); UI restyle open as PR #8 (`ui-refresh`). Work from `main`; `redesign`, `auto-refresh`, `competition-name-links` and `merge-writeups-into-competitions` are merged leftovers (PRs #3 to #6). Start with `Status.md` in the vault folder.
