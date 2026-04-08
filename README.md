# HermesSkills

Custom skills for [Hermes Agent](https://github.com/hermes-ai/hermes-agent).

## Skills

### creative/
- **essay-writing** — Multi-agent essay writing workflow (Claude Opus drafts, GLM-5.1 reviews)

### devops/
- **hermes-backup** — Backup Hermes config, sessions, memories, and skills

### openclaw-imports/
- **check-market-movers** — Monitor portfolio holdings for market moves
- **generating-briefs** — Generate daily AI tech and investment briefs
- **import-openclaw-skills** — Import skills from Openclaw
- **openbb-sync** — Sync OpenBB financial data pipeline
- **paper-queue** — Manage a reading queue of academic papers
- **paper-summarizer** — Summarize papers and save to Obsidian vault
- **self-improving-agent** — Capture learnings and corrections
- **wiki-manager** — Maintain a living knowledge wiki in Obsidian
- **wiki-query** — Answer research questions from the knowledge wiki

## Installation

Copy skills into `~/.hermes/skills/`:

```bash
git clone https://github.com/zhanglpg/HermesSkills.git /tmp/HermesSkills
cp -R /tmp/HermesSkills/*/ ~/.hermes/skills/
```
