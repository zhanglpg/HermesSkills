#!/usr/bin/env python3
"""Fetch arXiv papers from pastweek pages. Iterates categories, parses DT/DD pairs with
h3 date headings, applies keyword filtering for cs.LG/cs.SE, outputs JSON.
Usage: python3 fetch_arxiv.py > /tmp/arxiv_full.json 2>&1
"""
import json, re, ssl, sys, urllib.request

CATEGORIES = ["cs.AI", "cs.LG", "cs.SE"]
CUTOFF_DAYS = 3.5  # ~84 hours for pastweek coverage

KEYWORDS = [
    "llm", "language model", "transformer", "reasoning", "agent",
    "reinforcement learning", "rlhf", "diffusion", "attention",
    "fine-tun", "alignment", "benchmark", "scaling", "multimodal",
    "safety", "hallucin", "generation", "vision", "neural",
    "inference", "quantization", "training", "moe", "mixture of expert",
    "grpo", "reward", "policy", "rl", "gpu", "distributed",
    "kv cache", "speculative", "lora", "adapter", "pretrain",
    "embedding", "rag", "retrieval", "prompt", "chain of thought",
    "tool", "function call", "code generation", "synthetic data",
    "distillation", "pruning", "sparse", "mamba", "state space",
    "long context", "context window", "token", "decoding",
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_category(category):
    url = f"https://arxiv.org/list/{category}/pastweek?show=2000"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=60, context=ctx)
    raw = resp.read().decode("utf-8", errors="replace")

    # Find all <h3> date headings
    h3_pattern = re.compile(r'<h3>((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[^<]*)</h3>')
    dates = h3_pattern.findall(raw)

    # Find all <dl> blocks (one per listing day)
    dl_pattern = re.compile(r'<dl[^>]*>(.*?)</dl>', re.DOTALL)
    dl_blocks = dl_pattern.findall(raw)

    all_papers = []
    for dl_idx, dl_content in enumerate(dl_blocks):
        date_str = dates[dl_idx] if dl_idx < len(dates) else "unknown"

        # Match DT blocks for paper IDs
        dt_pattern = re.compile(r'<dt>.*?arXiv:(\d+\.\d+).*?</dt>', re.DOTALL)
        dts = list(dt_pattern.finditer(dl_content))

        for dt_match in dts:
            paper_id = dt_match.group(1)
            dt_end = dt_match.end()

            # Find following <dd>
            dd_match = re.search(r'<dd>(.*?)</dd>', dl_content[dt_end:], re.DOTALL)
            if not dd_match:
                continue
            dd_text = dd_match.group(1)

            # Extract fields
            title_match = re.search(
                r"class=['\"]list-title[^'\"]*['\"][^>]*>.*?</span>\s*(.*?)\s*</div>",
                dd_text, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1).strip()) if title_match else ""

            authors_match = re.search(
                r"class=['\"]list-authors[^'\"]*['\"][^>]*>(.*?)</div>",
                dd_text, re.DOTALL)
            authors = re.sub(r'<[^>]+>', '', authors_match.group(1).strip()) if authors_match else ""
            authors = re.sub(r'^Authors:\s*', '', authors)

            subjects_match = re.search(
                r"class=['\"]list-subjects[^'\"]*['\"][^>]*>(.*?)</div>",
                dd_text, re.DOTALL)
            subjects = re.sub(r'<[^>]+>', '', subjects_match.group(1).strip()) if subjects_match else ""
            subjects = re.sub(r'^Subjects:\s*', '', subjects)

            comments_match = re.search(
                r"class=['\"]list-comments[^'\"]*['\"][^>]*>(.*?)</div>",
                dd_text, re.DOTALL)
            comments = re.sub(r'<[^>]+>', '', comments_match.group(1).strip()) if comments_match else ""
            comments = re.sub(r'^Comments:\s*', '', comments)

            all_papers.append({
                "id": paper_id, "title": title, "authors": authors,
                "subjects": subjects, "comments": comments, "date": date_str,
            })

    return all_papers, dates

results = {}
for cat in CATEGORIES:
    try:
        papers, dates = fetch_category(cat)
        total = len(papers)
        if cat == "cs.AI":
            filtered = papers[:200]  # cap cs.AI output
        else:
            filtered = []
            for p in papers:
                text = (p["title"] + " " + p.get("subjects", "")).lower()
                score = sum(1 for kw in KEYWORDS if kw in text)
                if score >= 1:
                    p["_score"] = score
                    filtered.append(p)
            filtered.sort(key=lambda x: x.get("_score", 0), reverse=True)
            filtered = filtered[:100]  # cap filtered output
        results[cat] = {
            "total": total, "filtered": len(filtered),
            "dates": dates, "papers": filtered,
        }
    except Exception as e:
        results[cat] = {"error": str(e)[:300]}

print(json.dumps(results, indent=2, ensure_ascii=False))
