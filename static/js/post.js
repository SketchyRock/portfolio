// Fetches one write-up from the writeups repo and renders its Markdown.
const WRITEUPS = "https://raw.githubusercontent.com/SketchyRock/writeups/main/";

(async function () {
    const target = document.getElementById("post");
    const path = new URLSearchParams(location.search).get("p") || "";
    if (!/^20\d\d\/[a-z0-9-]+\.md$/.test(path)) {
        target.textContent = "Post not found.";
        return;
    }
    try {
        const res = await fetch(WRITEUPS + path);
        if (!res.ok) throw new Error(res.status);
        let md = await res.text();
        md = md.replace(/^---\n[\s\S]*?\n---\n/, ""); // front matter
        md = md.replace(/^\[← All write-ups\]\(\.\.\/README\.md\)\n/m, ""); // repo-only link
        target.innerHTML = marked.parse(md);
        const h1 = target.querySelector("h1");
        if (h1) document.title = h1.textContent + " - Enzo Hins";
    } catch (err) {
        target.textContent = "Could not load this post.";
    }
})();
