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

CATEGORY_LABEL = {"news": "뉴스", "story": "이야기", "paper": "논문"}
CONFIDENCE_LABEL = {"verified": "검증됨", "unverified_but_fun": "미검증·재미사례"}

CSS = """
/* Design v2 (2026-10-07, user-ordered redesign) — Notion식 밝고 깔끔한 톤:
   흰 카드 + 속삭임 테두리(rgba(0,0,0,.1)) + 다층 부드러운 섀도 + 틴티드 pill 배지 */
:root {
  --bg: #f6f5f4; --panel: #ffffff; --text: rgba(0,0,0,.95); --muted: #615d59;
  --faint: #a39e98;
  --news: #0075de; --news-bg: #f2f9ff; --news-fg: #097fe8;
  --story: #dd5b00; --story-bg: #fff4ec; --story-fg: #b64b00;
  --paper: #1a8a34; --paper-bg: #eefaf1; --paper-fg: #157a2c;
  --line: rgba(0,0,0,.1); --accent: #0075de;
  --card-shadow: rgba(0,0,0,.04) 0 4px 18px, rgba(0,0,0,.027) 0 2px 7.8px,
    rgba(0,0,0,.02) 0 .8px 2.9px, rgba(0,0,0,.01) 0 .2px 1px;
  --card-shadow-hover: rgba(0,0,0,.06) 0 8px 26px, rgba(0,0,0,.03) 0 3px 10px,
    rgba(0,0,0,.02) 0 1px 3px;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: "Pretendard", "Inter", -apple-system, "Apple SD Gothic Neo",
  "Noto Sans KR", "Malgun Gothic", sans-serif; background: var(--bg); color: var(--text);
  -webkit-font-smoothing: antialiased; }
header { padding: 44px 24px 10px; max-width: 980px; margin: 0 auto; }
header h1 { margin: 0 0 6px; font-size: 1.72rem; font-weight: 700; letter-spacing: -0.5px; }
header h1 a { color: var(--text); text-decoration: none; }
.updated { color: var(--muted); font-size: .85rem; }
nav.topnav { margin-top: 14px; font-size: .9rem; }
nav.topnav a { color: var(--accent); margin-right: 16px; text-decoration: none; font-weight: 500; }
nav.topnav a:hover { text-decoration: underline; }
main { max-width: 980px; margin: 0 auto; padding: 14px 24px 56px; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 16px 0 24px;
  position: sticky; top: 0; z-index: 50; padding: 12px 0 10px;
  background: linear-gradient(var(--bg) 85%, rgba(246,245,244,0)); }
.controls-label { width: 100%; color: var(--muted); font-size: .78rem; font-weight: 600;
  letter-spacing: .3px; margin-bottom: 2px; }
.controls input[type=search] { flex: 1 1 260px; padding: 10px 14px; border-radius: 8px;
  border: 1px solid #dddddd; background: var(--panel); color: var(--text); font-size: .95rem; }
.controls input[type=search]:focus { outline: 2px solid #097fe8; outline-offset: 1px; border-color: transparent; }
.controls input[type=search]::placeholder { color: var(--faint); }
.filter-btn { padding: 8px 15px; border-radius: 999px; border: 1px solid var(--line);
  background: var(--panel); color: var(--muted); cursor: pointer; font-size: .86rem;
  font-weight: 500; transition: all .15s ease; }
.filter-btn:hover { color: var(--text); border-color: rgba(0,0,0,.25); }
.filter-btn.active { background: var(--news-bg); border-color: transparent; color: var(--news-fg);
  font-weight: 600; }
.month-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.month-list a { display: block; padding: 20px 16px; background: var(--panel);
  border: 1px solid var(--line); border-radius: 12px; color: var(--text);
  text-decoration: none; font-size: 1.05rem; font-weight: 600; letter-spacing: -0.2px;
  box-shadow: var(--card-shadow); transition: box-shadow .15s ease; }
.month-list a:hover { box-shadow: var(--card-shadow-hover); }
.month-list .count { display: block; color: var(--muted); font-size: .8rem;
  font-weight: 400; margin-top: 5px; }
/* Design v3 (2026-10-07, user-ordered): 컴팩트 리스트 — 한 줄 요약 행, 클릭 시 펼쳐짐 */
details.card { background: var(--panel); border: 1px solid var(--line); border-left: 3px solid var(--faint);
  border-radius: 10px; margin-bottom: 8px; box-shadow: var(--card-shadow); }
details.card:hover { box-shadow: var(--card-shadow-hover); }
details.card summary { list-style: none; cursor: pointer; display: flex; align-items: center;
  gap: 10px; padding: 12px 16px; outline-offset: -2px; }
details.card summary::-webkit-details-marker { display: none; }
details.card summary::after { content: "▸"; color: var(--faint); font-size: .8rem;
  margin-left: auto; transition: transform .15s ease; flex: 0 0 auto; }
details.card[open] summary::after { transform: rotate(90deg); }
details.card summary .row-date { color: var(--faint); font-size: .76rem; flex: 0 0 auto; }
details.card summary .row-title { font-weight: 600; font-size: .95rem; line-height: 1.4;
  letter-spacing: -0.2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  min-width: 0; }
details.card .body { padding: 2px 18px 14px 18px; border-top: 1px solid var(--line); }
details.card .body .summary { margin-top: 12px; }
.card.news  { border-left-color: var(--news); }
.card.story { border-left-color: var(--story); }
.card.paper { border-left-color: var(--paper); }
.card .meta { display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  color: var(--faint); font-size: .78rem; margin: 12px 0 10px; }
.badge { padding: 3px 10px; border-radius: 999px; font-weight: 600; font-size: .72rem;
  letter-spacing: .1px; }
.card.news .badge  { background: var(--news-bg); color: var(--news-fg); }
.card.story .badge { background: var(--story-bg); color: var(--story-fg); }
.card.paper .badge { background: var(--paper-bg); color: var(--paper-fg); }
.card h3 { margin: 0 0 9px; font-size: 1.08rem; line-height: 1.4; font-weight: 700;
  letter-spacing: -0.25px; }
.card .summary { margin: 0 0 9px; line-height: 1.65; font-size: .93rem; color: var(--text); }
.card .why { margin: 0 0 12px; color: #8a5a00; font-size: .87rem; line-height: 1.55;
  background: #fdf7ea; border-radius: 8px; padding: 8px 11px; }
.card .foot { display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
  justify-content: space-between; border-top: 1px solid var(--line); padding-top: 11px; }
.card .foot a { color: var(--accent); font-size: .84rem; text-decoration: none; word-break: break-all; }
.card .foot a:hover { text-decoration: underline; }
.conf { font-size: .73rem; color: var(--muted); border: 1px solid var(--line);
  padding: 2px 9px; border-radius: 999px; background: #fafaf9; }
.empty { color: var(--muted); padding: 40px 0; text-align: center; }
.extra-links { margin: 0 0 12px; padding: 11px 13px; background: #fbfbfa;
  border: 1px dashed rgba(0,0,0,.16); border-radius: 10px; }
.extra-links .xl-head { color: var(--muted); font-size: .75rem; font-weight: 600;
  margin: 0 0 7px; letter-spacing: .1px; }
.extra-links ul { margin: 0; padding: 0; list-style: none; }
.extra-links li { margin: 5px 0; font-size: .86rem; line-height: 1.5; }
.extra-links li a { color: var(--accent); text-decoration: none; }
.extra-links li a:hover { text-decoration: underline; }
.extra-links .xl-note { color: var(--faint); font-size: .78rem; }
/* Design v4 (2026-10-07, user-ordered): 오늘자 항목만 3열 정사각형 그리드 */
.day-head { display: flex; align-items: baseline; gap: 10px; margin: 4px 0 12px; }
.day-head h2 { margin: 0; font-size: 1.05rem; font-weight: 700; letter-spacing: -0.3px; }
.day-head .day-sub { color: var(--faint); font-size: .78rem; }
.day-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 26px; }
@media (max-width: 760px) { .day-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px) { .day-grid { grid-template-columns: 1fr; } }
a.gcard { aspect-ratio: 1 / 1; background: var(--panel); border: 1px solid var(--line);
  border-left: 3px solid var(--faint); border-radius: 12px; padding: 14px 15px;
  display: flex; flex-direction: column; gap: 7px; overflow: hidden; text-decoration: none;
  color: var(--text); box-shadow: var(--card-shadow); transition: box-shadow .15s ease; }
a.gcard:hover { box-shadow: var(--card-shadow-hover); }
a.gcard.news  { border-left-color: var(--news); }
a.gcard.story { border-left-color: var(--story); }
a.gcard.paper { border-left-color: var(--paper); }
.gcard .g-top { display: flex; align-items: center; gap: 8px; }
.gcard .badge { padding: 3px 10px; border-radius: 999px; font-weight: 600; font-size: .7rem;
  letter-spacing: .1px; flex: 0 0 auto; }
.gcard.news .badge  { background: var(--news-bg); color: var(--news-fg); }
.gcard.story .badge { background: var(--story-bg); color: var(--story-fg); }
.gcard.paper .badge { background: var(--paper-bg); color: var(--paper-fg); }
.gcard time { color: var(--faint); font-size: .72rem; }
.gcard h3 { margin: 0; font-size: .95rem; line-height: 1.38; font-weight: 700;
  letter-spacing: -0.2px; display: -webkit-box; -webkit-line-clamp: 3;
  -webkit-box-orient: vertical; overflow: hidden; }
.gcard .g-summary { margin: 0; color: var(--muted); font-size: .8rem; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; }
.gcard .g-foot { margin-top: auto; padding-top: 8px; border-top: 1px solid var(--line);
  display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.gcard .g-foot span:first-child { color: var(--accent); font-size: .76rem;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.gcard .conf { font-size: .66rem; flex: 0 0 auto; }
footer.page { max-width: 980px; margin: 0 auto; padding: 0 24px 36px;
  color: var(--faint); font-size: .78rem; }
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
      var show = okCat && okText;
      c.style.display = show ? '' : 'none';
      // 검색어에 걸린 항목은 자동으로 펼침 (v3 compact list)
      if (needle && show && c.tagName === 'DETAILS') c.open = true;
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
  <span class="controls-label">🔍 검색 · 분류 필터</span>
  <input type="search" id="q" placeholder="제목·요약·코멘트 검색…">
  <button class="filter-btn active" data-f="all">전체</button>
  <button class="filter-btn" data-f="news">뉴스만 보기</button>
  <button class="filter-btn" data-f="story">이야기만 보기</button>
  <button class="filter-btn" data-f="paper">논문만 보기</button>
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


def extra_links_html(e):
    """optional per-day extra_links: [{title,url,comment?}] -> dashed link box."""
    xl = e.get("extra_links")
    if not isinstance(xl, list) or not xl:
        return ""
    items = []
    for ln in xl:
        if not isinstance(ln, dict):
            continue
        note = str(ln.get("comment", "")).strip()
        items.append(
            '<li><a href="%s" target="_blank" rel="noopener noreferrer">%s</a>%s</li>'
            % (esc(ln.get("url", "")), esc(ln.get("title", "")),
               (' <span class="xl-note">— %s</span>' % esc(note)) if note else "")
        )
    if not items:
        return ""
    return ('<div class="extra-links"><p class="xl-head">📎 참고할 만한 다른 AI 기사</p>'
            '<ul>%s</ul></div>' % "".join(items))


def grid_card_html(e):
    """v4: 오늘자 항목용 정사각형 그리드 카드 (클릭 시 출처 페이지로 이동)."""
    cat = e.get("category", "news")
    if cat not in CATEGORY_LABEL:
        cat = "news"
    hay = " ".join(str(e.get(k, "")) for k in ("title", "summary", "why_interesting"))
    for ln in (e.get("extra_links") or []):
        if isinstance(ln, dict):
            hay += " " + str(ln.get("title", "")) + " " + str(ln.get("comment", ""))
    url = str(e.get("source_url", ""))
    conf = CONFIDENCE_LABEL.get(e.get("confidence", ""), esc(e.get("confidence", "")))
    return (
        '<a class="card gcard %s" data-category="%s" data-search="%s" href="%s" '
        'target="_blank" rel="noopener noreferrer">\n'
        '  <span class="g-top"><span class="badge">%s</span><time>%s</time></span>\n'
        "  <h3>%s</h3>\n"
        '  <p class="g-summary">%s</p>\n'
        '  <span class="g-foot"><span>🔗 %s</span><span class="conf">%s</span></span>\n'
        "</a>"
    ) % (
        cat, cat, esc(hay), esc(url),
        CATEGORY_LABEL[cat], esc(e.get("date", "")),
        esc(e.get("title", "")),
        esc(e.get("summary", "")),
        esc(source_host(url)), conf,
    )


def card_html(e):
    cat = e.get("category", "news")
    if cat not in CATEGORY_LABEL:
        cat = "news"
    hay = " ".join(str(e.get(k, "")) for k in ("title", "summary", "why_interesting"))
    for ln in (e.get("extra_links") or []):
        if isinstance(ln, dict):
            hay += " " + str(ln.get("title", "")) + " " + str(ln.get("comment", ""))
    url = str(e.get("source_url", ""))
    conf = CONFIDENCE_LABEL.get(e.get("confidence", ""), esc(e.get("confidence", "")))
    return (
        '<details class="card %s" data-category="%s" data-search="%s">\n'
        '  <summary><span class="badge">%s</span>'
        '<time class="row-date">%s</time>'
        '<span class="row-title">%s</span></summary>\n'
        '  <div class="body">\n'
        '  <div class="meta"><time>%s</time><span>%s</span></div>\n'
        '  <p class="summary">%s</p>\n'
        '  <p class="why">💡 %s</p>\n'
        "%s"
        '  <div class="foot"><a href="%s" target="_blank" rel="noopener noreferrer">'
        "🔗 출처: %s</a><span class=\"conf\">%s</span></div>\n"
        "  </div>\n"
        "</details>"
    ) % (
        cat, cat, esc(hay),
        CATEGORY_LABEL[cat],
        esc(e.get("date", "")),
        esc(e.get("title", "")),
        esc(e.get("date", "")), esc(e.get("id", "")),
        esc(e.get("summary", "")),
        esc(e.get("why_interesting", "")),
        extra_links_html(e),
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
    # v4: 가장 최신 날짜(보통 오늘자) 항목은 3열 정사각형 그리드로, 나머지는 컴팩트 리스트로
    cutoff = (today - timedelta(days=RECENT_DAYS)).isoformat()
    recent = [e for e in entries if str(e.get("date", "")) >= cutoff]
    today_entries = [e for e in recent if str(e.get("date", "")) == last_updated]
    older_entries = [e for e in recent if str(e.get("date", "")) < last_updated]
    parts = []
    if today_entries:
        parts.append('<div class="day-head"><h2>오늘 큐레이션 · %s</h2>'
                     '<span class="day-sub">%d개 항목</span></div>' % (esc(last_updated), len(today_entries)))
        parts.append('<div class="day-grid">%s</div>'
                     % "".join(grid_card_html(e) for e in today_entries))
    if older_entries:
        if today_entries:
            parts.append('<div class="day-head"><h2>지난 큐레이션</h2>'
                         '<span class="day-sub">클릭하면 펼쳐짐</span></div>')
        parts.append("\n".join(card_html(e) for e in older_entries))
    content = "\n".join(parts) or empty_box()
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
