#!/bin/sh
# Rebuild every generated part of the site, in dependency order. Stops on the first failure.
#   1. build_chapter.py  chapter-1.html (English) + content/chapter-1.zh.html from the manuscripts
#      build_posts.py    blog/<slug>.html from content/posts/*.json
#      build_blog.py     Writing index (blog.html) from data/posts.json
#      build_quotes.py   LinkedIn recommendations from data/testimonials.json
#   2. build_shell.py    launch phase on every page + shared header/footer on marked pages
#   3. build_zh.py       /zh/ mirror from the EN pages
#   4. build_fonts.py    Chinese display subset from .cjk-display text (EN + zh)
# Then run the tests:  /usr/bin/python3 -m unittest discover -s tests
set -e
cd "$(dirname "$0")"
PY=/usr/bin/python3
# The manuscript lives beside the main checkout (../../writing/...). Resolve the main
# checkout through git so this also works from a worktree under .claude/worktrees/.
REPO=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
MANUSCRIPT=${MANUSCRIPT:-"$REPO/../../writing/Claude_Book_Editing/Manuscript_v2.0_FINAL.docx"}
MANUSCRIPT_EN=${MANUSCRIPT_EN:-"$REPO/../../writing/Claude_Book_Editing/publishing/english/Manuscript_EN.docx"}
$PY build_chapters.py
$PY build_chapter.py "$MANUSCRIPT" "$MANUSCRIPT_EN"
$PY build_posts.py
$PY build_blog.py
$PY build_quotes.py
$PY build_shell.py
$PY build_zh.py
$PY build_fonts.py
