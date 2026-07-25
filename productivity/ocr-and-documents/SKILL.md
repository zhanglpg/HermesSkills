---
name: ocr-and-documents
description: Extract text from PDFs and scanned documents. Use browser_navigate for remote URLs, pymupdf for local text-based PDFs, marker-pdf for OCR/scanned docs. For DOCX use python-docx, for PPTX see the powerpoint skill.
version: 2.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
For PDF text editing (fix typos, change titles via natural language): see `references/nano-pdf.md`.
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `browser_navigate` first**:

```
browser_navigate(url="https://arxiv.org/pdf/2402.03300")
# then extract with browser_console or browser_snapshot
browser_navigate(url="https://example.com/report.pdf")
```

This handles PDF-to-content conversion with no local dependencies.

Only use local extraction when: the file is local, browser_navigate fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use browser_navigate, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
browser_navigate(url="https://arxiv.org/abs/2402.03300")
# then extract via browser_console

# Full paper
browser_navigate(url="https://arxiv.org/pdf/2402.03300")
# or: curl -sL "https://arxiv.org/pdf/ID" | pdftotext -layout - -

# Search
# Use terminal: curl -s "https://export.arxiv.org/api/query?search_query=all:GRPO+reinforcement+learning&max_results=5&sortBy=submittedDate&sortOrder=descending"
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Notes

- `browser_navigate` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)

## Tesseract OCR: Image-to-Text Fallback

**When to use:** The user sends a photo (whiteboard, screenshot, handwritten notes) and the vision API fails. This happens on providers that don't support `image_url` in message content (e.g., DeepSeek-v4-pro on custom providers). The error looks like:

```
unknown variant `image_url`, expected `text`
```

**One-time setup:**
```bash
brew install tesseract tesseract-lang   # includes chi_sim, jpn, etc.
pip install pytesseract Pillow
```

**Workflow:**

1. **Resize the image first** — large images produce worse OCR:
   ```bash
   sips -Z 1200 input.jpg --out /tmp/resized.jpg
   ```

2. **Run OCR with appropriate languages:**
   ```bash
   # Chinese + English (whiteboard/notes in Chinese)
   tesseract /tmp/resized.jpg /tmp/ocr_out -l chi_sim+eng

   # English only
   tesseract image.jpg /tmp/ocr_out -l eng

   # List available: tesseract --list-langs
   ```

3. **Read the result:**
   ```bash
   cat /tmp/ocr_out.txt
   ```

**Pitfalls:**
- **OCR quality is mediocre for handwriting** — printed text works well; cursive/whiteboard handwriting may produce garbled characters. Accept that partial extraction is better than none. Parse the output for recognizable Chinese/English fragments and reconstruct meaning from context.
- **Image resolution matters** — use `sips -Z 1200` (macOS) to resize before OCR. The original dimensions are often too large for tesseract's resolution estimator.
- **Mixed-language documents need both language packs** — `-l chi_sim+eng` enables both simultaneously. For Japanese add `-l jpn+eng`, etc.
- **`tesseract-lang` is separate from `tesseract`** — just `brew install tesseract` only gives English. The full language pack is ~685MB.
- **Pillow may need separate install** — `pip install Pillow` before `pytesseract` if the auto-dependency fails.

**When NOT to use tesseract:**
- Remote PDFs → use `browser_navigate` first
- Local text-based PDFs → use pymupdf
- Scanned PDFs needing high quality → use marker-pdf
- The vision API works → just use `vision_analyze` or `browser_vision`
