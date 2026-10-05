# Bible Commentator QA Report (NT)

Date: 2026-10-05. Server: http://127.0.0.1:8124

## Scope
- 27 NT books, 260 chapters on disk (364 .txt files total under bible/nt incl. citation files).
- Systematic 2-chapter random sample per book (seed 7): 50 chapters.
- All 7,559 citations in those chapters checked; 7,137 unique src URLs resolved.

## API checks (all PASS)
- /api/books/nt: 27 books, chapter counts correct vs files.
- /api/chapter/nt/<Book>/<n>: verse-per-line OK; Matthew 1 = 25 verses; John 1 = 51 verses verified earlier probing.
- /api/citations/nt/<Book>/<n>: dict of groups (ot, luther, rcdoctors, calvin, fathers); 30 items with no src (verse-only entries) - acceptable.
- /api/passage/text/<file>/L<n>: all Calvin-commentary/institutes sources resolve with JSON {vol,line,ref,snippet,raw}.
- /api/passage/fathers/<vol>/L<n>: all anf/npnf sources resolve.
- HTML routes /rawtext/..., /passage/..., /viewer all return 200 with content.

## Results
- Endpoints: 0 failures across 50 chapters + 7,137 src-resolve calls (0/7,137 failures).
- No missing books/chapters; no malformed JSON; citation srcs all reachable.

## Notes
- Early apparent failures were test-harness bugs (double "fathers-text/" prefix in constructed URL, and using HTML routes /fathers/... with a JSON parser). Verified server, not data, was at fault by direct curl.
- ot citations use src like /ot/Isaiah/40 (viewer route), not exercised via passage API by design.
