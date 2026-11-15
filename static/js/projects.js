// Renders the project cards on the homepage from data/projects.json.
(async function () {
    const grid = document.getElementById("projects-grid");
    try {
        const res = await fetch("data/projects.json");
        if (!res.ok) throw new Error(res.status);
        const projects = await res.json();
        grid.replaceChildren(...projects.map(card));
    } catch (err) {
        grid.textContent = "Could not load projects. They are listed at github.com/SketchyRock.";
    }

    function card(p) {
        const a = el("a", "project-card");
        a.href = p.repo;
        a.target = "_blank";
        a.rel = "noopener";

        const header = el("div", "card-header");
        const icon = el("img", "project-icon");
        icon.src = "static/img/" + p.icon;
        icon.alt = "";
        header.append(icon, text("h3", p.name));

        const tags = el("div", "tag-container");
        tags.append(...p.learned.map((t) => text("span", t, "tech-tag")));

        a.append(header, text("p", p.description.trim(), "project-desc"), tags, text("span", "View Repository →", "repo-cta"));
        return a;
    }
    function el(tag, cls) {
        const e = document.createElement(tag);
        e.className = cls;
        return e;
    }
    function text(tag, str, cls) {
        const e = document.createElement(tag);
        e.textContent = str;
        if (cls) e.className = cls;
        return e;
    }
})();
