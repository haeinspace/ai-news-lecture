#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_html.py — AI 강의 뉴스 큐레이션 사이트 생성기

data/entries-*.json 파일을 전부 읽어서 다음 페이지를 만든다:
  index.html             최근 30일 항목 (최신순 카드) + 검색 + 카테고리 필터
  archive/index.html     존재하는 모든 월(YYYY-MM) 목록
  archive/YYYY-MM.html   각 월 전체 항목

이 스크립트는 최초 1회 작성된 것이며 다시 고쳐 쓰지 않는다.
사용법:  python3 generate_html.py   (언제든 그대로 재실행)
"""
import json
import html
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = ROOT / "archive"

RECENT_DAYS = 30

CATEGORY_LABEL = {"news": "뉴스", "story": "이야기"}
CONFIDENCE_LABEL = {"verified": "검증됨", "unverified_but_fun": "미검증·재미사례"}

CSS = """
:root {
  --bg: #10141b; --panel: #1a2130; --text: #e6ebf4; --muted: #8b97ad;
  --news-a: #2b6cb0; --news-b: #1e3a5f; --story-a: #c05621; --story-b: #7b341e;
  --line: #2b3548; --accent: #63b3ed;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, "Apple SD Gothic Neo",
  "Noto Sans KR", "Malgun Gothic", sans-serif; background: var(--bg); color: var(--text); }
header { padding: 28px 20px 16px; max-width: 980px; margin: 0 auto; }
header h1 { margin: 0 0 6px; font-size: 1.5rem; }
header h1 a { color: var(--accent); text-decoration: none; }
.updated { color: var(--muted); font-size: .85rem; }
nav.topnav { margin-top: 10px; font-size: .9rem; }
nav.topnav a { color: var(--accent); margin-right: 14px; text-decoration: none; }
main { max-width: 980px; margin: 0 auto; padding: 8px 20px 48px; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 12px 0 20px; }
.controls input[type=search] { flex: 1 1 260px; padding: 10px 12px; border-radius: 8px;
  border: 1px solid var(--line); background: var(--panel); color: var(--text); font-size: .95rem; }
.filter-btn { padding: 8px 14px; border-radius: 8px; border: 1px solid var(--line);
  background: var(--panel); color: var(--text); cursor: pointer; font-size: .88rem; }
.filter-btn.active { border-color: var(--accent); color: var(--accent); }
.month-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.month-list a { display: block; padding: 18px 14px; background: var(--panel);
  border: 1px solid var(--line); border-radius: 10px; color: var(--text);
  text-decoration: none; font-size: 1.05rem; }
.month-list a:hover { border-color: var(--accent); }
.month-list .count { display: block; color: var(--muted); font-size: .8rem; margin-top: 4px; }
.card { background: var(--panel); border: 1px solid var(--line); border-left: 5px solid var(--muted);
  border-radius: 12px; padding: 16px 18px; margin-bottom: 14px; }
.card.news  { border-left-color: var(--news-a);
  background: linear-gradient(135deg, var(--news-b) 0%, var(--panel) 45%); }
.card.story { border-left-color: var(--story-a);
  background: linear-gradient(135deg, var(--story-b) 0%, var(--panel) 45%); }
.card .meta { display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  color: var(--muted); font-size: .8rem; margin-bottom: 8px; }
.badge { padding: 2px 9px; border-radius: 999px; font-weight: 600; font-size: .74rem; }
.card.news .badge  { background: var(--news-a); color: #fff; }
.card.story .badge { background: var(--story-a); color: #fff; }
.card h3 { margin: 0 0 8px; font-size: 1.06rem; line-height: 1.4; }
.card .summary { margin: 0 0 8px; line-height: 1.6; font-size: .93rem; }
.card .why { margin: 0 0 10px; color: #ffd580; font-size: .87rem; line-height: 1.5; }
.card .foot { display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
  justify-content: space-between; border-top: 1px solid var(--line); padding-top: 10px; }
.card .foot a { color: var(--accent); font-size: .84rem; text-decoration: none; word-break: break-all; }
.card .foot a:hover { text-decoration: underline; }
.conf { font-size: .74rem; color: var(--muted); border: 1px solid var(--line);
  padding: 2px 8px; border-radius: 999px; }
.empty { color: var(--muted); padding: 30px 0; text-align: center; }
footer.page { max-width: 980px; margin: 0 auto; padding: 0 20px 30px;
  color: var(--muted); font-size: .78rem; }
"""

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <h1><a href="@@HREF_INDEX@@">AI 강의 뉴스 큐레이션</a></h1>
  <div class="updated">마지막 업데이트: @@LAST_UPDATED@@</div>
  <nav class="topnav">
    <a href="@@HREF_INDEX@@">최신 (최근 30일)</a>
    <a href="@@HREF_ARCHIVE@@">지난 아카이브 보기</a>
  </nav>
</header>
<main>
@@CONTROLS@@
@@CONTENT@@
</main>
<footer class="page">생성형 AI 활용 강의용 뉴스·이야기 모음 · 생성일 @@GEN_DATE@@</footer>
<script>
(function () {
  var q = document.getElementById('q');
  var btns = document.querySelectorAll('.filter-btn');
  var cat = 'all';
  function apply() {
    var needle = (q && q.value ? q.value : '').toLowerCase();
    document.querySelectorAll('.card').forEach(function (c) {
      var okCat = cat === 'all' || c.getAttribute('data-category') === cat;
      var hay = (c.getAttribute('data-search') || '').toLowerCase();
      var okText = !needle || hay.indexOf(needle) !== -1;
      c.style.display = (okCat && okText) ? '' : 'none';
    });
  }
  if (q) q.addEventListener('input', apply);
  btns.forEach(function (b) {
    b.addEventListener('click', function () {
      cat = b.getAttribute('data-f');
      btns.forEach(function (x) { x.classList.toggle('active', x === b); });
      apply();
    });
  });
})();
</script>
</body>
</html>
"""

CONTROLS_HTML = """<div class="controls">
  <input type="search" id="q" placeholder="제목·요약·코멘트 검색…">
  <button class="filter-btn active" data-f="all">전체</button>
  <button class="filter-btn" data-f="news">뉴스만 보기</button>
  <button class="filter-btn" data-f="story">이야기만 보기</button>
</div>"""


def load_entries():
    """data/entries-*.json 전체를 읽고 (date, id) 기준 최신순으로 정렬해 반환."""
    entries = []
    if DATA_DIR.is_dir():
        for f in sorted(DATA_DIR.glob("entries-*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = []
            if isinstance(data, list):
                for e in data:
                    if isinstance(e, dict) and e.get("title"):
                        entries.append(e)
    entries.sort(key=lambda e: (str(e.get("date", "")), str(e.get("id", ""))), reverse=True)
    return entries


def month_of(entry):
    d = str(entry.get("date", ""))
    return d[:7] if len(d) >= 7 else "unknown"


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def source_host(url):
    u = str(url or "")
    for prefix in ("https://", "http://", "www."):
        if u.startswith(prefix):
            u = u[len(prefix):]
    return u.split("/")[0] or u


def card_html(e):
    cat = e.get("category", "news")
    if cat not in CATEGORY_LABEL:
        cat = "news"
    hay = " ".join(str(e.get(k, "")) for k in ("title", "summary", "why_interesting"))
    url = str(e.get("source_url", ""))
    conf = CONFIDENCE_LABEL.get(e.get("confidence", ""), esc(e.get("confidence", "")))
    return (
        '<article class="card %s" data-category="%s" data-search="%s">\n'
        '  <div class="meta"><span class="badge">%s</span>'
        '<time>%s</time><span>%s</span></div>\n'
        "  <h3>%s</h3>\n"
        '  <p class="summary">%s</p>\n'
        '  <p class="why">💡 %s</p>\n'
        '  <div class="foot"><a href="%s" target="_blank" rel="noopener noreferrer">'
        "🔗 출처: %s</a><span class=\"conf\">%s</span></div>\n"
        "</article>"
    ) % (
        cat, cat, esc(hay),
        CATEGORY_LABEL[cat],
        esc(e.get("date", "")), esc(e.get("id", "")),
        esc(e.get("title", "")),
        esc(e.get("summary", "")),
        esc(e.get("why_interesting", "")),
        esc(url), esc(source_host(url)), conf,
    )


def render_page(title, content, last_updated, gen_date, href_index, href_archive, controls=""):
    out = PAGE_TEMPLATE
    for key, val in (("@@TITLE@@", esc(title)), ("@@CSS@@", CSS), ("@@CONTENT@@", content),
                     ("@@LAST_UPDATED@@", esc(last_updated)), ("@@GEN_DATE@@", gen_date),
                     ("@@HREF_INDEX@@", href_index), ("@@HREF_ARCHIVE@@", href_archive),
                     ("@@CONTROLS@@", controls)):
        out = out.replace(key, val)
    return out


def empty_box():
    return ('<div class="empty">아직 등록된 항목이 없습니다. '
            "data/entries-YYYY-MM.json 에 항목을 추가한 뒤 generate_html.py 를 다시 실행하세요.</div>")


def main():
    entries = load_entries()
    ARCHIVE_DIR.mkdir(exist_ok=True)

    today = date.today()
    gen_date = today.isoformat()
    dates = [str(e.get("date", "")) for e in entries if str(e.get("date", ""))[:1].isdigit()]
    last_updated = max(dates) if dates else gen_date

    months = sorted({month_of(e) for e in entries}, reverse=True)

    # 1) 월별 아카이브 페이지: archive/YYYY-MM.html
    counts = {}
    for m in months:
        m_entries = [e for e in entries if month_of(e) == m]
        counts[m] = len(m_entries)
        content = "\n".join(card_html(e) for e in m_entries) or empty_box()
        page = render_page(f"{m} 아카이브 — AI 강의 뉴스 큐레이션", content,
                           last_updated, gen_date, "../index.html", "index.html")
        (ARCHIVE_DIR / f"{m}.html").write_text(page, encoding="utf-8")

    # 2) 아카이브 인덱스: archive/index.html
    if months:
        links = "\n".join(
            '<a href="%s.html">%s<span class="count">%d개 항목</span></a>' % (m, m, counts[m])
            for m in months)
        content = '<div class="month-list">%s</div>' % links
    else:
        content = empty_box()
    page = render_page("지난 아카이브 — AI 강의 뉴스 큐레이션", content,
                       last_updated, gen_date, "../index.html", "index.html")
    (ARCHIVE_DIR / "index.html").write_text(page, encoding="utf-8")

    # 3) 메인은 최근 30일 항목 (최신순) + 검색/필터
    cutoff = (today - timedelta(days=RECENT_DAYS)).isoformat()
    recent = [e for e in entries if str(e.get("date", "")) >= cutoff]
    content = "\n".join(card_html(e) for e in recent) or empty_box()
    content += ('\n<p style="margin-top:22px"><a style="color:var(--accent)" '
                'href="archive/index.html">← 지난 아카이브 보기</a></p>')
    page = render_page("AI 강의 뉴스 큐레이션", content,
                       last_updated, gen_date, "index.html", "archive/index.html",
                       controls=CONTROLS_HTML)
    (ROOT / "index.html").write_text(page, encoding="utf-8")

    print(f"생성 완료: index.html ({len(recent)}개 카드 / 전체 {len(entries)}개), "
          f"archive/index.html, 월별 {len(months)}개 ({', '.join(months) if months else '없음'})")


if __name__ == "__main__":
    main()
