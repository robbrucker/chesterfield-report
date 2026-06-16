"""Fetch Chesterfield County BOS zoning-case staff reports from Laserfiche WebLink.

Given a case number (e.g. "26SN2017"), returns the plain text of the staff-report
pages from the county's Laserfiche WebLink 10.2 instance, or None if the case has
no published packet yet (e.g. a Pending case) or anything fails.

Stdlib only. Verified working 2026-06-15.

HTTP sequence (base https://documents.chesterfield.gov/Weblink_BOS):
  1. GET /Welcome.aspx (follows redirect to CookieCheck.aspx) -> sets the session
     cookies. Done once; the CookieJar is reused across many cases in one run.
  2. POST /SearchService.aspx/GetSearchListing with searchSyn
     '{LF:Basic ~= "<CASE>", option="DFLT"}', searchUuid "" and getNewListing:true
     -> the server mints a search and returns results[] with entryId + contexthits
     (page numbers) in the SAME response. (getNewListing:true + empty uuid is the
     key; a random uuid returns 0 results.)
  3. POST /DocumentService.aspx/GetTextHtmlForPage for each contexthit page ->
     {text}. We only pull the hit pages, never the ~150 MB packet PDF.
"""
from __future__ import annotations

import http.cookiejar
import json
import re
import ssl
import urllib.error
import urllib.request

BASE = "https://documents.chesterfield.gov/Weblink_BOS"
REPO = "BoardOfSupervisors"
TIMEOUT = 30
_TAG_RE = re.compile(r"<[^>]+>")
_UA = "Mozilla/5.0 (ChesterfieldReport; +brucker.rob@gmail.com)"


def new_session() -> http.cookiejar.CookieJar:
    """Return a primed CookieJar, reusable across many cases in one run."""
    jar = http.cookiejar.CookieJar()
    opener = _opener(jar)
    _prime(opener)
    return jar


def _opener(jar):
    ctx = ssl.create_default_context()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=ctx))


def _prime(opener):
    req = urllib.request.Request(BASE + "/Welcome.aspx",
                                 headers={"User-Agent": _UA, "Accept": "text/html"})
    opener.open(req, timeout=TIMEOUT).read()


def _post(opener, path, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST", headers={
        "User-Agent": _UA, "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest", "Referer": BASE + "/Welcome.aspx",
        "Accept": "application/json, text/plain, */*"})
    try:
        raw = opener.open(req, timeout=TIMEOUT).read().decode("utf-8", "replace")
        obj = json.loads(raw)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None
    return obj.get("data", obj) if isinstance(obj, dict) else obj


def _clean(text: str) -> str:
    text = _TAG_RE.sub("", text or "").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_staff_report(case_number: str, jar=None, max_pages: int = 8) -> str | None:
    """Staff-report text for a BOS zoning case, or None. Pass a shared `jar`
    (from new_session()) to reuse one primed session across many cases."""
    case_number = (case_number or "").strip()
    if not case_number:
        return None
    own = jar is None
    if jar is None:
        jar = http.cookiejar.CookieJar()
    opener = _opener(jar)
    if own:
        try:
            _prime(opener)
        except (urllib.error.URLError, TimeoutError):
            return None

    search_body = {
        "repoName": REPO,
        "searchSyn": '{LF:Basic ~= "%s", option="DFLT"}' % case_number,
        "searchUuid": "", "sortColumn": "", "startIdx": 1, "endIdx": 50,
        "getNewListing": True, "sortOrder": 0, "displayInGridView": False,
    }
    data = _post(opener, "/SearchService.aspx/GetSearchListing", search_body)
    if not isinstance(data, dict) or "results" not in data:
        try:
            _prime(opener)
        except (urllib.error.URLError, TimeoutError):
            return None
        data = _post(opener, "/SearchService.aspx/GetSearchListing", search_body)
    if not isinstance(data, dict):
        return None
    results = data.get("results") or []
    if not results:
        return None  # no packet yet (Pending case)

    suid = data.get("searchUUID") or ""
    pieces, seen, want = [], set(), case_number.upper()
    for r in results:
        eid = r.get("entryId")
        if not eid:
            continue
        pages = []
        for ch in (r.get("contexthits") or []):
            p = ch.get("PageNumber") or ch.get("pageNumber")
            if p and p not in pages:
                pages.append(p)
        for page in pages:
            if len(seen) >= max_pages:
                break
            if (eid, page) in seen:
                continue
            seen.add((eid, page))
            td = _post(opener, "/DocumentService.aspx/GetTextHtmlForPage", {
                "repoName": REPO, "documentId": eid, "pageNum": page,
                "showAnn": False, "searchUuid": suid})
            if isinstance(td, dict):
                txt = _clean(td.get("text", ""))
                if txt and want in txt.upper():
                    pieces.append(f"[{r.get('name','')} p.{page}]\n{txt}")
    return "\n\n".join(pieces) if pieces else None
