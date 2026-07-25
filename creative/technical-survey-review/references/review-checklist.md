# Survey Review Checklist — Detailed

Expanded diagnostic checklist with concrete examples from real reviews. Use alongside the SKILL.md summary.

## 1. Title-delivery gap

The title makes a promise. Check the survey delivers it *structurally*, not just in prose.

- **"Comparison" titled** → needs a master comparison table where every method appears on common dimensions. Without it, the comparing is scattered and the reader must assemble the comparison from prose across hundreds of lines. Build the table near the top, after the intro/argument, with columns like: Method | Axis/Category | Complexity | Memory | Quality impact | Retrofittable? | Train/Infer asymmetry | Production status. Follow with 2-3 observations the table surfaces (e.g. a retrofittability split, a train/infer asymmetry, a complexity floor).
- **"Lineage" titled** → needs the lineage arc stated explicitly and defended against counterexamples. A single-direction "march of progress" narrative that can't account for re-complexification is incomplete.
- **"Survey" titled** → needs coverage breadth; check the vault for thematically-central omissions.

## 2. Intro structural overload

Symptoms:
- Names systems/papers in the intro that the reader hasn't met yet (premature citations). Fix: state the framework abstractly, defer specific evidence to the relevant section, or compress to a one-line forward reference ("as we will see in the X analysis").
- Meta-references like "developed in Section 8 and drives the conclusion in Section 9." Fix: cut them; let the sections do the work.
- A monolithic final intro paragraph that is effectively a 200-word abstract of the whole argument. Fix: split into (a) what the essay traces, (b) the tempting-but-incomplete reading, (c) the actual thesis.

## 3. Wall paragraphs

A single block making 3+ distinct points. Fix: break into separate paragraphs, one point each. The sharpest counterexample or most surprising claim usually deserves its own paragraph with real (verified) technical detail — that emphasis is earned.

## 4. Vault coverage gaps

Search the user's Obsidian vault for notes on the survey's topic:
```
search_files(target='files', pattern='*<topic>*', path='<vault>/notes')
```
A method that has its own vault note but is absent from the survey is the strongest, easiest coverage fix — the research is already done. When adding it, wire it into the overview diagram and the references list.

## 5. Repetitive conclusions

A conclusion that re-argues the thesis already established in the body. Fix: spend less time re-arguing, more on the forward-looking question. The most interesting sentence in the essay is often the forward question — don't bury it in the penultimate paragraph.

## 6. Draft artifacts in a published piece

- `TBD` / placeholder cells → "not yet reported" or remove.
- Broken YAML: inline arrays (`tags: [a, b]`) — Obsidian's parser won't parse them. Convert to list form (`- a` per line).
- Mermaid `graph LR` with subgraphs → overflows on phone/split-screen (subgraphs render side-by-side). Convert to `flowchart TD` with stacked subgraphs. Watch for redundant headers (subgraph title + internal node with same label) — remove the internal one.

## 7. Citation and mechanism accuracy

- Verify every arXiv ID resolves before publishing — especially any recalled from memory.
- Verify mechanism *descriptions* against the abstract/body. Named components and objectives are easy to get wrong from memory. When adding technical depth to explain a method, that is the moment to open the paper, not elaborate from recall.
- Recompute any numeric claim you touch.

## Editorial-pass mechanics

- Use targeted `patch` calls, not full rewrites (files are 40-70KB).
- Update byline to credit the pass; bump `date-updated`.
- Republish via `gh gist edit <id> <path>` (no `-f`, no stdin). Verify with `gh gist view <id> --raw | grep <new content>`.

## Real examples (anonymized patterns)

- RL-lineage survey: intro named R1/DAPO/VAPO before the reader met them → split into 3 paragraphs, deferred citations. Section 8.1 was one wall paragraph making 4 points → broke into 4, gave the VAPO counterexample its own paragraph. Conclusion re-argued the oscillation thesis → trimmed, emphasized forward question.
- Attention-comparison survey: titled "Comparison" but had no master table → added 14-method table. Intro front-loaded V4 before axes existed → added forward reference. Infini-attention was in the vault but missing → added subsection. FA4 row said `TBD` → "not yet reported". YAML used inline arrays → converted. Overview was `graph LR` → `flowchart TD`.
- VAPO mechanism described from memory as "value clipping + token-level advantage normalization" — both wrong; real techniques are Length-adaptive GAE and Decoupled-GAE. Caught by checking arXiv:2504.05118.
