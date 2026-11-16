"""hr_mcp_server.py - MCP server with HR tools for one organization.

The organization is a folder (--org) laid out like this:
    hr-docs/            the HR policy documents (HTML)
    employees.csv       one row per employee: work email, name and leave balances
    sample-emails/      example emails (used by agent.py, not by this server)
    system_prompt.txt   the agent's instructions (used by agent.py, not by this server)
Without --org it uses week-04/hartwell-hr, the lecture's organization.

Tools:
  search_policy(query)       the 4 sections of the HR documents closest to the query,
                             each with its source file, for citing.
  get_leave_balance(...)     the employee's leave balances, from employees.csv.
      HR staff mode (default):   takes an employee's work email.
      Employee mode (--as-employee ADDRESS): takes no inputs and returns only that
                                 employee's balance.

employees.csv's column names are not assumed. The header row (checked against the values)
tells which column holds the work email, which hold the name, and which hold leave
balances (see detect_columns), so files laid out differently from Hartwell's work too.

Usage (from the repository folder):
    .venv\\Scripts\\python.exe week-04\\hr_mcp_server.py                       HR staff mode, Hartwell
    .venv\\Scripts\\python.exe week-04\\hr_mcp_server.py --org week-04\\ridgeline-hotels
    .venv\\Scripts\\python.exe week-04\\hr_mcp_server.py --as-employee dana.whitfield@hartwellfoods.example
    .venv\\Scripts\\python.exe week-04\\hr_mcp_server.py --org week-04\\ridgeline-hotels --rebuild

The server talks to the AI app over standard input/output (stdio), so it never prints
to stdout; messages go to stderr. It never calls Claude and needs no API key.

The document search reuses week-03/ask.py's approach: one chunk per <h2> section with a
label line (title, version, section heading), stored in a Chroma database with Chroma's
built-in embedding model and cosine similarity. Each organization has its own database
in week-04/chroma-db/<organization folder name>/ (git-ignored), rebuilt automatically at
startup whenever a file in its hr-docs/ is added, removed or changed, or on demand with
--rebuild.
"""

import argparse
import contextlib
import csv
import hashlib
import re
import sys
from pathlib import Path
from typing import Any, TypedDict

import chromadb
from bs4 import BeautifulSoup
from chromadb.config import Settings
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

WEEK_DIR = Path(__file__).resolve().parent
DEFAULT_ORG = WEEK_DIR / "hartwell-hr"
DB_ROOT = WEEK_DIR / "chroma-db"  # one subfolder per organization; git-ignored
COLLECTION = "hr-docs"
CHUNKER_VERSION = "sections-v2"  # change to force a rebuild when chunking logic changes
MAX_WORDS = 170  # same limit as ask.py: keeps chunks under the embedding model's token limit
TOP_K = 4

# Set by set_org() at startup
ORG_DIR = DEFAULT_ORG
DOCS_DIR = ORG_DIR / "hr-docs"
EMPLOYEES_CSV = ORG_DIR / "employees.csv"
DB_DIR = DB_ROOT / ORG_DIR.name


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def set_org(org_dir: Path) -> None:
    global ORG_DIR, DOCS_DIR, EMPLOYEES_CSV, DB_DIR
    ORG_DIR = org_dir.resolve()
    DOCS_DIR = ORG_DIR / "hr-docs"
    EMPLOYEES_CSV = ORG_DIR / "employees.csv"
    DB_DIR = DB_ROOT / ORG_DIR.name
    for needed in (DOCS_DIR, EMPLOYEES_CSV):
        if not needed.exists():
            raise SystemExit(f"{ORG_DIR} is not an organization folder: {needed.name} is missing")


def org_title() -> str:
    """A readable name from the folder name (ridgeline-hotels -> Ridgeline Hotels)."""
    return " ".join(w.capitalize() for w in re.split(r"[-_ ]+", ORG_DIR.name) if w)


# ---------------------------------------------------------------------------
# Chunking (adapted from week-03/ask.py, HTML only)
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


def chunk_html(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for tag in soup(["style", "script", "footer", "nav"]):
        tag.decompose()
    bar = soup.find(class_="bar")
    if bar:
        bar.decompose()

    root = soup.find("main") or soup.body or soup
    h1 = root.find("h1")
    title = clean(h1.get_text()) if h1 else path.stem
    meta_tag = root.find(class_="meta")
    meta = clean(meta_tag.get_text()) if meta_tag else ""
    for tag in (meta_tag, h1):
        if tag:
            tag.decompose()

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

    chunks = []
    for heading, paragraphs in sections:
        paragraphs = [p for p in paragraphs if p]
        if not paragraphs:
            continue
        label = make_label(title, meta, heading)
        for piece in split_long(paragraphs):
            chunks.append({"text": label + "\n" + "\n".join(piece),
                           "source": path.name, "title": title, "section": heading})
    return chunks


def document_files() -> list[Path]:
    return sorted(p for p in DOCS_DIR.iterdir()
                  if p.is_file() and p.suffix.lower() in (".html", ".htm"))


# ---------------------------------------------------------------------------
# Chroma database (one per organization)
# ---------------------------------------------------------------------------

def folder_fingerprint() -> str:
    h = hashlib.sha256(CHUNKER_VERSION.encode())
    for path in document_files():
        h.update(path.name.encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def get_collection(force_rebuild: bool = False):
    """Open the organization's database, rebuilding it if forced or if the documents changed."""
    client = chromadb.PersistentClient(path=str(DB_DIR), settings=Settings(anonymized_telemetry=False))
    fingerprint = folder_fingerprint()
    try:
        existing = client.get_collection(COLLECTION)
    except Exception:
        existing = None

    if existing is not None and not force_rebuild and (existing.metadata or {}).get("fingerprint") == fingerprint:
        log(f"Database is up to date ({existing.count()} chunks) -> {DB_DIR}")
        return existing

    if existing is not None:
        client.delete_collection(COLLECTION)
    chunks = []
    for path in document_files():
        try:
            chunks.extend(chunk_html(path))
        except Exception as e:  # one bad file should not stop the build
            log(f"Skipping {path.name}: could not read it ({e})")
    if not chunks:
        raise SystemExit(f"No readable HTML documents found in {DOCS_DIR}")

    collection = client.create_collection(
        COLLECTION,
        metadata={"fingerprint": fingerprint},
        configuration={"hnsw": {"space": "cosine"}},
    )
    collection.add(
        ids=[f"{c['source']}#{i}" for i, c in enumerate(chunks)],
        documents=[c["text"] for c in chunks],
        metadatas=[{k: c[k] for k in ("source", "title", "section")} for c in chunks],
    )
    files = len({c["source"] for c in chunks})
    log(f"Built database: {len(chunks)} chunks from {files} files -> {DB_DIR}")
    return collection


# ---------------------------------------------------------------------------
# Employee records (column names worked out from the header row)
# ---------------------------------------------------------------------------

EMAIL_WORDS = ("email", "e-mail", "mail")
OTHER_PERSON_WORDS = ("manager", "supervisor", "lead", "boss", "reports_to", "reports to")
NAME_WORDS = ("name",)
BALANCE_WORDS = ("balance", "left", "remaining", "available", "accrued", "banked", "carry",
                 "pto", "vacation", "sick", "personal", "leave", "holiday", "float",
                 "bereavement", "hours", "days")
CONTEXT_WORDS = ("as_of", "as of", "asof", "updated", "accrual", "rate", "hire", "start",
                 "status", "employment", "type", "department", "dept", "property", "hotel",
                 "location", "site", "role", "job", "title", "position")


def norm(header: str) -> str:
    return header.strip().lower()


def looks_numeric(value: str) -> bool:
    try:
        float(value.strip().replace(",", ""))
        return True
    except ValueError:
        return False


def detect_columns(header: list[str], rows: list[dict]) -> dict:
    """Work out from the header row (checked against the values) which columns hold what.

    email:    a column whose name mentions email and whose values contain '@', skipping
              columns about another person (manager_email, supervisor_email, ...).
    names:    columns whose name contains 'name' (name, or first_name + last_name).
    balances: columns whose name has a leave word (pto, vacation, sick, balance, hours,
              days, ...) and whose values are all numbers or blank.
    context:  other columns that help read a balance (as-of date, accrual rate, hire date,
              employment type, department or property).
    Columns about another person are never returned.
    """
    def about_other_person(h: str) -> bool:
        return any(w in norm(h) for w in OTHER_PERSON_WORDS)

    def values(h: str) -> list[str]:
        return [(r.get(h) or "").strip() for r in rows]

    email_candidates = [h for h in header
                        if any(w in norm(h) for w in EMAIL_WORDS) and not about_other_person(h)
                        and any("@" in v for v in values(h))]
    if not email_candidates:  # no email-looking header: fall back to a column of addresses
        email_candidates = [h for h in header if not about_other_person(h)
                            and sum("@" in v for v in values(h)) > len(rows) / 2]
    if not email_candidates:
        raise SystemExit(f"Could not find a work email column in {EMPLOYEES_CSV.name}: {header}")
    email = email_candidates[0]

    names = [h for h in header if h != email and not about_other_person(h)
             and any(w in norm(h) for w in NAME_WORDS)]
    balances = [h for h in header if h not in names and h != email and not about_other_person(h)
                and any(w in norm(h) for w in BALANCE_WORDS)
                and all(v == "" or looks_numeric(v) for v in values(h))
                and any(v != "" for v in values(h))]
    if not balances:
        raise SystemExit(f"Could not find any leave balance columns in {EMPLOYEES_CSV.name}: {header}")
    context = [h for h in header if h not in names and h not in balances and h != email
               and not about_other_person(h) and any(w in norm(h) for w in CONTEXT_WORDS)]
    return {"email": email, "names": names, "balances": balances, "context": context}


def read_employees() -> tuple[list[dict], dict]:
    with EMPLOYEES_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        header = [h for h in (reader.fieldnames or []) if h is not None]
    return rows, detect_columns(header, rows)


def number(value: str) -> int | float | None:
    value = value.strip().replace(",", "")
    if not value:
        return None
    n = float(value)
    return int(n) if n.is_integer() else n


def find_balance(email: str) -> dict[str, Any]:
    """Exact (case-insensitive) email match in employees.csv, read fresh on every call.

    Returns the employee's email, name, leave balances (keyed by the file's own column
    names, so units such as hours or days stay visible) and any context columns.
    """
    wanted = email.strip().lower()
    rows, cols = read_employees()
    for row in rows:
        if (row.get(cols["email"]) or "").strip().lower() == wanted:
            name = " ".join((row.get(h) or "").strip() for h in cols["names"]).strip()
            record: dict[str, Any] = {"email": (row.get(cols["email"]) or "").strip(), "name": name}
            record["balances"] = {h.strip(): number(row.get(h) or "") for h in cols["balances"]}
            if cols["context"]:
                record["details"] = {h.strip(): (row.get(h) or "").strip() for h in cols["context"]}
            return record
    raise ToolError(
        f"No employee record matches '{email.strip()}'. Do not state, estimate or guess any leave "
        "balance for this person. Say that their balance could not be found and that HR will "
        "follow up."
    )


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

class PolicyChunk(TypedDict):
    rank: int
    source: str
    section: str
    similarity: float
    text: str


class PolicySearchResult(TypedDict):
    query: str
    results: list[PolicyChunk]


def build_server(collection, as_employee: str | None) -> MCPServer:
    mode = (f"employee mode: get_leave_balance returns only {as_employee}'s balance"
            if as_employee else "HR staff mode: get_leave_balance looks up any employee by work email")
    server = MCPServer(
        name=ORG_DIR.name,
        instructions=(
            f"{org_title()} HR tools. Use search_policy for policy questions and cite the source "
            "file of every policy fact. Use get_leave_balance for leave balances. Never state a "
            f"policy or a number that did not come from these tools. This server is in {mode}."
        ),
    )

    @server.tool()
    def search_policy(query: str) -> PolicySearchResult:
        """Search the organization's HR policy documents.

        Returns the 4 document sections closest to the query, best match first. Each result has
        its source file (cite it for every policy fact), section heading, similarity score
        (0 to 1, higher is closer) and full text. If none of them answers the question, the
        documents do not cover it; do not answer from outside knowledge.
        """
        if not query.strip():
            raise ToolError("The search query is empty. Pass a few words describing the policy question.")
        result = collection.query(query_texts=[query], n_results=min(TOP_K, collection.count()))
        results = [
            PolicyChunk(rank=rank, source=meta["source"], section=meta.get("section", ""),
                        similarity=round(1 - dist, 3), text=text)
            for rank, (text, meta, dist) in enumerate(
                zip(result["documents"][0], result["metadatas"][0], result["distances"][0]), start=1)
        ]
        return PolicySearchResult(query=query, results=results)

    if as_employee:
        def get_leave_balance() -> dict[str, Any]:
            """Get the leave balances of the employee this session is for (the email's sender).

            Takes no inputs: it can only return that one employee's balance. It cannot look up
            anyone else. Balance names are the employee file's column names, so check them for
            units (hours or days). If the sender has no employee record, it returns an error.
            """
            return find_balance(as_employee)
    else:
        def get_leave_balance(email: str) -> dict[str, Any]:
            """Get an employee's leave balances, for HR staff.

            Pass the employee's exact work email address. Names are not accepted. Balance names
            are the employee file's column names, so check them for units (hours or days).
            """
            return find_balance(email)

    server.tool()(get_leave_balance)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP server with one organization's HR tools (stdio).")
    parser.add_argument("--org", metavar="FOLDER", default=str(DEFAULT_ORG),
                        help="organization folder with hr-docs/ and employees.csv (default: week-04/hartwell-hr)")
    parser.add_argument("--as-employee", metavar="EMAIL",
                        help="employee mode: get_leave_balance takes no inputs and returns only this employee's balance")
    parser.add_argument("--rebuild", action="store_true",
                        help="rebuild the document database, then exit (does not start the server)")
    args = parser.parse_args()

    as_employee = args.as_employee.strip() if args.as_employee else None
    if args.as_employee is not None and not as_employee:
        parser.error("--as-employee needs an email address")

    set_org(Path(args.org))
    read_employees()  # fail now, not on the first tool call, if the columns can't be worked out

    # stdout carries the MCP connection, so anything a library prints while building goes to stderr
    with contextlib.redirect_stdout(sys.stderr):
        collection = get_collection(force_rebuild=args.rebuild)
        if args.rebuild:
            return
        collection.query(query_texts=["warm-up"], n_results=1)  # load the embedding model now, not on the first call

    log(f"Organization: {org_title()} ({ORG_DIR})")
    if as_employee:
        log(f"Employee mode for {as_employee}")
    build_server(collection, as_employee).run()  # stdio transport


if __name__ == "__main__":
    main()
