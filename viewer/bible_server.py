#!/usr/bin/env python3
"""Bible chapter server — browse BSB text + citation layers as web pages.

/                     -> index of books (OT/NT)
/ot/<Book>/           -> chapter list + citation files
/nt/<Book>/
/ot/<Book>/<n>        -> chapter N rendered, with citations inline
/nt/<Book>/<n>
"""
import html
import os
import re
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = "/Users/martinschoffstall/.hermes/biblecommentator/bible"
PORT = 8124

STYLE = """<style>
body{margin:0;background:#faf9f6;color:#2b2620;font:16px/1.7 Georgia,'Times New Roman',serif;padding:24px;max-width:760px}
h1{font-size:26px;margin:0 0 4px} h2{font-size:20px;margin:28px 0 8px;color:#5a4632}
.crumbs{font:12px/1.4 -apple-system,sans-serif;color:#8a7a66;margin-bottom:18px}
.crumbs a{color:#8a6d3b;text-decoration:none} .crumbs a:hover{text-decoration:underline}
.verse{margin:0 0 14px;text-indent:1.5em}
.cite{background:#f3ead9;border-left:3px solid #b08d4f;margin:14px 0;padding:10px 14px;font:13px/1.55 -apple-system,sans-serif;border-radius:4px}
.cite .src{color:#8a6d3b;font-weight:600}
.cite .who{color:#5a4632;font-weight:600}
.chapters{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 20px}
.chapters a{font:13px -apple-system,sans-serif;background:#efe6d3;color:#5a4632;padding:4px 9px;border-radius:5px;text-decoration:none}
.chapters a.cur{background:#b08d4f;color:#fff}
ul.books{columns:3;-webkit-columns:3;list-style:none;padding:0;margin:0}
ul.books li{margin:4px 0} ul.books a{color:#5a4632;text-decoration:none;font-size:15px}
.meta{font:11px -apple-system,sans-serif;color:#a2937d;margin:6px 0 0}
</style>"""


def load_citations(testament, book):
    out = {}
    base = os.path.join(ROOT, testament, book)
    if not os.path.isdir(base):
        return out
    for fname in os.listdir(base):
        if not fname.endswith(".citation"):
            continue
        kind = fname[:-len(".citation")]
        rows = []
        try:
            for line in open(os.path.join(base, fname), encoding="utf-8-sig"):
                line = line.strip()
                if not line:
                    continue
                # "<Book> <chapter>:<verse> -> <ot ref> | context"  or  "<Book> <c>:<v> | who: context"
                m = re.match(r"^(.*?)\s(\d+)(?::(\d+[-– ]*\d*))?\s*(?:->\s*(.+?)\s*\|)?\s*\|?\s*(.*)$", line)
                chap = int(m.group(2)) if m else None
                if chap is None:
                    chap, rest = 0, line
                else:
                    rest = (m.group(4) or "") + (" — " if m.group(4) and m.group(5) else "") + (m.group(5) or "")
                rows.append({"chap": chap, "text": line, "rest": rest})
        except Exception:
            continue
        out[kind] = rows
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, body):
        body = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0]).strip("/")
        parts = [p for p in path.split("/") if p]

        # /fathers/<vol>          -> volume TOC (works with links)
        # /fathers/<vol>/L<n>     -> the whole WORK containing line n, highlighted
        if len(parts) >= 1 and parts[0] == "fathers":
            import bisect
            vol = parts[1] if len(parts) > 1 else "anf01"
            anchor = None
            if len(parts) > 2 and parts[2].startswith("L"):
                try:
                    anchor = int(parts[2][1:])
                except ValueError:
                    pass
            f = os.path.join("/Users/martinschoffstall/.hermes/fathers/texts", vol + ".txt")
            if not os.path.exists(f):
                self._send(f"<h1>Volume not found</h1>{STYLE}"); return
            lines = open(f, encoding="utf-8", errors="replace").read().splitlines()

            # section map from DB (whole works, not snippets)
            con = sqlite3.connect("file:/Users/martinschoffstall/.hermes/fathers/citations.db?mode=ro", uri=True)
            secs = con.execute("SELECT line_num, father, work_key, work_title FROM sections WHERE vol=? ORDER BY line_num", (vol,)).fetchall()
            con.close()

            if anchor:
                starts = [s[0] for s in secs]
                i = bisect.bisect_right(starts, anchor) - 1
                if i < 0: i = 0
                lo, hi = secs[i][0], (secs[i+1][0] - 1 if i+1 < len(secs) else len(lines))
                cur_father, cur_title = secs[i][1], secs[i][3]
            else:
                lo, hi, cur_father, cur_title = 1, min(len(lines), 200), "", ""

            crumb = f" &middot; <a href='/fathers/{vol}'>{vol} contents</a>"
            rows = [f"<h1>{html.escape(cur_title or vol)}</h1>", STYLE,
                    f"<div class='crumbs'><a href='/fathers/{vol}'>Fathers</a>{crumb if anchor else ''}{f' &middot; by {html.escape(cur_father)}' if cur_father else ''} &middot; lines {lo+1}&ndash;{hi}</div>"]
            if not anchor:
                rows.append("<div class='chapters'>" + " ".join(
                    f"<a href='/fathers/{vol}/L{s[0]}'>{html.escape(s[3][:40])}</a>" for s in secs) + "</div>")
                rows.append(f"<div class='meta'>{len(lines)} lines total</div>")
            for i in range(lo, hi):
                n = i + 1
                hl = " style='background:#f3ead9;border-left:3px solid #b08d4f;padding-left:6px'" if n == anchor else ""
                rows.append(f"<p id='L{n}'{hl}><a href='#L{n}' style='color:#a2937d;font-size:11px;text-decoration:none'>{n}</a> {html.escape(lines[i])}</p>")
            if anchor and lo > 0:
                rows.append(f"<div class='meta'>&middot; <a href='/fathers/{vol}/L{lo}'>&uarr; start of work</a></div>")
            self._send("\n".join(rows))
            return

        # index
        if not parts:
            rows = ["<h1>Bible Commentator</h1>", STYLE,
                    "<div class='meta'>Berean Standard Bible + citation layers — NT's OT use, Church Fathers, N.T. Wright</div>"]
            for t, label in (("ot", "Old Testament"), ("nt", "New Testament")):
                base = os.path.join(ROOT, t)
                if not os.path.isdir(base):
                    continue
                books = sorted(b for b in os.listdir(base) if os.path.isdir(os.path.join(base, b)) and not b.startswith("."))
                rows.append(f"<h2>{label}</h2><ul class='books'>")
                for b in books:
                    ncites = len([f for f in os.listdir(os.path.join(base, b)) if f.endswith(".citation")])
                    tag = f" <span style='color:#b08d4f;font-size:12px'>({ncites})</span>" if ncites else ""
                    rows.append(f"<li><a href='/{t}/{urllib.parse.quote(b)}/'>{html.escape(b)}</a>{tag}</li>")
                rows.append("</ul>")
            self._send("\n".join(rows))
            return

        # book page
        if len(parts) == 2 and parts[0] in ("ot", "nt"):
            t, book = parts
            base = os.path.join(ROOT, t, book)
            if not os.path.isdir(base):
                self._send(f"<h1>Not found</h1>{STYLE}"); return
            chapters = sorted([int(f[len("chapter"):-len(".txt")]) for f in os.listdir(base)
                               if re.match(r"chapter\d+\.txt$", f)])
            cites = load_citations(t, book)
            rows = [f"<h1>{html.escape(book)}</h1>", STYLE,
                    f"<div class='crumbs'><a href='/'>Bible</a> / {html.escape(t)}</div>",
                    "<div class='chapters'>"]
            for c in chapters:
                rows.append(f"<a href='/{t}/{urllib.parse.quote(book)}/{c}'>{c}</a>")
            rows.append("</div>")
            total = sum(len(v) for v in cites.values())
            rows.append(f"<div class='meta'>{len(chapters)} chapters · {total} citations</div>")
            for kind in sorted(cites):
                rows.append(f"<h2>{kind} citations ({len(cites[kind])})</h2>")
                for r in cites[kind][:50]:
                    rows.append(f"<div class='cite'>{html.escape(r['text'])}</div>")
            self._send("\n".join(rows))
            return

        # chapter page
        if len(parts) == 3 and parts[0] in ("ot", "nt"):
            t, book, chap_s = parts
            try:
                chap = int(chap_s)
            except ValueError:
                self._send(f"<h1>Bad chapter</h1>{STYLE}"); return
            base = os.path.join(ROOT, t, book)
            f = os.path.join(base, f"chapter{chap}.txt")
            if not os.path.exists(f):
                self._send(f"<h1>Chapter not found</h1>{STYLE}"); return
            text = open(f, encoding="utf-8-sig").read()
            verses = []
            for para in text.split("\n\n"):
                para = para.strip()
                if not para:
                    continue
                m = re.match(r"^(\d+)\s*(.*)$", para, re.S)
                if m:
                    verses.append((int(m.group(1)), m.group(2).strip()))
                else:
                    verses.append((None, para))
            body = [f"<h1>{html.escape(book)} {chap}</h1>", STYLE,
                    f"<div class='crumbs'><a href='/'>Bible</a> / <a href='/{t}/{urllib.parse.quote(book)}/'>{html.escape(book)}</a> / {chap}</div>"]
            # citations for this chapter (BSB text is prose, not numbered verses)
            cites = load_citations(t, book)
            by_kind = {}
            for kind, rows_c in cites.items():
                for r in rows_c:
                    m = re.match(r"^(.*?)\s(\d+)(?::(\d+))?", r["text"])
                    # exact book match (avoid '1 John' matching as 'John')
                    if m and m.group(1).strip() == book and int(m.group(2)) == chap:
                        by_kind.setdefault(kind, []).append(r["text"])
            for v, txt in verses:
                body.append(f"<p class='verse'>{html.escape(txt)}</p>")
            for kind in sorted(by_kind, reverse=True):
                body.append(f"<h2>{kind} citations ({len(by_kind[kind])})</h2>")
                for ctext in by_kind[kind]:
                    # linkify "src: /..." tails into clickable links
                    parts_c = ctext.rsplit("| src: ", 1)
                    if len(parts_c) == 2:
                        label = html.escape(parts_c[0])
                        link = f" &middot; <a href='{html.escape(parts_c[1])}' style='color:#8a6d3b'>source</a>"
                    else:
                        label, link = html.escape(ctext), ""
                    body.append(f"<div class='cite'><span class='src'>[{kind}]</span> {label}{link}</div>")
            body.append(f"<div class='meta'>{sum(len(v) for v in by_kind.values())} citation(s) reference this chapter</div>")
            self._send("\n".join(body))
            return

        self._send(f"<h1>Not found</h1>{STYLE}")


if __name__ == "__main__":
    print(f"bible server on 0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()