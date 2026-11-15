# portfolio

My personal portfolio site. It is a static frontend: plain HTML, CSS, and a little JavaScript, with nothing to run on a server.

**Live site:** coming soon. I'm moving it to a new domain.

## How it works

- **Projects.** `static/js/projects.js` builds the homepage cards from `data/projects.json`.
- **Blog.** `static/js/blog.js` lists the posts in my [writeups](https://github.com/SketchyRock/writeups) repo using its `index.json`, and `static/js/post.js` fetches and renders one post. Nothing is copied into this repo, so a new write-up shows up as soon as it is on `main` there.
- **Markdown** is rendered in the browser with a vendored copy of [marked](https://github.com/markedjs/marked) (`static/js/marked.min.js`).

## Layout

```text
├── index.html            # Home: hero, about, projects
├── blog.html             # Post list
├── post.html             # One post (post.html?p=2026/some-post.md)
├── data/projects.json    # Project cards
└── static/
    ├── css/styles.css
    ├── img/              # Icons
    └── js/               # projects.js, blog.js, post.js, marked.min.js
```

## Running locally

Browsers block `fetch` on `file://` pages, so serve the folder:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Deploying

Upload the repo as is to any static host (GitHub Pages, Netlify, Vercel, Cloudflare Pages). There is no build step.

## Adding a project

Append an object to `data/projects.json`:

```json
{
    "name": "Project Name",
    "description": "One or two sentences.",
    "icon": "icon-name.svg",
    "learned": ["Skill 1", "Skill 2"],
    "repo": "https://github.com/SketchyRock/project-name"
}
```

`icon` is a file in `static/img/`.
