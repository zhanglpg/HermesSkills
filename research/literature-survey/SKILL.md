---
name: literature-survey
description: Multi-source literature surveys on technical topics — combining arxiv web search, lab blogs, citation cross-referencing, and structured synthesis. Use when the user asks to "search for papers on X", "what's the state of research on Y", or "find papers about Z from labs A, B, C".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Research, Literature-Survey, Papers, Synthesis]
    related_skills: [arxiv, breaking-news-research-essay]
---

# Literature Survey / Research Reconnaissance

Conduct structured multi-source literature surveys on technical topics. Combines arxiv search, lab blog scanning, citation following, and synthesis into a comprehensive report.

## When to Use

- "Search for papers on X" / "What's the state of research on Y"
- "Find work from [specific lab] on [topic]"
- "What's the relationship between technique A and technique B"
- "Is X being used as replacement for Y or alongside it?"
- Any request requiring coverage across multiple sources and labs

## Workflow

### Phase 1: Broad Discovery (arxiv web search)

Use **browser-based arxiv search** for exploratory multi-concept queries — far more practical than the API for complex boolean combinations:

```
browser_navigate(url="https://arxiv.org/search/?query=%22exact+phrase%22+concept2&searchtype=all")
```

- URL-encode exact phrases as `%22...%22`
- Combine with `+` (AND) or `+OR+`
- Results show titles, authors, abstracts, dates inline
- Use `read_file` on the truncated snapshot path to see all results
- Sort by announcement date (newest first) for recent work

**Run multiple searches in parallel** with different query formulations:
- `"exact phrase" + related_concept`
- `"exact phrase" + specific_lab_or_model_name`
- `broader_term + narrower_term`

### Phase 2: Lab Blog Scanning

Some labs publish primarily via blogs, NOT arxiv. Always check relevant lab blogs:

| Lab | Blog URL | Notes |
|-----|----------|-------|
| Thinking Machines (Mira Murati) | thinkingmachines.ai/blog | Technical posts, no arxiv papers |
| OpenAI | openai.com/research | Mix of blog + arxiv |
| Anthropic | anthropic.com/research | Mix of blog + arxiv |
| Google DeepMind | deepmind.google/research | Mostly arxiv |
| Meta FAIR | ai.meta.com/research | Mostly arxiv |
| Alibaba/Qwen | qwenlm.github.io | Tech reports on arxiv |
| DeepSeek | api-docs.deepseek.com | Papers on arxiv |

### Phase 3: Deep Reading

For key papers found in Phase 1-2:

```
# Full abstract + metadata
browser_navigate(url="https://arxiv.org/abs/XXXX.XXXXX")
browser_snapshot(full=true)

# Quick title verification (no browser needed)
curl -s "https://arxiv.org/abs/XXXX.XXXXX" | grep -o '<meta name="citation_title" content="[^"]*"'
```

For blog posts: navigate and use `browser_snapshot(full=true)`, then `read_file` on the snapshot for long content.

### Phase 4: Citation Cross-Referencing

Follow citations from blog posts and papers to discover foundational works:
- Blog post references → foundational arxiv papers
- Paper "Related Work" sections → competing approaches
- Use Semantic Scholar for citation graphs: `curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID/references?fields=title,citationCount&limit=20"`

### Phase 5: Synthesis

Structure the output as:
1. **Foundational paper** (origin of the technique)
2. **Key lab contributions** (who uses it and how)
3. **Technical formulations** (loss functions, algorithms)
4. **Relationship to related techniques** (complementary vs replacement)
5. **Paper table** (title, arxiv ID, date, key contribution)
6. **Quantitative results** where available

## Pitfalls

- **Don't rely on arxiv alone** — some of the most influential work (e.g., Thinking Machines OPD post) is blog-only
- **Search with multiple formulations** — "on-policy distillation" vs "OPD" vs "on-policy knowledge distillation" return different results
- **Check the truncated snapshot file** — arxiv search results often exceed the browser snapshot limit; use `read_file` on the saved path
- **Verify paper IDs** — arxiv IDs from search results can point to unrelated papers; always confirm title matches
- **Distinguish off-policy vs on-policy** — labs may use "distillation" generically; check if it's truly on-policy (student-generated rollouts) or off-policy (teacher-generated SFT data)
- **macOS grep lacks -P flag** — use `grep -o` with basic patterns or `python3 -c` for complex extraction

## Parallelization Strategy

Independent searches should be batched:
- Multiple arxiv queries with different formulations → parallel browser sessions
- curl metadata checks for multiple paper IDs → single terminal command with loop
- Lab blog check + arxiv search → parallel (different tools)

Only serialize when: reading a paper found in a previous search, or following a citation chain.
