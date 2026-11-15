// Lists the posts in the writeups repo, newest first, using its index.json.
const WRITEUPS = "https://raw.githubusercontent.com/SketchyRock/writeups/main/";

(async function () {
    const list = document.getElementById("blog-list");
    try {
        const res = await fetch(WRITEUPS + "index.json");
        if (!res.ok) throw new Error(res.status);
        const docs = (await res.json()).filter((d) => d.type !== "reference");
        list.replaceChildren(...docs.map(item));
    } catch (err) {
        list.textContent = "Could not load posts. They are all in the writeups repo on GitHub.";
    }

    function item(d) {
        const wrap = document.createElement("div");
        wrap.className = "blog-item";
        const a = document.createElement("a");
        a.href = "post.html?p=" + encodeURIComponent(d.path);
        const h3 = document.createElement("h3");
        h3.textContent = d.title;
        const span = document.createElement("span");
        span.textContent = [d.result, "Read →"].filter(Boolean).join("  ·  ");
        a.append(h3, span);
        wrap.append(a);
        return wrap;
    }
})();
