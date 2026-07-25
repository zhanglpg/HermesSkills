# GitHub Pages Deployment Patterns

## CDN Caching Pitfall

GitHub Pages uses an aggressive CDN cache. After `git push`, changes may NOT appear immediately — the CDN can serve stale content for minutes to hours, even with cache-busting query params on the initial URL.

### Symptoms
- Browser shows old HTML even after confirmed push
- `curl` shows new content but browser shows old
- Adding `?v=2` to URL doesn't fix it
- React app renders but with stale data / old DOM structure

### Fix Stack (apply all three)

**1. Cache-control meta tags in HTML `<head>`:**
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

**2. Fetch with cache-busting in JS:**
```js
fetch('schoology-data.json?' + Date.now())  // bust JSON data cache
```

**3. Unique URL on initial navigation after deploy:**
```bash
# When navigating immediately after push, use a fresh query param
https://user.github.io/repo/?nocache=<timestamp>
```

### Verification
- Push → wait 5s → `curl -s URL | grep <recent-change>` to confirm server has new content
- Then navigate browser with fresh cache-bust param
- Once verified, subsequent visits (without query params) will pick up new version within ~10 minutes

### When This Matters
- Single-file React apps with separate data JSON
- Dashboard-style pages that update frequently
- Any page where the user expects to see changes within seconds of a push

## Single-File React App Pattern

For GitHub Pages dashboards without a build step:

```html
<!DOCTYPE html>
<html>
<head>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
const { useState, useEffect } = React;
function App() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('data.json?' + Date.now())
      .then(r => r.json())
      .then(setData);
  }, []);
  // ... render
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
</body>
</html>
```

Key points:
- Babel standalone for JSX transpilation (no build step needed)
- `Date.now()` appended to data fetch URL to bypass CDN cache
- Single HTML file → push directly to `docs/` or repo root
- No npm/webpack/vite required — just `git push`
