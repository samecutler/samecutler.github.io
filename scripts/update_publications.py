#!/usr/bin/env python3
"""
Update Hugo/Wowchemy publication directories from a BibTeX file.

Usage:
    python3 scripts/update_publications.py path/to/export.bib

What it does:
  1. Parses the provided .bib file (abstracts optional but recommended).
  2. Deletes publication dirs that are no longer in the bib file
     (preserving any dirs listed in REUSE_DIRS, which hold featured images).
  3. Creates or updates each publication's index.md with clean text
     (LaTeX → Unicode, accented names, math symbols, etc.).
  4. Writes a cite.bib file in each publication directory.
  5. Updates the subtitle in content/home/publications.md with fresh counts.

Conventions used for Hugo/Wowchemy:
  - publication_types: ['2']  →  refereed journal article
  - publication_types: ['3']  →  arXiv preprint
  - featured: true            →  Cutler is first author
"""

import os, re, shutil, sys

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT  = os.path.dirname(SCRIPT_DIR)
PUB_DIR    = os.path.join(SITE_ROOT, 'content', 'publication')
WIDGET     = os.path.join(SITE_ROOT, 'content', 'home', 'publications.md')

# Existing publication dirs that hold featured images (main.png / main.jpg).
# Maps bib key → directory name.  These dirs are NEVER deleted; only their
# index.md is updated.
REUSE_DIRS = {
    'Cutler2025': 'a-2744-sizes',
    'Cutler2024': 'jwstsizes',
    'Cutler2023': 'insideout',
    'Cutler2022': 'dash',
}

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}

JOURNAL_MAP = {
    r'\apjl':  'The Astrophysical Journal Letters',
    r'\apj':   'The Astrophysical Journal',
    r'\apjs':  'The Astrophysical Journal Supplement Series',
    r'\mnras': 'Monthly Notices of the Royal Astronomical Society',
    r'\aap':   'Astronomy & Astrophysics',
    r'\nat':   'Nature',
    r'\nat.':  'Nature',
}

# {\ensuremath{X}} → symbol
ENSUREMATH = {
    r'\sim': '~',       r'\lesssim': '≲',   r'\gtrsim': '≳',
    r'\leq': '≤',       r'\geq': '≥',        r'\approx': '≈',
    r'\pm':  '±',       r'\Delta': 'Δ',      r'\alpha': 'α',
    r'\beta': 'β',      r'\lambda': 'λ',     r'\mu': 'μ',
    r'\odot': '☉',      r'\star': '★',       r'\propto': '∝',
    r'\sigma': 'σ',     r'\rho': 'ρ',        r'\xi': 'ξ',
    r'\langle': '⟨',    r'\rangle': '⟩',
    r'>': '>',          r'<': '<',            r'-': '-',
}

# ── LaTeX → plain text ────────────────────────────────────────────────────────

def latex_to_text(s):
    if not s:
        return s

    named = [
        (r"Labb{\'e}",          'Labbé'),
        (r"Brada{\v{c}}",       'Bradač'),
        (r"Maru{\v{s}}a",       'Maruša'),
        (r"F{\"o}rster",        'Förster'),
        (r"F{\"{o}}rster",      'Förster'),
        (r"{\'A}kos",           'Ákos'),
        (r"Ga{\"e}l",           'Gaël'),
        (r"St{\'e}phanie",      'Stéphanie'),
        (r"Ad{\`e}le",          'Adèle'),
        (r"{\'{e}}",            'é'),
        (r"{\'o}",              'ó'),
        (r"{\`{e}}",            'è'),
        (r"{\ensuremath{\sim}}",    '~'),
        (r"{\ensuremath{\lesssim}}", '≲'),
        (r"{\ensuremath{\gtrsim}}",  '≳'),
        (r"{\ensuremath{>}}",   '>'),
        (r"{\ensuremath{<}}",   '<'),
        (r"{\ensuremath{\leq}}", '≤'),
        (r"{\ensuremath{\geq}}", '≥'),
        (r"\textemdash",        '—'),
        (r"\textendash",        '–'),
        (r"\textasciitilde",    '~'),
        (r"\raisebox{-0.5ex}",  ''),
        (r"{\sim}",             '~'),
        (r"\sim",               '~'),
    ]
    for src, dst in named:
        s = s.replace(src, dst)

    # {\ensuremath{X}} → symbol table
    s = re.sub(r'\{\\ensuremath\{([^}]+)\}\}',
               lambda m: ENSUREMATH.get(m.group(1), m.group(1)), s)

    # Accented characters
    acute = {'a':'á','e':'é','i':'í','o':'ó','u':'ú','y':'ý',
             'A':'Á','E':'É','I':'Í','O':'Ó','U':'Ú','Y':'Ý',
             'c':'ć','C':'Ć','n':'ń','N':'Ń','s':'ś','S':'Ś','z':'ź','Z':'Ź'}
    s = re.sub(r"\{\\'(\{([A-Za-z])\}|([A-Za-z]))\}",
               lambda m: acute.get(m.group(2) or m.group(3),
                                   m.group(2) or m.group(3)), s)

    uml = {'a':'ä','e':'ë','i':'ï','o':'ö','u':'ü',
           'A':'Ä','E':'Ë','I':'Ï','O':'Ö','U':'Ü'}
    s = re.sub(r'\{\\"(\{([A-Za-z])\}|([A-Za-z]))\}',
               lambda m: uml.get(m.group(2) or m.group(3),
                                 m.group(2) or m.group(3)), s)

    grave = {'a':'à','e':'è','i':'ì','o':'ò','u':'ù',
             'A':'À','E':'È','I':'Ì','O':'Ò','U':'Ù'}
    s = re.sub(r'\{\\`(\{([A-Za-z])\}|([A-Za-z]))\}',
               lambda m: grave.get(m.group(2) or m.group(3),
                                   m.group(2) or m.group(3)), s)

    caron = {'c':'č','C':'Č','s':'š','S':'Š','z':'ž','Z':'Ž',
             'n':'ň','N':'Ň','r':'ř','R':'Ř'}
    s = re.sub(r'\{\\v\{([A-Za-z])\}\}',
               lambda m: caron.get(m.group(1), m.group(1)), s)

    s = re.sub(r'\{\\c\{([A-Za-z])\}\}',
               lambda m: {'c':'ç','C':'Ç','s':'ş','S':'Ş'}.get(
                   m.group(1), m.group(1)), s)

    circ = {'a':'â','e':'ê','i':'î','o':'ô','u':'û',
            'A':'Â','E':'Ê','I':'Î','O':'Ô','U':'Û'}
    s = re.sub(r'\{\\\^\{([A-Za-z])\}\}',
               lambda m: circ.get(m.group(1), m.group(1)), s)

    # Strip remaining braces iteratively
    for _ in range(5):
        ns = re.sub(r'\{([^{}]*)\}', r'\1', s)
        if ns == s:
            break
        s = ns
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# ── BibTeX field extraction ───────────────────────────────────────────────────

def get_field(name, text):
    pattern = rf'(?<![a-zA-Z]){re.escape(name)}\s*=\s*'
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    start = m.end()
    if start >= len(text):
        return None
    ch = text[start]
    if ch == '{':
        depth = 0
        for i, c in enumerate(text[start:]):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[start + 1:start + i]
    elif ch == '"':
        end = text.index('"', start + 1)
        return text[start + 1:end]
    else:
        m2 = re.match(r'(\S+)', text[start:])
        if m2:
            return m2.group(1).rstrip(',')
    return None


# ── BibTeX file parser ────────────────────────────────────────────────────────

def parse_bib_file(path):
    """Return list of entry dicts with all relevant fields plus raw text."""
    with open(path, encoding='utf-8') as f:
        text = f.read()

    entries = []
    pat = re.compile(r'(@\w+\{(\w+),)(.*?)(?=\n@|\Z)', re.DOTALL)
    for m in pat.finditer(text):
        header, key, body = m.group(1), m.group(2), m.group(3)
        entry = {
            '_key':  key,
            '_raw':  (header + body).strip(),
            '_body': body,
        }
        for field in ['author', 'title', 'journal', 'year', 'month', 'volume',
                      'number', 'pages', 'eid', 'doi', 'eprint',
                      'archivePrefix', 'primaryClass', 'adsurl', 'abstract']:
            val = get_field(field, body)
            if val is not None:
                entry[field] = val.strip()
        entries.append(entry)
    return entries


# ── Author parsing ────────────────────────────────────────────────────────────

def parse_authors(author_field):
    parts = re.split(r'\s+and\s+', author_field, flags=re.IGNORECASE)
    authors = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if ',' not in p:
            authors.append(latex_to_text(p.strip('{}')))
            continue
        comma = p.index(',')
        last_raw = p[:comma].strip()
        # Strip exactly one layer of outer braces so inner LaTeX survives
        if last_raw.startswith('{') and last_raw.endswith('}'):
            last_raw = last_raw[1:-1]
        first = p[comma + 1:].strip()
        authors.append(latex_to_text(f'{first} {last_raw}'))
    return authors


# ── Slug generation ───────────────────────────────────────────────────────────

def make_slug(entry, used_slugs):
    key = entry['_key']
    if key in REUSE_DIRS:
        return REUSE_DIRS[key]

    authors_raw = entry.get('author', '')
    first = re.split(r'\s+and\s+', authors_raw, maxsplit=1,
                     flags=re.IGNORECASE)[0].strip()
    if ',' in first:
        last = first.split(',')[0].strip()
        if last.startswith('{') and last.endswith('}'):
            last = last[1:-1]
    else:
        last = first.strip('{} ')
    last = re.sub(r'[^a-z0-9]', '', latex_to_text(last).lower())

    year = entry.get('year', '0000').strip()
    base = f'{last}-{year}'

    if base not in used_slugs:
        used_slugs.add(base)
        return base

    # Disambiguate with first significant title word
    title = latex_to_text(entry.get('title', ''))
    skip = {'uncover', 'jwst', 'from', 'with', 'that', 'this', 'most', 'what',
            'toward', 'discovery', 'everything', 'measuring', 'taking',
            'evidence', 'efficient', 'investigating', 'quantifying'}
    for w in re.findall(r'[A-Za-z]{4,}', title):
        if w.lower() not in skip:
            cand = f'{base}-{w.lower()[:6]}'
            if cand not in used_slugs:
                used_slugs.add(cand)
                return cand

    for i in range(2, 20):
        cand = f'{base}-{i}'
        if cand not in used_slugs:
            used_slugs.add(cand)
            return cand
    return base


# ── Publication helpers ───────────────────────────────────────────────────────

def is_cutler_first(entry):
    first = re.split(r'\s+and\s+', entry.get('author', ''),
                     maxsplit=1, flags=re.IGNORECASE)[0]
    return 'Cutler' in first


def pub_type(entry):
    j = entry.get('journal', '').strip().strip('{}')
    return '3' if j == 'arXiv e-prints' else '2'


def format_journal(entry):
    j = entry.get('journal', '').strip().strip('{}')
    for k, v in JOURNAL_MAP.items():
        if j == k:
            return f'*{v}*'
    return 'arXiv e-prints' if j == 'arXiv e-prints' else (f'*{j}*' if j else '')


# ── index.md builder ─────────────────────────────────────────────────────────

def make_index_md(entry):
    title      = latex_to_text(entry.get('title', ''))
    title_yaml = title.replace("'", "''")

    authors      = parse_authors(entry.get('author', ''))
    authors_yaml = '\n'.join(f'- {a}' for a in authors)

    year  = entry.get('year', '2020')
    month = MONTH_MAP.get(entry.get('month', 'jan').lower()[:3], '01')
    date  = f'{year}-{month}-01'

    abstract_raw  = latex_to_text(entry.get('abstract', ''))
    abstract_yaml = abstract_raw.replace("'", "''")

    featured       = 'true' if is_cutler_first(entry) else 'false'
    pub_type_code  = pub_type(entry)
    journal_str    = format_journal(entry)
    doi            = entry.get('doi', '')
    eprint         = entry.get('eprint', '')

    links = ''
    if eprint:
        links = f"""links:
- name: arXiv
  url: https://arxiv.org/abs/{eprint}
"""

    return f"""---
title: '{title_yaml}'

authors:
{authors_yaml}

author_notes: []

date: '{date}'

publishDate: '2026-10-07T00:00:00Z'

publication_types:
- '{pub_type_code}'

publication: '{journal_str}'
publication_short: ''

doi: {doi}

abstract: '{abstract_yaml}'

summary: ''

tags: []

featured: {featured}

url_pdf: ''
url_code: ''
url_dataset: ''
url_poster: ''
url_project: ''
url_slides: ''
url_source: ''
url_video: ''

image:
  caption: ''
  focal_point: ''
  preview_only: false

projects: []
{links}---
"""


# ── Publication count updater ─────────────────────────────────────────────────

def update_pub_counts(pub_dir, widget_path):
    refereed = first_author = 0
    for name in os.listdir(pub_dir):
        idx = os.path.join(pub_dir, name, 'index.md')
        if not os.path.isfile(idx):
            continue
        with open(idx, encoding='utf-8') as f:
            content = f.read()
        if re.search(r'^featured:\s*true',      content, re.MULTILINE):
            first_author += 1
        if re.search(r"publication_types:\n- '2'", content, re.MULTILINE):
            refereed += 1

    with open(widget_path, encoding='utf-8') as f:
        widget = f.read()

    new_subtitle = (f"subtitle: 'Total Refereed: {refereed}"
                    f" <br> As First Author: {first_author}'")
    updated = re.sub(r'^subtitle:.*$', new_subtitle, widget, flags=re.MULTILINE)

    if updated != widget:
        with open(widget_path, 'w', encoding='utf-8') as f:
            f.write(updated)

    print(f'  publications.md → Total Refereed: {refereed}, '
          f'As First Author: {first_author}')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(f'Usage: python3 {sys.argv[0]} path/to/export.bib', file=sys.stderr)
        sys.exit(1)

    bib_path = sys.argv[1]
    if not os.path.isfile(bib_path):
        print(f'ERROR: bib file not found: {bib_path}', file=sys.stderr)
        sys.exit(1)

    print(f'Reading {bib_path} …')
    entries = parse_bib_file(bib_path)
    print(f'  Parsed {len(entries)} entries')

    # Build slug map
    used_slugs  = set()
    slug_map    = {}   # entry index → slug
    new_slug_set = set()
    for i, e in enumerate(entries):
        slug = make_slug(e, used_slugs)
        slug_map[i] = slug
        new_slug_set.add(slug)
        print(f'  {e["_key"]:20s} → {slug}')

    # ── Step 1: delete stale directories ──────────────────────────────────────
    existing = [d for d in os.listdir(PUB_DIR)
                if os.path.isdir(os.path.join(PUB_DIR, d))]
    to_delete = [d for d in existing if d not in new_slug_set]

    if to_delete:
        print(f'\nDeleting {len(to_delete)} stale directories:')
        for d in sorted(to_delete):
            print(f'  DELETE {d}')
            shutil.rmtree(os.path.join(PUB_DIR, d))
    else:
        print('\nNo stale directories to delete.')

    # ── Step 2: create / update each publication ───────────────────────────────
    print(f'\nWriting {len(entries)} publication directories:')
    has_abstract = sum(1 for e in entries if e.get('abstract'))
    for i, entry in enumerate(entries):
        slug     = slug_map[i]
        dir_path = os.path.join(PUB_DIR, slug)
        os.makedirs(dir_path, exist_ok=True)

        # index.md
        with open(os.path.join(dir_path, 'index.md'), 'w', encoding='utf-8') as f:
            f.write(make_index_md(entry))

        # cite.bib
        with open(os.path.join(dir_path, 'cite.bib'), 'w', encoding='utf-8') as f:
            f.write(entry['_raw'] + '\n')

        tag = '[1st author]' if is_cutler_first(entry) else ''
        print(f'  {slug} {tag}')

    print(f'\n  ({has_abstract}/{len(entries)} entries had abstracts)')

    # ── Step 3: refresh publication counts in homepage widget ─────────────────
    print('\nUpdating publication counts …')
    update_pub_counts(PUB_DIR, WIDGET)

    print('\nDone.')


if __name__ == '__main__':
    main()
