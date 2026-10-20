#!/usr/bin/env python3
"""
serp_research.py - the pack's free-by-default SERP content analysis.

Replaces the paid SERP heading tool and the paid term-target tool with one pipeline:

  1. Top 10 URLs   DataForSEO live Google SERP (pay per use, about US$0.002 a call).
                   Optional extra: Thruuu, only when THRUUU_API_KEY is set and there are no
                   DataForSEO credentials. No key at all: pass --urls with the top results
                   you found by WebSearch (they are labelled approximate).
  2. Page fetch    Scrapling CLI (`scrapling extract get`, then `scrapling extract fetch` for
                   JavaScript pages), then fetch_page.py (Scrapling library tiers, then
                   Firecrawl when FIRECRAWL_API_KEY is set). A URL nothing could fetch is
                   listed under `needs_webfetch` so the session can read it with WebFetch.
  3. Extraction    H1 to H3 headings and body word counts, parsed locally (stdlib only).
  4. Themes        headings clustered into themes; the caller passes its own theme table.
  5. Terms         term targets from the fetched pages: unigrams, bigrams and trigrams with
                   stop words removed, ranked by TF-IDF style weight, each with the number of
                   pages using it and a min to max usage range across those pages.

Every DataForSEO call's cost is read from the API response and reported in `cost_usd`.
Nothing here needs a subscription. A missing provider is named in `gaps`, never guessed.

Library use (the skills' serp_outline_builder.py wrappers):
    import serp_research as sr
    result = sr.analyse("keyword", country="au", theme_keywords=sr.THEME_KEYWORDS)

CLI:
    python3 serp_research.py "project management software for small agencies" --country au
    python3 serp_research.py "kw" --urls "https://a.example/x,https://b.example/y"
    python3 serp_research.py --extract-file page.html          # headings + word count of one file
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)

import dataforseo_api as dfs  # noqa: E402  (same folder, stdlib only)

# --------------------------------------------------------------------------- themes

# The generic article themes. Skills extend this with their own (buyer's guide themes).
THEME_KEYWORDS: dict[str, list[str]] = {
    'definition': ['what is', 'what are', 'definition', 'overview', 'introduction'],
    'how_it_works': ['how do', 'how does', 'how it works', 'how they work', 'mechanism'],
    'types': ['types', 'type of', 'kinds', 'varieties', 'options', 'different'],
    'installation': ['install', 'installation', 'how to install', 'fitting', 'mount', 'set up', 'setup'],
    'cost': ['cost', 'price', 'pricing', 'how much', 'expense', 'budget'],
    'benefits': ['benefit', 'advantages', 'why', 'effective', 'worth', 'purpose'],
    'maintenance': ['maintenance', 'maintain', 'repair', 'replace', 'upkeep', 'care'],
    'sizing': ['how many', 'how often', 'number', 'size', 'sizing', 'capacity'],
    'comparison': ['vs', 'versus', 'compared', 'difference', 'alternative', 'compare'],
    'faq': ['faq', 'frequently asked', 'questions', 'common question'],
    'diy': ['diy', 'yourself', 'step by step', 'guide to'],
    'problems': ['problem', 'issue', 'disadvantage', 'downside', 'wrong', 'mistake'],
    'choosing': ['choose', 'choosing', 'selecting', 'right', 'best', 'pick'],
    'location_service': ['near me', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide'],
    'why_choose_us': ['why choose', 'why us', 'our service', 'our process', 'what makes'],
    'conclusion': ['conclusion', 'final thoughts', 'summary', 'get started', 'next step'],
}

NOISE_PATTERNS = [
    '$', 'inc gst', 'save $', 'enquire', 'latest articles', 'contact us', 'testimonials',
    'get your free', 'related post', 'about us', 'our products', 'quick links', 'footer',
    'newsletter', 'follow us', 'share this', 'recent posts', 'browse the', 'you may also',
    'quote request', 'general enquiry', 'ready to get started', 'book online', 'call us',
    'email us', 'request a quote', 'copyright', 'categories', 'table of contents',
    'want to connect', 'subscribe', 'sign up', 'leave a reply', 'comments', 'related articles',
    'popular posts', 'search', 'menu', 'cookie',
]


def is_noise(heading: str) -> bool:
    h = heading.strip()
    if len(h) < 5 or len(h) > 120:
        return True
    low = h.lower()
    return any(n in low for n in NOISE_PATTERNS)


def cluster_themes(competitors: list[dict], theme_keywords: dict | None = None,
                   priority: tuple = ()) -> tuple[dict, dict]:
    """Count H2/H3 headings per theme. First matching theme wins; `priority` themes are tried first."""
    theme_keywords = theme_keywords or THEME_KEYWORDS
    order = list(priority) + [t for t in theme_keywords if t not in priority]
    counts: dict[str, int] = {}
    examples: dict[str, list] = defaultdict(list)
    headings = [(h, 'h2') for c in competitors for h in c.get('h2', [])] + \
               [(h, 'h3') for c in competitors for h in c.get('h3', [])]
    for heading, level in headings:
        low = heading.lower()
        for theme in order:
            if any(kw in low for kw in theme_keywords[theme]):
                counts[theme] = counts.get(theme, 0) + 1
                if len(examples[theme]) < 10:
                    examples[theme].append({"heading": heading, "level": level})
                break
    return counts, dict(examples)


def theme_page_counts(competitors: list[dict], theme_keywords: dict | None = None,
                      priority: tuple = ()) -> dict:
    """How many competitor PAGES cover each theme (table stakes = 3+, gaps = under 2)."""
    out: dict[str, int] = {}
    for c in competitors:
        counts, _ = cluster_themes([c], theme_keywords, priority)
        for theme in counts:
            out[theme] = out.get(theme, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def word_count_stats(competitors: list[dict]) -> dict:
    wcs = sorted(c['word_count'] for c in competitors if c.get('word_count'))
    if not wcs:
        return {}
    avg = sum(wcs) // len(wcs)
    median = int(statistics.median(wcs))
    target_min = max(avg, median)
    target_max = min(max(wcs), target_min + 800)
    if target_max < target_min:
        target_max = target_min
    return {'avg': avg, 'min': wcs[0], 'max': wcs[-1], 'median': median,
            'target': f"{target_min:,}-{target_max:,}", 'count': len(wcs)}


# --------------------------------------------------------------------------- extraction

SKIP_TAGS = {'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside', 'form',
             'template', 'iframe', 'button', 'select'}
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
             'param', 'source', 'track', 'wbr'}
BLOCK_TAGS = {'p', 'div', 'li', 'section', 'article', 'main', 'td', 'th', 'tr', 'table', 'ul',
              'ol', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'dd', 'dt', 'figcaption'}


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.stack: list[str] = []
        self.heading: str | None = None
        self.heading_buf: list[str] = []
        self.headings = {'h1': [], 'h2': [], 'h3': []}
        self.text: list[str] = []
        self.title_buf: list[str] = []
        self.in_title = False
        self.main_depth = 0            # inside <main> or <article>
        self.main_text: list[str] = []
        self.main_headings = {'h1': [], 'h2': [], 'h3': []}
        self.heading_in_main = False

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            if tag == 'br':
                self.text.append('\n')
            return
        self.stack.append(tag)
        if tag in SKIP_TAGS:
            self.skip_depth += 1
        if tag == 'title':
            self.in_title = True
        if tag in ('main', 'article'):
            self.main_depth += 1
        if tag in self.headings and not self.skip_depth:
            self.heading, self.heading_buf = tag, []
            self.heading_in_main = self.main_depth > 0
        if tag in BLOCK_TAGS:
            self.text.append('\n')
            if self.main_depth:
                self.main_text.append('\n')
            if self.heading:
                self.heading_buf.append(' ')

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if tag not in self.stack:
            return
        while self.stack:
            t = self.stack.pop()
            if t in SKIP_TAGS:
                self.skip_depth = max(0, self.skip_depth - 1)
            if t == 'title':
                self.in_title = False
            if t in ('main', 'article'):
                self.main_depth = max(0, self.main_depth - 1)
            if t == self.heading:
                txt = re.sub(r'\s+', ' ', ''.join(self.heading_buf)).strip()
                if txt:
                    self.headings[t].append(txt)
                    if self.heading_in_main:
                        self.main_headings[t].append(txt)
                self.heading = None
            if t == tag:
                break
        if tag in BLOCK_TAGS:
            self.text.append('\n')

    def handle_data(self, data):
        if self.in_title:
            self.title_buf.append(data)
            return
        if self.skip_depth:
            return
        if self.heading:
            self.heading_buf.append(data)
        self.text.append(data)
        if self.main_depth:
            self.main_text.append(data)


def _words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", text))


def _tidy(parts: list[str]) -> str:
    text = re.sub(r'[ \t\r\f\v]+', ' ', ''.join(parts))
    return re.sub(r'\n\s*\n+', '\n\n', text).strip()


def extract_html(html: str, main_min_words: int = 300) -> dict:
    """Headings (H1-H3), body text and word count from raw HTML. Navigation, header, footer,
    aside, forms and scripts are excluded so the count reflects the article, not the chrome.
    When the page has a <main> or <article> holding at least `main_min_words` words, only that
    region is counted (sidebars and related-post rails outside it are dropped)."""
    p = _PageParser()
    try:
        p.feed(html)
        p.close()
    except Exception:  # noqa: BLE001 - malformed HTML still yields what was parsed
        pass
    text, heads, scope = _tidy(p.text), p.headings, 'page'
    main_text = _tidy(p.main_text)
    if _words(main_text) >= main_min_words and any(p.main_headings.values()):
        text, heads, scope = main_text, p.main_headings, 'main'
    return {'title': re.sub(r'\s+', ' ', ''.join(p.title_buf)).strip(),
            'h1': heads['h1'], 'h2': heads['h2'], 'h3': heads['h3'],
            'text': text, 'word_count': _words(text), 'scope': scope}


def extract_markdown(md: str) -> dict:
    """Same shape as extract_html, from Markdown (Firecrawl and Scrapling .md output)."""
    heads = {'h1': [], 'h2': [], 'h3': []}
    for level, txt in re.findall(r'^(#{1,3})\s+(.+?)\s*#*\s*$', md, re.M):
        clean = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', txt).strip(' *_`')
        heads[f'h{len(level)}'].append(clean)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', md)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[#*_`>|]', ' ', text)
    return {'title': heads['h1'][0] if heads['h1'] else '', **heads, 'text': text.strip(),
            'word_count': len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", text))}


# --------------------------------------------------------------------------- terms

STOP_WORDS = set("""
a about above after again against all also am an and any are aren't as at be because been
before being below between both but by can can't cannot could couldn't did didn't do does
doesn't doing don't down during each few for from further get gets got had hadn't has hasn't
have haven't having he her here hers herself him himself his how i if in into is isn't it
it's its itself just let's like make makes may me might more most much must my myself need
no nor not now of off on once one only or other our ours ourselves out over own per really
same she should shouldn't so some such than that that's the their theirs them themselves
then there there's these they they're this those through to too under until up upon us use
used using very via want was wasn't way we we're were weren't what what's when where which
while who whom why will with within without won't would wouldn't you you're your yours
yourself yourselves etc eg ie ve ll re s t d m new well even still yet many lot lots read
click here learn see find best top across along around every including
""".split())

_TOKEN = re.compile(r"[a-z][a-z0-9'’-]*[a-z0-9]|[a-z]")


def _tokens(text: str) -> list[str]:
    return [t.replace('’', "'") for t in _TOKEN.findall(text.lower())]


def _ngrams(tokens: list[str], n: int) -> list[str]:
    out = []
    for i in range(len(tokens) - n + 1):
        gram = tokens[i:i + n]
        if gram[0] in STOP_WORDS or gram[-1] in STOP_WORDS:
            continue
        if any(len(g) < 2 or g.isdigit() for g in gram):
            continue
        out.append(' '.join(gram))
    return out


def extract_terms(docs: list[str], top_n: int = 40, min_docs: int = 2,
                  exclude: set | None = None) -> list[dict]:
    """Term targets from competitor page texts.

    For every 1 to 3 word phrase (stop words trimmed from the ends): how many pages use it,
    its usage per page (min, median, max across the pages that use it) and a weight of
    doc share x average frequency x n-gram length bonus x idf smoothing. Phrases used by fewer
    than `min_docs` pages are dropped: one site's pet phrase is not a SERP signal.
    A phrase fully contained in a stronger kept phrase with the same page count is dropped.
    """
    exclude = {e.lower() for e in (exclude or set())}
    n_docs = len(docs)
    if n_docs == 0:
        return []
    min_docs = min(min_docs, n_docs)
    per_doc: list[Counter] = []
    for d in docs:
        toks = _tokens(d)
        c = Counter()
        for n in (1, 2, 3):
            c.update(_ngrams(toks, n))
        per_doc.append(c)
    df = Counter()
    for c in per_doc:
        df.update(c.keys())
    scored = []
    for term, k in df.items():
        if k < min_docs or term in exclude:
            continue
        uses = [c[term] for c in per_doc if term in c]
        n = term.count(' ') + 1
        share = k / n_docs
        avg = sum(uses) / len(uses)
        idf = math.log(1 + n_docs / k)
        weight = share * (1 + math.log(avg)) * (1 + 0.5 * (n - 1)) * (0.5 + idf)
        scored.append({'term': term, 'pages': k, 'min': min(uses), 'median': int(statistics.median(uses)),
                       'max': max(uses), 'weight': round(weight, 3)})
    scored.sort(key=lambda r: (-r['weight'], -r['pages'], r['term']))
    kept: list[dict] = []
    for row in scored:
        if any(row['term'] in k['term'] and row['pages'] <= k['pages'] for k in kept):
            continue
        kept.append(row)
        if len(kept) >= top_n:
            break
    return kept


# --------------------------------------------------------------------------- fetching

def scrapling_cli() -> str | None:
    return shutil.which('scrapling')


def _scrapling_cli_fetch(url: str, mode: str, timeout: int) -> str | None:
    exe = scrapling_cli()
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'page.html')
        cmd = [exe, 'extract', mode, url, out]
        cmd += ['--timeout', str(timeout if mode == 'get' else timeout * 1000)]
        try:
            subprocess.run(cmd, capture_output=True, timeout=timeout + 30, check=False)
        except (subprocess.TimeoutExpired, OSError):
            return None
        if os.path.isfile(out):
            with open(out, encoding='utf-8', errors='replace') as fh:
                return fh.read()
    return None


def fetch_page_text(url: str, min_words: int = 250, timeout: int = 30) -> dict:
    """Fetch one page down the ladder; return the extraction plus `fetched_by` and `escalations`."""
    escalations = []
    for mode in ('get', 'fetch'):
        if not scrapling_cli():
            escalations.append({'tier': 'scrapling-cli', 'reason': 'scrapling CLI not on PATH'})
            break
        html = _scrapling_cli_fetch(url, mode, timeout)
        if html:
            ex = extract_html(html)
            if ex['word_count'] >= min_words:
                return {**ex, 'fetched_by': f'scrapling extract {mode}', 'escalations': escalations}
            escalations.append({'tier': f'scrapling {mode}', 'reason': f"thin ({ex['word_count']} words)"})
        else:
            escalations.append({'tier': f'scrapling {mode}', 'reason': 'no output'})
    try:
        import fetch_page  # noqa: WPS433 - same folder; Scrapling library tiers then Firecrawl
        r = fetch_page.fetch(url, min_text=min_words * 5, timeout=timeout)
        if r.get('markdown'):
            ex = extract_markdown(r['markdown'])
        elif r.get('text'):
            words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", r['text']))
            hs = r.get('headings') or {}
            ex = {'title': r.get('title', ''), 'h1': hs.get('h1', []), 'h2': hs.get('h2', []),
                  'h3': [], 'text': r['text'], 'word_count': words}
        else:
            ex = None
        escalations.extend(r.get('escalations') or [])
        if ex and ex['word_count'] >= min_words:
            return {**ex, 'fetched_by': f"fetch_page.py ({r.get('tier')})", 'escalations': escalations}
    except Exception as exc:  # noqa: BLE001
        escalations.append({'tier': 'fetch_page.py', 'reason': f'{type(exc).__name__}: {str(exc)[:160]}'})
    return {'title': '', 'h1': [], 'h2': [], 'h3': [], 'text': '', 'word_count': 0,
            'fetched_by': None, 'escalations': escalations}


# --------------------------------------------------------------------------- SERP sources

def _thruuu_key() -> str:
    key = os.environ.get('THRUUU_API_KEY', '').strip()
    if key:
        return key
    for path in dfs._env_candidates():
        if os.path.isfile(path):
            with open(path, encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    line = line.strip().removeprefix('export ').lstrip()
                    if line.startswith('THRUUU_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"').strip("'")
    return ''


THRUUU_ENGINES = {"AU": "google.com.au", "US": "google.com", "GB": "google.co.uk", "UK": "google.co.uk",
                  "NZ": "google.co.nz", "CA": "google.ca", "IE": "google.ie", "SG": "google.com.sg",
                  "IN": "google.co.in", "ZA": "google.co.za"}


def _thruuu_call(path: str, key: str, payload=None) -> tuple[int, object]:
    import urllib.error
    import urllib.request
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request("https://api.thruuu.com/api/v2" + path, data=data,
                                 method="POST" if data else "GET",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except ValueError:
            return e.code, {"success": False, "message": f"HTTP {e.code}"}


def thruuu_serp(keyword: str, country: str, key: str, max_wait: int = 180, poll: int = 15) -> list[dict]:
    """Optional extra: Thruuu SERP analysis (only when THRUUU_API_KEY is set and DataForSEO is not).
    Same calls as the previous Thruuu builder: POST /serps, then walk the oldest-first /serps
    list to the end (last match is newest) and GET /serps/<id>."""
    params = {"search_engine": THRUUU_ENGINES.get(country.upper(), "google.com"), "country": country.upper(),
              "language": "en", "device": "desktop", "num": 10, "search_volume": True,
              "analyze_headings": True, "analyze_top_topics": True}
    status, data = _thruuu_call("/serps", key, {"keywords": [keyword], "parameters": params,
                                                "reference": keyword.replace(' ', '-'),
                                                "minified_response": False})
    if not (isinstance(data, dict) and data.get("success")):
        raise RuntimeError(f"Thruuu trigger failed: {(data or {}).get('message', status)}")
    start = time.time()
    while time.time() - start < max_wait:
        sid = None
        for page in range(1, 101):
            _, rows = _thruuu_call(f"/serps?page={page}&itemsPerPage=100", key)
            if not rows:
                break
            for item in rows:
                if (item.get("query") or "").lower() == keyword.lower():
                    sid = item["id"]
        if sid:
            st, full = _thruuu_call(f"/serps/{sid}", key)
            if st == 200 and isinstance(full, dict) and full.get("result"):
                return [{"position": r.get("position"), "url": r.get("url"), "title": r.get("title"),
                         "domain": urlparse(r.get("url") or "").netloc, "thruuu": {
                             "h1": r.get("h1", []), "h2": r.get("h2", []), "h3": r.get("h3", []),
                             "word_count": r.get("wordCount", 0)}} for r in full["result"]]
        time.sleep(poll)
    raise RuntimeError(f"Thruuu analysis did not finish within {max_wait}s")


SKIP_DOMAINS = ('youtube.com', 'facebook.com', 'instagram.com', 'tiktok.com', 'twitter.com', 'x.com',
                'linkedin.com', 'pinterest.')


def analyse(keyword: str, country: str = "au", theme_keywords: dict | None = None,
            priority: tuple = (), top: int = 10, urls: list[str] | None = None,
            min_word_count: int = 300, cache_dir: str | None = None, use_cache: bool = True) -> dict:
    """Full pipeline. Never raises for a missing provider: gaps are reported in the result."""
    cache_dir = cache_dir or tempfile.gettempdir()
    slug = re.sub(r'[^a-z0-9]+', '_', keyword.lower()).strip('_')
    cache_file = os.path.join(cache_dir, f"serp_{country.lower()}_{slug}.json")
    if use_cache and not urls and os.path.isfile(cache_file):
        with open(cache_file, encoding='utf-8') as fh:
            cached = json.load(fh)
        if cached.get('competitors'):
            cached['from_cache'] = cache_file
            cached['cost_usd'] = 0.0
            return cached

    gaps: list[str] = []
    cost_before = dfs.TOTAL_COST
    serp_rows: list[dict] = []
    serp_extra: dict = {}
    provider = None

    if urls:
        provider = 'manual URLs (approximate: from WebSearch, not a located SERP)'
        serp_rows = [{"position": i + 1, "url": u, "title": "", "domain": urlparse(u).netloc}
                     for i, u in enumerate(urls[:top])]
    else:
        login, password = dfs.find_credentials()
        if login and password:
            try:
                s = dfs.serp(keyword, country, depth=top, login=login, password=password)
                serp_rows = s['organic']
                serp_extra = {k: s[k] for k in ('ai_overview', 'people_also_ask', 'featured_snippet', 'item_types')}
                provider = 'DataForSEO SERP'
            except dfs.DataForSEOError as e:
                gaps.append(f"DataForSEO SERP failed: {e}")
        else:
            gaps.append("Not available (no DATAFORSEO key): top 10 SERP. Run WebSearch for the "
                        "keyword and pass the result URLs with --urls (labelled approximate).")
        if not serp_rows:
            key = _thruuu_key()
            if key:
                try:
                    serp_rows = thruuu_serp(keyword, country, key)
                    provider = 'Thruuu (optional extra)'
                except Exception as e:  # noqa: BLE001
                    gaps.append(f"Thruuu failed: {type(e).__name__}: {str(e)[:160]}")

    competitors, needs_webfetch, skipped = [], [], []
    texts = []
    for row in serp_rows:
        url = row.get('url') or ''
        if not url or any(d in urlparse(url).netloc for d in SKIP_DOMAINS):
            skipped.append({'url': url, 'reason': 'video or social result'})
            continue
        page = fetch_page_text(url)
        th = row.get('thruuu') or {}
        if not page['fetched_by'] and th.get('h2'):
            page.update({'h1': th.get('h1', []), 'h2': th.get('h2', []), 'h3': th.get('h3', []),
                         'word_count': th.get('word_count', 0), 'fetched_by': 'thruuu headings'})
        if not page['fetched_by']:
            needs_webfetch.append(url)
            continue
        h2 = [h for h in page['h2'] if not is_noise(h)]
        h3 = [h for h in page['h3'] if not is_noise(h)]
        if page['word_count'] < min_word_count or not h2:
            skipped.append({'url': url, 'reason': f"{page['word_count']} words, {len(h2)} usable H2s"})
            continue
        if page.get('text'):
            texts.append(page['text'])
        competitors.append({'position': row.get('position'), 'url': url,
                            'title': row.get('title') or page.get('title', ''),
                            'word_count': page['word_count'], 'h1': page['h1'][:3], 'h2': h2, 'h3': h3,
                            'fetched_by': page['fetched_by']})

    if not scrapling_cli():
        gaps.append("Scrapling CLI not installed: pages were fetched with fetch_page.py tiers "
                    "(install Scrapling for the free path: uv tool install 'scrapling[shell]').")
    if needs_webfetch:
        gaps.append(f"{len(needs_webfetch)} page(s) could not be fetched locally: read them with "
                    "WebFetch if their headings matter (see needs_webfetch).")

    theme_counts, theme_examples = cluster_themes(competitors, theme_keywords, priority)
    page_counts = theme_page_counts(competitors, theme_keywords, priority)
    exclude = set(_tokens(keyword)) | {keyword.lower()}
    terms = extract_terms(texts, exclude=exclude) if len(texts) >= 2 else []
    if len(texts) < 2:
        gaps.append("Term targets need at least 2 fetched pages: none extracted.")

    result = {
        'keyword': keyword, 'country': country.lower(), 'serp_provider': provider,
        'serp': serp_rows, **serp_extra,
        'competitors': competitors, 'theme_counts': theme_counts, 'theme_page_counts': page_counts,
        'theme_examples': theme_examples, 'word_count_stats': word_count_stats(competitors),
        'terms': terms, 'skipped': skipped, 'needs_webfetch': needs_webfetch, 'gaps': gaps,
        'cost_usd': round(dfs.TOTAL_COST - cost_before, 4),
    }
    if competitors and not urls:
        try:
            with open(cache_file, 'w', encoding='utf-8') as fh:
                json.dump(result, fh, indent=2, ensure_ascii=False)
            result['cache_file'] = cache_file
        except OSError:
            pass
    return result


def terms_markdown(terms: list[dict], limit: int = 30) -> str:
    """Writer-facing term targets, Surfer style: `term (min-max)` with the page count."""
    if not terms:
        return "Not available (fewer than 2 competitor pages fetched)."
    return "\n".join(f"- {t['term']} ({t['min']}-{t['max']}, used by {t['pages']} pages)"
                     for t in terms[:limit])


def run_cli(theme_keywords: dict | None = None, priority: tuple = (), prog: str | None = None,
            description: str | None = None, argv=None) -> int:
    ap = argparse.ArgumentParser(prog=prog, description=description or __doc__.split("\n\n")[0])
    ap.add_argument("keyword", nargs="?", help="primary keyword")
    ap.add_argument("--country", default="au", help="2-letter market (default au)")
    ap.add_argument("--top", type=int, default=10, help="SERP results to analyse (default 10)")
    ap.add_argument("--urls", default=None,
                    help="comma-separated URLs to analyse instead of a SERP call (the no-key path)")
    ap.add_argument("--cache-dir", default=None, help="cache folder (default: system temp dir)")
    ap.add_argument("--no-cache", action="store_true", help="ignore a cached result")
    ap.add_argument("--terms-md", action="store_true", help="print the term targets as Markdown bullets")
    ap.add_argument("--extract-file", default=None, help="extract headings + word count from one HTML file")
    a = ap.parse_args(argv)
    if a.extract_file:
        with open(a.extract_file, encoding='utf-8', errors='replace') as fh:
            ex = extract_html(fh.read())
        ex.pop('text', None)
        print(json.dumps(ex, indent=2, ensure_ascii=False))
        return 0
    if not a.keyword:
        ap.error("keyword is required")
    urls = [u.strip() for u in a.urls.split(",") if u.strip()] if a.urls else None
    print(f"Analysing SERP: {a.keyword} ({a.country})", file=sys.stderr)
    res = analyse(a.keyword, a.country, theme_keywords, priority, a.top, urls,
                  cache_dir=a.cache_dir, use_cache=not a.no_cache)
    if a.terms_md:
        print(terms_markdown(res['terms']))
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    for g in res['gaps']:
        print(f"[gap] {g}", file=sys.stderr)
    print(f"[cost] DataForSEO ${res['cost_usd']:.4f}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(run_cli())
