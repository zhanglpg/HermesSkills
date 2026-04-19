---
name: de-ai
description: "Remove AI-generated writing patterns from text. Detects and rewrites hedging filler, formulaic transitions, rhetorical crutches, and structural tics that mark text as LLM-produced. Use when polishing essays, papers, or any prose that should read as human-written."
---

# De-AI: Remove LLM Writing Patterns

Strip AI-generated writing tics from essays, papers, and prose. This skill provides a pattern catalog and a rewriting workflow.

## When to Use

- After drafting an essay or paper with an LLM
- Before publishing to arXiv, blog, or gist
- When text "sounds like ChatGPT" and you want it to sound like a person

## The Pattern Catalog

### Category 1: Hedging Filler

Phrases that add nothing. Delete them or rewrite the sentence without them.

| Pattern | Example | Fix |
|---------|---------|-----|
| "It's important to note that..." | "It's important to note that rate limiting was the most damaging." | "Rate limiting was the most damaging." |
| "It's worth mentioning that..." | "It's worth mentioning that costs vary." | "Costs vary." |
| "It should be noted that..." | "It should be noted that this is a limitation." | "This is a limitation." |
| "Interestingly, ..." | "Interestingly, the results diverged." | "The results diverged." |
| "Notably, ..." | "Notably, all platforms converged." | "All platforms converged." |
| "It bears mentioning..." | — | Delete entirely. |
| "As we shall see..." | — | Delete. The reader will see when they get there. |

**Detection regex**: `(?:It(?:'s| is) (?:important|worth|crucial|essential|interesting) to (?:note|mention|highlight|emphasize|point out|observe) that)`

### Category 2: The "Not X, But Y" Crutch

AI models love false-contrast framing. The pattern: "It isn't [strawman], it is [actual point]." This is a rhetorical crutch — just state the actual point.

| Pattern | Example | Fix |
|---------|---------|-----|
| "It isn't X, it is Y" | "The root cause is not model intelligence. It is lifecycle infrastructure." | "The root cause is lifecycle infrastructure." |
| "This is not about X — it's about Y" | "This is not about making models smarter — it's about making execution reliable." | "The challenge is making execution reliable." |
| "Rather than X, we Y" | "Rather than focusing on accuracy, we focus on reliability." | "We focus on reliability." |
| "The question is not X but Y" | — | State Y directly. |

**When to keep it**: Only when the reader genuinely holds the wrong belief and you need to explicitly correct it. If the contrast is rhetorical decoration, cut it.

### Category 3: Formulaic Transitions

Words that signal "I'm an LLM organizing my output into sections."

| Kill | Replace With |
|------|-------------|
| "Furthermore" | Cut, or use "and" |
| "Moreover" | Cut, or restructure so the point follows naturally |
| "Additionally" | Cut |
| "In addition" | Cut |
| "It is also worth noting" | Cut |
| "To that end" | Cut or use "So" |
| "In this regard" | Cut |
| "With that in mind" | Cut |
| "Building on this" | Cut |
| "Taken together" | Cut or use "Together" |
| "As previously mentioned" | Cut. If the reader needs reminding, the structure is wrong. |

**Rule of thumb**: If you can delete the transition word and the paragraph still flows, delete it.

### Category 4: Excessive Adverbs

LLMs over-season with adverbs. Most can be deleted without loss.

| Overused | Action |
|----------|--------|
| "significantly" | Delete, or replace with the actual magnitude |
| "fundamentally" | Delete, or explain *what* is fundamental |
| "remarkably" | Delete |
| "particularly" | Usually delete |
| "essentially" | Delete — say what it *is*, not that it "essentially is" |
| "arguably" | Delete — either argue it or don't |
| "undeniably" | Delete — if it's undeniable, the evidence speaks |
| "increasingly" | Keep only with data showing the increase |

### Category 5: Symmetrical Lists

LLMs default to lists of three. Two items that are genuine are better than three where one is padding.

**Detection**: Any bulleted list or "X, Y, and Z" enumeration. Ask: does the last item add information, or is it filler to complete a triple?

**Example**:
- Before: "This requires new theoretical frameworks that bridge distributed systems, formal methods, and language model capabilities."
- After: "This requires frameworks bridging distributed systems and language model capabilities." (if formal methods wasn't doing real work)

### Category 6: Over-Summarizing

LLMs summarize at the end of every section, then summarize again in the conclusion, then summarize in the abstract. The reader doesn't need to be told what they just read.

**Rule**: Each fact should appear exactly once in the paper. The abstract gets a compressed version. Section endings should *advance* the argument, not recap it.

### Category 7: Grandiose Framing

| Pattern | Example | Fix |
|---------|---------|-----|
| "In the rapidly evolving landscape of..." | "In the rapidly evolving landscape of AI agents..." | Cut. Start with the point. |
| "represents a paradigm shift" | — | Say what changed, specifically |
| "revolutionizing" | — | Say what improved, with evidence |
| "a cornerstone of" | — | "used in" or "central to" |
| "paving the way for" | — | "enabling" |
| "at the forefront of" | — | Cut |
| "a testament to" | — | Cut |

### Category 8: Structural Tics

| Pattern | What's Wrong | Fix |
|---------|-------------|-----|
| Every paragraph is exactly 3 sentences | Mechanical rhythm | Vary paragraph length (1-6 sentences) |
| Every section ends with a forward pointer ("In the next section...") | LLM scaffolding | Cut. The table of contents exists. |
| Opening with "In this paper, we..." | Acceptable in academic writing but overused | Vary: lead with the finding, not the meta-statement |
| Closing with "In conclusion, ..." followed by restating every point | Padding | One-sentence restatement, then *new* insight or implication |

## Workflow

### Quick Pass (5 minutes)

Run the detection script on the file:

```bash
python3 ~/.hermes/skills/creative/de-ai/scripts/detect.py <file.md>
```

This flags lines matching the pattern catalog. Review each flag and decide: delete, rewrite, or keep.

### Full Rewrite Pass

1. **Read** the full text.
2. **Flag** every instance from Categories 1-8.
3. **Rewrite** each flagged instance. Prefer deletion over rewriting — most AI patterns are pure filler.
4. **Read aloud** (mentally): does each sentence sound like something a person would say in conversation? If not, simplify.
5. **Check paragraph rhythm**: vary lengths. Break up uniform 3-sentence paragraphs.
6. **Verify** you haven't removed actual content — only decoration.

### Integration with Essay Writing

Add a de-AI pass as the final step before publishing:

```
Draft → Review → Revise → **De-AI pass** → Publish
```

When used with the `essay-writing` skill, run de-AI after the reviewer cycle completes.

## What NOT to Remove

- **Technical precision**: "significantly different (p < 0.05)" — the adverb is doing real work here.
- **Genuine contrast**: "Unlike prior work which assumes X, we relax this to Y" — the contrast is substantive.
- **Field-standard phrases**: "We propose", "Our contributions are", "Related work" — these are conventions, not AI tics.
- **Hedging with epistemic purpose**: "This may indicate..." when you genuinely aren't sure.
