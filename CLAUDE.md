# Portfolio

Flask site rendered to static HTML for Vercel (home, about, competitions, projects, writeups, photos). Copy lives in `data/*.json`. Writeups and public repos come from GitHub via `sync.py` into `data/cache/`; the old `data/blogs/*.md` files are no longer used. Build with `python build.py` (add `--offline` to skip the GitHub fetch; `GITHUB_TOKEN` is optional and only avoids the API rate limit), test with `pytest` after `pip install -r requirements-dev.txt`. Photos: put originals in `photos/<album>/` (git-ignored) and run `python photos.py`. Repo and writeup filters are in `data/github.json`. The daily GitHub Action only calls a Vercel deploy hook, so the rebuild and sync happen on Vercel.

Docs and research: `~/Documents/Obsidian Vault/Claude/Projects/portfolio/`. Do not add docs to this repo.

Status: redesign built on local branch `redesign` (uncommitted as of 2026-11-10), static build for Vercel. Start with `Status.md` in the vault folder.
