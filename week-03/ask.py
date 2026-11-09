"""ask.py - answer questions from a folder of documents with retrieval + Claude (RAG).

Usage (from the repository folder):
    .venv\\Scripts\\python.exe week-03\\ask.py "Your question"
    .venv\\Scripts\\python.exe week-03\\ask.py --docs week-03\\larkfield-docs "Your question"
    .venv\\Scripts\\python.exe week-03\\ask.py --docs week-03\\larkfield-docs --save week-03\\runs\\q1.txt "Your question"

How it works:
  1. Reads every file directly inside the document folder: HTML, PDF, Word (.docx),
     Markdown and plain text; any other file is read as text if it is text.
  2. Splits each document into one chunk per section (heading + everything under it).
     Each chunk starts with a label line: document title, version line, section heading,
     and records the file it came from.
  3. Stores the chunks in a Chroma database kept in week-03/chroma-db/<folder name>/
     (one database per document folder, git-ignored), embedded with Chroma's built-in
     embedding model. The database is rebuilt automatically whenever files in the
     folder are added, removed or changed, or on demand with --rebuild.
  4. Retrieves the 4 chunks most similar to the question, prints each one's rank,
     similarity score, source file and first 150 characters (--full prints whole
     chunks), then asks Claude to answer from those chunks only, citing the source file.

The Anthropic API key is read at runtime from the ANTHROPIC_API_KEY environment
variable, or else from API-Key.txt / APIKey.txt in the folder that contains the
repository. It is never printed or saved.
"""

import argparse
import hashlib
import os
import re
import sys
from collections import Counter
from pathlib import Path

import anthropic
import chromadb
from bs4 import BeautifulSoup
from chromadb.config import Settings
from pypdf import PdfReader

MODEL = "claude-sonnet-5"
WEEK_DIR = Path(__file__).resolve().parent
DEFAULT_DOCS = WEEK_DIR / "copperline-docs"
DB_ROOT = WEEK_DIR / "chroma-db"
KEY_DIR = WEEK_DIR.parent.parent  # the folder that contains the repository
API_KEY_FILES = [KEY_DIR / "API-Key.txt", KEY_DIR / "APIKey.txt"]
CHUNKER_VERSION = "sections-v2"  # change to force a rebuild when chunking logic changes
MAX_WORDS = 300  # sections longer than this are split at paragraph breaks
DEFAULT_TOP_K = 4
PREVIEW_CHARS = 150

SYSTEM_PROMPT = """You answer questions for staff using only the document excerpts provided in the user message.

Rules:
- Use only information in the excerpts. Do not use outside knowledge and do not guess.
- Give the specific figure, amount, deadline or rule that answers the question.
- Cite the source file name of every fact you use, in the form (Source: file-name.html).
- If the excerpts do not contain the answer, say plainly that {org}'s documents do not contain that information, and do not provide a figure from anywhere else.
- Keep the answer short and direct."""


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    for path in API_KEY_FILES:
        try:
            key = path.read_text(encoding="utf-8-sig").strip()
        except OSError:
            continue
        if key:
            return key
    sys.exit(f"No API key found. Set ANTHROPIC_API_KEY or put the key in {API_KEY_FILES[0]}.")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_label(title: str, meta: str, heading: str) -> str:
    status = clean(meta.split("Owner:")[0]).rstrip(".") if meta else ""
    label = f"{title} [{status}]" if status else title
    return f"{label} | {heading}" if heading else label


def split_long(paragraphs: list[str]) -> list[list[str]]:
    """Group paragraphs into pieces of at most MAX_WORDS words (never splits a paragraph)."""
    pieces, current, words = [], [], 0
    for para in paragraphs:
        n = len(para.split())
        if current and words + n > MAX_WORDS:
            pieces.append(current)
            current, words = [], 0
        current.append(para)
        words += n
    if current:
        pieces.append(current)
    return pieces


def sections_to_chunks(title, meta, org, sections, source):
    """sections: list of (heading, [paragraph, ...]) -> list of chunk dicts."""
    chunks = []
    for heading, paragraphs in sections:
        paragraphs = [p for p in paragraphs if p]
        if not paragraphs:
            continue
        label = make_label(title, meta, heading)
        for piece in split_long(paragraphs):
            chunks.append({
                "text": label + "\n" + "\n".join(piece),
                "source": source,
                "title": title,
                "section": heading,
                "org": org,
            })
    return chunks


def chunk_html(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for tag in soup(["style", "script", "footer", "nav"]):
        tag.decompose()

    bar = soup.find(class_="bar")
    org = clean(bar.strong.get_text()) if bar and bar.strong else ""
    if bar:
        bar.decompose()

    root = soup.find("main") or soup.body or soup
    h1 = root.find("h1")
    title = clean(h1.get_text()) if h1 else path.stem
    meta_tag = root.find(class_="meta")
    meta = clean(meta_tag.get_text()) if meta_tag else ""
    if meta_tag:
        meta_tag.decompose()
    if h1:
        h1.decompose()

    sections, heading, paragraphs = [], "", []
    for el in root.find_all(["h2", "h3", "p", "li", "td", "dt", "dd"]):
        if el.name in ("h2", "h3"):
            sections.append((heading, paragraphs))
            heading, paragraphs = clean(el.get_text()), []
        elif el.name in ("li", "dd"):
            paragraphs.append("- " + clean(el.get_text()))
        elif el.find_parent(["li", "dd"]) is None:
            paragraphs.append(clean(el.get_text()))
    sections.append((heading, paragraphs))
    return sections_to_chunks(title, meta, org, sections, path.name)


def is_heading(line: str) -> bool:
    return len(line) <= 70 and not line.endswith((".", ":", ",", ";")) and line[:1].isupper()


def lines_to_blocks(lines) -> list[list[str]]:
    """Group lines into blocks separated by blank lines, dropping page footers."""
    blocks, current = [], []
    for raw in lines:
        line = clean(raw)
        if re.search(r"\bPage \d+ of \d+\b", line):
            line = ""
        if line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def chunk_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    meta_title = str((reader.metadata or {}).get("/Title", "") or "")
    title, _, org = (part.strip() for part in meta_title.partition("|"))
    lines = []
    for page in reader.pages:
        lines.extend(page.extract_text(extraction_mode="layout").splitlines())
        lines.append("")
    return chunk_blocks(path, lines_to_blocks(lines), title, org)


def chunk_text(path: Path, text: str) -> list[dict]:
    """Plain text: first line is the title, short unpunctuated lines are headings."""
    return chunk_blocks(path, lines_to_blocks(text.splitlines()), "", "")


def chunk_markdown(path: Path, text: str) -> list[dict]:
    title, meta, sections, heading, paragraphs = "", "", [], "", []
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", block)
        if m:
            rest = block[m.end():].strip()
            if len(m.group(1)) == 1 and not title:
                title = clean(m.group(2))
            else:
                sections.append((heading, paragraphs))
                heading, paragraphs = clean(m.group(2)), []
            block = rest
            if not block:
                continue
        if title and not heading and not sections and not paragraphs and not meta:
            meta = clean(block)  # first paragraph under the title (version/owner line)
            continue
        items = [clean(line) for line in block.splitlines() if line.strip()]
        if all(re.match(r"^[-*+]\s|^\d+[.)]\s", i) for i in items):
            paragraphs.extend("- " + re.sub(r"^([-*+]|\d+[.)])\s+", "", i) for i in items)
        else:
            paragraphs.append(clean(block))
    sections.append((heading, paragraphs))
    return sections_to_chunks(title or path.stem, meta, "", sections, path.name)


def chunk_docx(path: Path) -> list[dict]:
    import docx  # python-docx

    document = docx.Document(str(path))
    title = clean(document.core_properties.title or "")
    meta, sections, heading, paragraphs = "", [], "", []
    for para in document.paragraphs:
        text = clean(para.text)
        if not text:
            continue
        style = (para.style.name or "").lower() if para.style is not None else ""
        if style == "title" or (style == "heading 1" and not title):
            title = title or text
        elif style.startswith("heading"):
            sections.append((heading, paragraphs))
            heading, paragraphs = text, []
        elif title and not heading and not sections and not paragraphs and not meta:
            meta = text
        elif "list" in style:
            paragraphs.append("- " + text)
        else:
            paragraphs.append(text)
    for table in document.tables:  # each table row becomes one line in a "Table" section
        rows = [" | ".join(clean(c.text) for c in row.cells) for row in table.rows]
        sections.append(("Table", [r for r in rows if r.strip(" |")]))
    sections.append((heading, paragraphs))
    return sections_to_chunks(title or path.stem, meta, "", sections, path.name)


def chunk_blocks(path: Path, blocks: list[list[str]], title: str, org: str) -> list[dict]:
    """Turn blocks of lines (from PDF or plain text) into section chunks."""
    if not title:
        title = blocks[0][0] if blocks else path.stem
    meta, sections = "", []
    started = False
    for block in blocks:
        if not started:
            if block[0] == title:  # title block: title line + version/meta lines
                meta = " ".join(block[1:])
                started = True
            elif not org:
                org = block[0]
            continue
        if is_heading(block[0]) and len(block) > 1:
            sections.append((block[0], [" ".join(block[1:])]))
        elif sections:
            sections[-1][1].append(" ".join(block))
        else:
            sections.append(("", [" ".join(block)]))
    if not started:  # no recognizable title block: treat everything as body
        sections = [("", [" ".join(b) for b in blocks])]
    return sections_to_chunks(title, meta, org, sections, path.name)


def document_files(docs_dir: Path) -> list[Path]:
    """Every file directly in the folder, ignoring hidden/system files like .DS_Store."""
    return sorted(p for p in docs_dir.iterdir()
                  if p.is_file() and not p.name.startswith((".", "~$")) and p.name.lower() != "thumbs.db")


def load_chunks(docs_dir: Path) -> list[dict]:
    chunks = []
    for path in document_files(docs_dir):
        suffix = path.suffix.lower()
        try:
            if suffix in (".html", ".htm"):
                file_chunks = chunk_html(path)
            elif suffix == ".pdf":
                file_chunks = chunk_pdf(path)
            elif suffix == ".docx":
                file_chunks = chunk_docx(path)
            else:
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except UnicodeDecodeError:
                    print(f"Skipping {path.name}: not a supported document or text file", file=sys.stderr)
                    continue
                if suffix in (".md", ".markdown"):
                    file_chunks = chunk_markdown(path, text)
                else:
                    file_chunks = chunk_text(path, text)
        except Exception as e:  # one bad file should not stop the whole build
            print(f"Skipping {path.name}: could not read it ({e})", file=sys.stderr)
            continue
        if not file_chunks:
            print(f"Skipping {path.name}: no text found", file=sys.stderr)
        chunks.extend(file_chunks)
    return chunks


# ---------------------------------------------------------------------------
# Chroma database (one per document folder)
# ---------------------------------------------------------------------------

def folder_fingerprint(docs_dir: Path) -> str:
    h = hashlib.sha256(CHUNKER_VERSION.encode())
    for path in document_files(docs_dir):
        h.update(path.name.encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def get_collection(docs_dir: Path, force_rebuild: bool):
    db_dir = DB_ROOT / re.sub(r"[^A-Za-z0-9_-]+", "-", docs_dir.name)
    client = chromadb.PersistentClient(path=str(db_dir), settings=Settings(anonymized_telemetry=False))
    fingerprint = folder_fingerprint(docs_dir)

    existing = None
    try:
        existing = client.get_collection("docs")
    except Exception:
        existing = None

    if existing is not None and not force_rebuild and (existing.metadata or {}).get("fingerprint") == fingerprint:
        return existing, db_dir, False

    if existing is not None:
        client.delete_collection("docs")
    chunks = load_chunks(docs_dir)
    if not chunks:
        sys.exit(f"No readable documents found in {docs_dir}")
    collection = client.create_collection(
        "docs",
        metadata={"fingerprint": fingerprint, "docs_dir": str(docs_dir)},
        configuration={"hnsw": {"space": "cosine"}},
    )
    collection.add(
        ids=[f"{c['source']}#{i}" for i, c in enumerate(chunks)],
        documents=[c["text"] for c in chunks],
        metadatas=[{k: c[k] for k in ("source", "title", "section", "org")} for c in chunks],
    )
    files = len({c["source"] for c in chunks})
    print(f"Built database for {docs_dir.name}: {len(chunks)} chunks from {files} files -> {db_dir}",
          file=sys.stderr)
    return collection, db_dir, True


# ---------------------------------------------------------------------------
# Question answering
# ---------------------------------------------------------------------------

def resolve_docs(arg: str | None) -> Path:
    if not arg:
        return DEFAULT_DOCS
    p = Path(arg)
    for candidate in (p, WEEK_DIR.parent / p, WEEK_DIR / p):
        if candidate.is_dir():
            return candidate.resolve()
    sys.exit(f"Document folder not found: {arg}")


def ask_claude(question: str, hits: list[dict], org: str) -> str:
    excerpts = "\n\n".join(
        f'<excerpt rank="{h["rank"]}" source="{h["source"]}">\n{h["text"]}\n</excerpt>' for h in hits
    )
    client = anthropic.Anthropic(api_key=load_api_key())
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT.format(org=org or "the organization"),
            messages=[{
                "role": "user",
                "content": f"<excerpts>\n{excerpts}\n</excerpts>\n\nQuestion: {question}",
            }],
        )
    except anthropic.AuthenticationError:
        sys.exit("The Anthropic API rejected the API key.")
    except anthropic.RateLimitError:
        sys.exit("Rate limited by the Anthropic API. Wait a moment and try again.")
    except anthropic.APIStatusError as e:
        sys.exit(f"Anthropic API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("Could not connect to the Anthropic API. Check your internet connection.")

    if response.stop_reason == "refusal":
        return "(Claude declined to answer this question.)"
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(description="Answer a question from a folder of documents (RAG with Claude).")
    parser.add_argument("question", nargs="?", help="the question to ask (in quotes)")
    parser.add_argument("--docs", help="document folder (default: week-03/copperline-docs)")
    parser.add_argument("--save", help="also write the complete output to this text file (UTF-8)")
    parser.add_argument("--k", type=int, default=DEFAULT_TOP_K, help=f"number of chunks to retrieve (default {DEFAULT_TOP_K})")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the database even if no documents changed")
    parser.add_argument("--full", action="store_true", help=f"print whole chunks instead of the first {PREVIEW_CHARS} characters")
    args = parser.parse_args()

    docs_dir = resolve_docs(args.docs)
    collection, _, _ = get_collection(docs_dir, args.rebuild)
    if not args.question:
        print(f"Database for {docs_dir.name} is ready ({collection.count()} chunks). Ask a question to query it.")
        return

    result = collection.query(query_texts=[args.question], n_results=min(args.k, collection.count()))
    hits = []
    for rank, (text, meta, dist) in enumerate(
        zip(result["documents"][0], result["metadatas"][0], result["distances"][0]), start=1
    ):
        hits.append({"rank": rank, "text": text, "source": meta["source"],
                     "org": meta.get("org", ""), "similarity": 1 - dist})

    org = Counter(h["org"] for h in hits if h["org"]).most_common(1)
    answer = ask_claude(args.question, hits, org[0][0] if org else "")

    lines = []
    for h in hits:
        lines.append(f"[{h['rank']}] similarity {h['similarity']:.3f} | source: {h['source']}")
        if args.full:
            lines.append(h["text"])
        else:
            flat = clean(h["text"])
            lines.append(flat[:PREVIEW_CHARS] + ("..." if len(flat) > PREVIEW_CHARS else ""))
        lines.append("")
    lines.append("ANSWER")
    lines.append(answer)
    output = "\n".join(lines) + "\n"

    print(output, end="")
    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(output, encoding="utf-8")
        print(f"\nSaved to {save_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
