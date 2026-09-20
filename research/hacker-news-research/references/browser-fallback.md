# Browser-only HN pipeline

Use when terminal/curl is unavailable (approval-gated interactive session, cron job
without the terminal toolset). Everything below ran successfully end-to-end on the
DeepSeek Harness 0813 digest: discovery → comments → primary sources.

## 1. Discovery: Algolia via browser_navigate

Navigate directly to the API URL — the JSON renders as page text:

    https://hn.algolia.com/api/v1/search_by_date?query=KEYWORDS&tags=story&hitsPerPage=12

Then extract in browser_console:

    (() => { const d = JSON.parse(document.body.innerText);
      return d.hits.map(h => ({id: h.objectID, at: h.created_at, title: h.title,
        url: h.url, pts: h.points, comments: h.num_comments, author: h.author,
        text: (h.story_text||'').slice(0,300)})); })()

- `search_by_date` surfaces the cluster of dupe/spinoff submissions around a big
  release; the real thread is the one with ~100x the points.
- `story_text` often carries the submitter's primary links (GitHub repo, docs).

## 2. Story + top-level comment IDs

Algolia items API (works in console):

    fetch('https://hn.algolia.com/api/v1/items/<id>').then(r=>r.json())
      .then(d=>({title:d.title, url:d.url, points:d.points, text:d.text, kids:d.kids}))

`kids` = top-level comment IDs. The Firebase item endpoint works equally well and
additionally returns `descendants` (total comment count).

## 3. Comments via parallel fetch (replaces Step 3's Python)

    (async () => { const kids = [/* top-level IDs */];
      const items = await Promise.all(kids.map(id =>
        fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`)
          .then(r=>r.json()).catch(()=>null)));
      const clean = t => { if(!t) return ''; const div = document.createElement('div');
        div.innerHTML = t; return div.textContent.replace(/\s+/g,' ').trim(); };
      const rows = items.filter(i=>i && i.type==='comment')
        .map(i=>({score: i.score||0, by: i.by, n_kids: (i.kids||[]).length,
                  id: i.id, text: clean(i.text)}));
      rows.sort((a,b)=>(b.score-a.score)||(b.n_kids-a.n_kids));
      return rows.map(r=>({s:r.score, by:r.by, k:r.n_kids, id:r.id,
                           t:r.text.slice(0,900)})); })()

If every score is 0 (see SKILL.md Step 3 pitfall), sort by `n_kids` alone.

## 4. Subthread expansion (quote material)

Fetch replies of the top ~5 highest-reply top-level comments:

    const parents = await Promise.all(ids.map(id =>
      fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`).then(r=>r.json())));
    const kids = parents.flatMap(p => (p.kids||[]).slice(0,6));
    // fetch those kids the same way, group by i.parent, clean() the text

This is where the digest's best named-user quotes usually live.

## 5. Primary sources

- **GitHub repo metadata**: `fetch('https://api.github.com/repos/<org>/<repo>')` →
  `default_branch` (never assume `main`!), stars, forks, license, created_at.
  Then fetch README/docs from `raw.githubusercontent.com/<org>/<repo>/<branch>/...`.
  Docs trees are guessable from README links; 404s are cheap — try variants.
- **Landing pages**: `browser_navigate` directly. Cross-origin `fetch()` from an
  HN/API page often fails with `TypeError: Failed to fetch` — don't burn time on it.
- **Tweets**: navigate `https://xcancel.com/<user>/status/<id>`; the snapshot
  includes the tweet body plus replies with like/repost/view counts. Occasionally
  hits a "Checking your browser" wall — retry once, otherwise note and move on.
