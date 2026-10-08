#!/usr/bin/env python3
"""
Count publications and update the subtitle in content/home/publications.md.

Counts:
  - Refereed: publication_types: ['2'] (journal article, not arXiv preprint)
  - First author: featured: true  (set for Cutler first-author papers)

Run this before `hugo` or `hugo server`.
"""
import os, re, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT  = os.path.dirname(SCRIPT_DIR)   # scripts/ lives one level inside the repo
PUB_DIR    = os.path.join(SITE_ROOT, 'content', 'publication')
WIDGET     = os.path.join(SITE_ROOT, 'content', 'home', 'publications.md')


def count_publications(pub_dir):
    refereed = 0
    first_author = 0
    for name in os.listdir(pub_dir):
        idx = os.path.join(pub_dir, name, 'index.md')
        if not os.path.isfile(idx):
            continue
        with open(idx, encoding='utf-8') as f:
            content = f.read()
        if re.search(r'^featured:\s*true', content, re.MULTILINE):
            first_author += 1
        if re.search(r"publication_types:\n- '2'", content, re.MULTILINE):
            refereed += 1
    return refereed, first_author


def update_widget(widget_path, refereed, first_author):
    with open(widget_path, encoding='utf-8') as f:
        content = f.read()

    new_subtitle = f"subtitle: 'Total Refereed: {refereed} <br> As First Author: {first_author}'"
    updated = re.sub(
        r"^subtitle:.*$",
        new_subtitle,
        content,
        flags=re.MULTILINE
    )

    if updated == content:
        print(f"publications.md subtitle already up-to-date ({refereed} refereed, {first_author} first-author)")
        return

    with open(widget_path, 'w', encoding='utf-8') as f:
        f.write(updated)
    print(f"Updated publications.md: Total Refereed: {refereed}, As First Author: {first_author}")


if __name__ == '__main__':
    if not os.path.isdir(PUB_DIR):
        print(f"ERROR: publication dir not found: {PUB_DIR}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(WIDGET):
        print(f"ERROR: widget file not found: {WIDGET}", file=sys.stderr)
        sys.exit(1)

    refereed, first_author = count_publications(PUB_DIR)
    update_widget(WIDGET, refereed, first_author)
