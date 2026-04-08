# Wiki Schema

This document codifies the conventions for the knowledge wiki in the Obsidian vault. It serves as both human documentation and injectable LLM context.

## Contents
- Page Types (Digest, Concept, Name, Synthesis, Comparison)
- Frontmatter Conventions
- Wikilink Conventions
- Tag Taxonomy
- Status Conventions
- Index Conventions

## Page Types

### Digest
- **Directory:** `gen-notes/digests/`
- **Created by:** paper-digest, paper-summarizer
- **Required frontmatter:** `title`, `authors`, `year`, `domain`, `tags`, `categories`, `related`, `source`, `digested`, `status`
- **Sections:** TL;DR or Main Idea, Key Ideas/Conclusions, What's Novel, Method, Results, Limitations, Connections

### Concept
- **Directory:** `gen-notes/concepts/`
- **Created by:** wiki-manager ingest
- **Required frontmatter:** `title`, `type: concept`, `domain`, `aliases`, `date-created`, `date-updated`, `source-digests`, `tags`
- **Sections:** Overview, Key Papers, Evolution, Open Questions, Related Concepts
- **Naming:** Use the canonical concept name (e.g., `Transformer.md`, `RLHF.md`)

### Name
- **Directory:** `gen-notes/names/`
- **Created by:** wiki-manager ingest
- **Required frontmatter:** `title`, `type: name`, `domain`, `aliases`, `date-created`, `date-updated`, `source-digests`, `tags`, `name-type`
- **Sections:** Overview, Key Contributions, Timeline, Related Names, Related Concepts
- **Naming:** Use the canonical name (e.g., `Geoffrey Hinton.md`, `ImageNet.md`, `GPT-4.md`)
- **name-type values:** `person`, `dataset`, `model`, `place`, `paper`

### Synthesis
- **Directory:** `gen-notes/syntheses/`
- **Created by:** wiki-query or manual
- **Required frontmatter:** `title`, `type: synthesis`, `domain`, `date-created`, `sources`, `tags`
- **Sections:** Query (original question), Answer, Sources Used

### Comparison
- **Directory:** `gen-notes/comparisons/`
- **Created by:** wiki-query or manual
- **Required frontmatter:** `title`, `type: comparison`, `domain`, `date-created`, `sources`, `tags`
- **Sections:** Overview, Side-by-Side Comparison (table), Key Differences, Key Similarities, Verdict/Takeaway

## Frontmatter Conventions

All pages MUST have YAML frontmatter delimited by `---`. Common fields:

```yaml
---
title: "Page Title"
type: digest | concept | name | synthesis
domain: ai | systems | history | science | wisdom
date-created: YYYY-MM-DD
date-updated: YYYY-MM-DD
tags:
  - tag-one
  - tag-two
---
```

Concept pages additionally include:
```yaml
aliases:
  - "Alternate Name"
  - "Abbreviation"
source-digests:
  - "[[Paper Title One]]"
  - "[[Paper Title Two]]"
```

Name pages additionally include:
```yaml
name-type: person | dataset | model | place | paper
aliases:
  - "Alternate Name"
source-digests:
  - "[[Paper Title One]]"
```

## Wikilink Conventions

- Always use `[[Page Title]]` for cross-references
- Concept references: `[[Transformer]]`, `[[RLHF]]`
- Name references: `[[Geoffrey Hinton]]`, `[[ImageNet]]`
- Digest references: `[[Attention Is All You Need]]`
- Prefer exact page titles over approximate names
- The Connections section of every page should link to related pages

## Domain Taxonomy

Every page MUST have a `domain` field in frontmatter. Domains are the top-level knowledge areas that organize the wiki. A page belongs to exactly **one** primary domain; cross-domain connections are expressed through wikilinks, not multiple domains.

### Valid Domains

| Domain | Scope | Examples |
|--------|-------|---------|
| `ai` | AI & Machine Learning | Transformers, scaling laws, RLHF, agents, LLMs, training, inference optimization, AI strategy |
| `systems` | Computing Systems & Infrastructure | GPU programming, CUDA, data center networking, RDMA, distributed systems, computer architecture, TPU/NPU |
| `history` | History & Civilization | Chinese history, world history, historiography methodology, historical figures and events |
| `science` | Physics, Mathematics & Complexity | Quantum mechanics, information theory, complexity theory, Kolmogorov complexity, thermodynamics, biology, philosophy of science |
| `wisdom` | Philosophy, Leadership & Classical Thought | Chinese classical philosophy, Western philosophy, management, engineering culture, self-development, decision-making |

### Domain Assignment Rules

1. **Use the primary domain** — if a concept spans two domains, pick the one where it's most commonly discussed. E.g., "Kolmogorov Complexity" → `science` (even though it connects to AI compression).
2. **Digests inherit domain from their subject matter**, not their application. A physics paper applied to ML → `science`.
3. **Concepts and names inherit domain from their canonical field.** "Geoffrey Hinton" → `ai`. "Yang Zhenning" → `science`. "Edsger Dijkstra" → `systems`.
4. **Cross-domain pages are the most valuable.** A concept page on "Complex Systems" (domain: `science`) should wikilink to AI emergence, historical examples, etc. The links cross domains even though the page lives in one.
5. **When in doubt, ask:** "If someone searched for this topic, which section of a university library would they check first?"

### Frontmatter Example

```yaml
---
title: "Transformer"
type: concept
domain: ai
# ... other fields
---
```

## Tag Taxonomy

Tags provide fine-grained categorization within and across domains. Match existing vault categories:
- **AI/ML:** `AI`, `LLM`, `transformer`, `attention`, `scaling`, `training`, `inference`, `data`
- **Systems:** `systems`, `hardware`, `distributed`, `optimization`
- **Subfield:** `NLP`, `vision`, `multimodal`, `agents`, `reasoning`
- **Meta:** `management`, `leadership`, `engineering`, `philosophy`, `history`

## Status Conventions

- `📥` — just added, not yet deeply read
- `⌨️` — in progress / working notes
- `🌴` — evergreen / fully processed
- `🔗` — concept/name page (auto-maintained)

## Index Conventions

`index.md` is auto-generated. Sections:
- **Recent Digests** — last 10 digested papers
- **Concepts** — alphabetical list with one-line descriptions
- **Names** — alphabetical list with one-line descriptions
- **By Topic** — grouped by primary tag
- **Stats** — counts by type and status
