#!/usr/bin/env python3
"""강의계획서 Markdown -> 단일 HTML 빌드.

    python build.py 2026-2

src/{학기}.md 를 읽어 {학기}/index.html 로 출력하고, 루트 index.html(학기 목록)을
함께 갱신한다. 외부 파일·CDN·웹폰트 의존이 없는 HTML 한 장으로 완결된다.

HTML은 직접 수정하지 않는다. md를 고치고 다시 빌드한다.
"""

import html
import re
import sys
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# ---------------------------------------------------------------- 스타일 / 스크립트

CSS = r"""
:root{
  color-scheme:light dark;
  --bg:#ffffff; --fg:#1b1b1b; --muted:#5f6672; --line:#dcdfe4;
  --accent:#0b4f8f; --thead:#f2f4f7; --card:#fafbfc;
  --now-bg:#fff6e0; --now-line:#c07a00; --now-fg:#7a4a00;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#14171b; --fg:#e4e6e9; --muted:#9aa2ae; --line:#3f4650;
    --accent:#7fb6f0; --thead:#1e232a; --card:#191d23;
    --now-bg:#3a2e10; --now-line:#d69a2a; --now-fg:#f2d391;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0 auto; max-width:900px; padding:30px 22px 64px;
  background:var(--bg); color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",Roboto,"Helvetica Neue",Arial,sans-serif;
  font-size:17px; line-height:1.7; word-break:keep-all; overflow-wrap:break-word;
}
h1{font-size:1.85em; line-height:1.3; margin:0 0 .45em; letter-spacing:-.01em}
h2{font-size:1.35em; margin:2.2em 0 .6em; padding-bottom:.25em; border-bottom:2px solid var(--line)}
h3{font-size:1.12em; margin:1.9em 0 .5em}
h4{font-size:1em; margin:1.4em 0 .4em; color:var(--muted)}
p{margin:.7em 0}
a{color:var(--accent)}
hr{border:0; border-top:1px solid var(--line); margin:2.4em 0}
ul,ol{padding-left:1.35em}
li{margin:.3em 0}
h1+p{color:var(--muted); font-size:.95em; line-height:1.65}
h1+p strong{color:var(--fg)}
blockquote{margin:1.3em 0; padding:.7em 1.1em; border-left:4px solid var(--accent);
  background:var(--card); border-radius:0 6px 6px 0}
blockquote p{margin:.3em 0}
code{background:var(--thead); padding:.1em .35em; border-radius:4px; font-size:.92em}

/* ---- 목차 ---- */
#toc{margin:1.7em 0; border:1px solid var(--line); border-radius:8px; background:var(--card)}
#toc>summary{cursor:pointer; padding:.7em 1em; font-weight:700; list-style:none}
#toc>summary::-webkit-details-marker{display:none}
#toc>summary::before{content:"\25B8\00A0\00A0"; color:var(--muted)}
#toc[open]>summary::before{content:"\25BE\00A0\00A0"}
#toc .toc{padding:0 1.1em .9em}
#toc ul{margin:.2em 0; padding-left:1.1em; list-style:none}
#toc>.toc>ul{padding-left:0}
#toc li{margin:.18em 0}
#toc ul ul{font-size:.93em}
#toc ul ul a{color:var(--muted)}
#toc a{text-decoration:none}
#toc a:hover{text-decoration:underline}

/* ---- 표 ---- */
table{width:100%; border-collapse:collapse; margin:1.2em 0; font-size:.95em}
caption{position:absolute; width:1px; height:1px; margin:-1px; padding:0;
  overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0}
th,td{border-bottom:1px solid var(--line); padding:.6em .7em; text-align:left; vertical-align:top}
thead th{background:var(--thead); border-bottom:2px solid var(--line); font-weight:700; white-space:nowrap}
tbody tr.past{opacity:.6}
tbody tr.now{background:var(--now-bg)}
tbody tr.now td{border-bottom-color:var(--now-line)}
tbody tr.now td:first-child{border-left:4px solid var(--now-line); padding-left:calc(.7em - 4px)}
.badge{display:inline-block; margin-left:.5em; padding:.05em .55em; border:1px solid var(--now-line);
  border-radius:999px; background:var(--now-bg); color:var(--now-fg);
  font-size:.78em; font-weight:700; white-space:nowrap}

footer{margin-top:3.2em; padding-top:1em; border-top:1px solid var(--line);
  color:var(--muted); font-size:.9em}

/* ---- 좁은 화면: 4열 이상 표를 카드형으로 ---- */
@media (max-width:700px){
  body{font-size:16px; padding:22px 14px 48px}
  h1{font-size:1.5em}
  table.cards{font-size:1em; margin:1.1em 0}
  table.cards,table.cards tbody,table.cards tr,table.cards td{display:block; width:100%}
  table.cards thead{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0)}
  table.cards tr{margin:0 0 12px; padding:10px 12px; background:var(--card);
    border:1px solid var(--line); border-left:4px solid var(--line); border-radius:8px}
  table.cards td{border:0; padding:3px 0 3px 5.6em; display:block; position:relative}
  table.cards td::before{content:attr(data-label); position:absolute; left:0; top:3px;
    width:5em; color:var(--muted); font-weight:700; font-size:.86em; line-height:1.95}
  table.cards td:empty{display:none}
  table.cards tr.now{border-left-color:var(--now-line); background:var(--now-bg)}
  table.cards tr.now td:first-child{border-left:0; padding-left:5.6em}
}

/* ---- 인쇄 (A4) ---- */
@media print{
  :root{
    --bg:#fff; --fg:#000; --muted:#333; --line:#999; --accent:#000;
    --thead:#eee; --card:#fff; --now-bg:transparent; --now-line:#999; --now-fg:#000;
  }
  @page{size:A4; margin:16mm}
  body{max-width:none; padding:0; font-size:10.5pt; line-height:1.55}
  #toc{display:none}
  .badge{display:none}
  tbody tr.past{opacity:1}
  tbody tr.now{background:none}
  tbody tr.now td:first-child{border-left:0; padding-left:.7em}
  a{color:#000; text-decoration:none}
  table{font-size:9.5pt}
  thead{display:table-header-group}
  tr,thead,caption,blockquote,li{break-inside:avoid; page-break-inside:avoid}
  h1,h2,h3,h4{break-after:avoid; page-break-after:avoid}
}
"""

JS = r"""
(function(){
  var rows=Array.prototype.slice.call(document.querySelectorAll('tr[data-date]'));
  if(!rows.length)return;
  var n=new Date(), p=function(v){return (v<10?'0':'')+v;};
  var today=n.getFullYear()+'-'+p(n.getMonth()+1)+'-'+p(n.getDate()), next=null;
  rows.forEach(function(r){
    var d=r.getAttribute('data-date');
    if(d<today){r.className+=' past';} else if(!next){next=r;}
  });
  if(!next)return;
  var exact=next.getAttribute('data-date')===today;
  next.className+=' now';
  var cell=next.querySelector('[data-label="날짜"]')||next.cells[1]||next.cells[0];
  var b=document.createElement('span');
  b.className='badge';
  b.textContent=exact?'오늘':'다음 수업';
  cell.appendChild(b);
})();
"""

PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>__CSS__</style>
</head>
<body>
__BODY__
<footer><p>최종 수정: __BUILT__</p></footer>
<script>__JS__</script>
</body>
</html>
"""

# ---------------------------------------------------------------- 유틸

TAG_RE = re.compile(r"<[^>]+>")
TABLE_RE = re.compile(r"<table>(.*?)</table>", re.S)
THEAD_RE = re.compile(r"<thead>(.*?)</thead>", re.S)
TBODY_RE = re.compile(r"<tbody>(.*?)</tbody>", re.S)
TH_RE = re.compile(r"<th([^>]*)>(.*?)</th>", re.S)
TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TD_RE = re.compile(r"<td([^>]*)>(.*?)</td>", re.S)
HEAD_OR_TABLE_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>|<table>", re.S)
DATE_RE = re.compile(r"(\d{1,2})\s*/\s*(\d{1,2})")


def text_of(fragment):
    """태그를 걷어낸 순수 텍스트."""
    return html.unescape(TAG_RE.sub("", fragment)).strip()


def year_for(term, month):
    """학기 인자에서 해당 월의 연도를 유도한다. 2026-2 -> 9~12월은 2026년, 1~2월은 2027년."""
    year, half = term.split("-")
    year = int(year)
    if half == "2":
        return year if month >= 7 else year + 1
    return year


def table_captions(body):
    """각 표 바로 앞의 제목을 caption 문구로 쓴다. 같은 제목 아래 여러 표면 번호를 붙인다."""
    caps, current, seen = [], "표", {}
    for m in HEAD_OR_TABLE_RE.finditer(body):
        if m.group(1):
            current = text_of(m.group(2))
        else:
            seen[current] = seen.get(current, 0) + 1
            caps.append(current if seen[current] == 1 else "%s — 표 %d" % (current, seen[current]))
    return caps


def rewrite_tables(body, term):
    """caption/scope 부여, 4열 이상 표에 data-label, 날짜 셀에서 tr[data-date] 생성."""
    caps = table_captions(body)
    counter = [0]

    def one_table(tm):
        inner = tm.group(1)
        hm, bm = THEAD_RE.search(inner), TBODY_RE.search(inner)
        head, tbody = (hm.group(1) if hm else ""), (bm.group(1) if bm else "")
        headers = [text_of(c) for _, c in TH_RE.findall(head)]
        cards = len(headers) >= 4
        date_col = headers.index("날짜") if "날짜" in headers else -1

        new_head = TH_RE.sub(lambda m: '<th scope="col"%s>%s</th>' % (m.group(1), m.group(2)), head)

        def one_row(rm):
            cells = TD_RE.findall(rm.group(1))
            out = []
            for i, (attrs, content) in enumerate(cells):
                label = headers[i] if i < len(headers) else ""
                extra = ' data-label="%s"' % html.escape(label, quote=True) if cards and label else ""
                out.append("<td%s%s>%s</td>" % (attrs, extra, content))
            tr_attrs = ""
            if 0 <= date_col < len(cells):
                dm = DATE_RE.search(text_of(cells[date_col][1]))
                if dm:
                    mth, day = int(dm.group(1)), int(dm.group(2))
                    tr_attrs = ' data-date="%04d-%02d-%02d"' % (year_for(term, mth), mth, day)
            return "<tr%s>%s</tr>" % (tr_attrs, "".join(out))

        new_body = TR_RE.sub(one_row, tbody)
        caption = caps[counter[0]] if counter[0] < len(caps) else "표"
        counter[0] += 1
        return '<table%s>\n<caption>%s</caption>\n<thead>%s</thead>\n<tbody>%s</tbody>\n</table>' % (
            ' class="cards"' if cards else "", html.escape(caption), new_head, new_body)

    return TABLE_RE.sub(one_table, body)


def render(title, body):
    return (PAGE.replace("__CSS__", CSS)
                .replace("__TITLE__", html.escape(title))
                .replace("__BODY__", body)
                .replace("__BUILT__", date.today().isoformat()))


def build_term(term):
    src = SRC / ("%s.md" % term)
    if not src.exists():
        sys.exit("소스가 없습니다: %s" % src)

    md = markdown.Markdown(extensions=["tables", "toc", "attr_list", "md_in_html", "nl2br"],
                           extension_configs={"toc": {"toc_depth": "2-3"}})
    body = md.convert(src.read_text(encoding="utf-8"))
    body = rewrite_tables(body, term)

    title_m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    title = text_of(title_m.group(1)) if title_m else term
    page_title = "%s %s학기 강의계획서" % (title, term.replace("-", "학년도 "))

    toc = ('<details id="toc"><summary>목차</summary>%s</details>'
           '<script>if(matchMedia("(min-width:701px)").matches)'
           'document.getElementById("toc").open=true;</script>' % md.toc)
    # 목차는 제목 블록 바로 뒤(첫 <hr> 앞)에 끼운다.
    parts = body.split("<hr />", 1)
    body = (parts[0] + toc + "<hr />" + parts[1]) if len(parts) == 2 else (toc + body)

    out_dir = ROOT / term
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(render(page_title, body).replace("__JS__", JS),
                                        encoding="utf-8")
    print("빌드 완료: %s" % (out_dir / "index.html"))


def build_index():
    """src/ 안의 학기들을 최신순으로 나열한 루트 index.html."""
    terms = sorted((p.stem for p in SRC.glob("*.md")), reverse=True)
    items = []
    for t in terms:
        first = ""
        for line in (SRC / ("%s.md" % t)).read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                first = line[2:].strip()
                break
        items.append('<li><a href="%s/">%s학기 &mdash; %s</a></li>'
                     % (t, html.escape(t.replace("-", "학년도 ")), html.escape(first)))
    body = "<h1>강의계획서</h1>\n<ul>\n%s\n</ul>" % "\n".join(items)
    (ROOT / "index.html").write_text(render("강의계획서", body).replace("__JS__", ""),
                                     encoding="utf-8")
    print("빌드 완료: %s" % (ROOT / "index.html"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("사용법: python build.py 2026-2")
    build_term(sys.argv[1])
    build_index()
