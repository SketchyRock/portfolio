# portfolio

Source for my personal portfolio site, built with Flask. Projects come from a JSON file and blog posts from Markdown files, so adding either does not mean touching the code.

**Live site:** coming soon. I'm moving it to a new domain.

## How it works

- **Projects.** The homepage cards are rendered from `data/projects.json`.
- **Blog.** Every `.md` file in `data/blogs/` becomes a post. The file name is turned into the title, so `my-new-post.md` is shown as "My New Post". Prefix the name with a date (`2026-1-30-my-new-post.md`) so posts sort newest first.
- **Templates.** Jinja2 templates share a `base.html` layout, and the CSS uses variables in `:root` for theming and mobile layouts.

## Stack

Python 3, Flask, Python-Markdown, and Gunicorn for production. The frontend is plain HTML and CSS.

## Layout

```text
├── app.py                # Flask app and routes
├── data/
│   ├── blogs/            # Markdown posts
│   └── projects.json     # Project cards
├── static/
│   ├── css/              # Stylesheets
│   └── img/              # Icons
├── templates/            # base, index, blog list, blog post
└── requirements.txt
```

## Running locally

```bash
git clone https://github.com/SketchyRock/portfolio.git
cd portfolio

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

The site is served at `http://127.0.0.1:5000`.

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

`icon` is a file in `static/img/`. If it is missing, the card shows no icon.

## Roadmap

- Pull posts from the [writeups](https://github.com/SketchyRock/writeups) repo through the GitHub API instead of keeping local copies in `data/blogs/`.
- Fix the spacing on the blog list page.
