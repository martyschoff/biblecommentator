import os, re, json

BASE = '/Users/martinschoffstall/.hermes/ntwright'
titles = {}
for ln in open(f'{BASE}/videos.txt'):
    if ' | ' in ln:
        i, t = ln.split(' | ', 1)
        titles[i.strip()] = t.strip()

BOOKS = {
 'Genesis':'Genesis','Exodus':'Exodus','Leviticus':'Leviticus','Numbers':'Numbers',
 'Deuteronomy':'Deuteronomy','Joshua':'Joshua','Judges':'Judges','Ruth':'Ruth',
 '1 Samuel':'1 Samuel','2 Samuel':'2 Samuel','1 Kings':'1 Kings','2 Kings':'2 Kings',
 '1 Chronicles':'1 Chronicles','2 Chronicles':'2 Chronicles','Ezra':'Ezra','Nehemiah':'Nehemiah',
 'Esther':'Esther','Job':'Job','Psalms':'Psalms','Psalm':'Psalms','Proverbs':'Proverbs',
 'Ecclesiastes':'Ecclesiastes','Song of Songs':'Song of Songs','Isaiah':'Isaiah','Jeremiah':'Jeremiah',
 'Lamentations':'Lamentations','Ezekiel':'Ezekiel','Daniel':'Daniel','Hosea':'Hosea','Joel':'Joel',
 'Amos':'Amos','Obadiah':'Obadiah','Jonah':'Jonah','Micah':'Micah','Nahum':'Nahum','Habakkuk':'Habakkuk',
 'Zephaniah':'Zephaniah','Haggai':'Haggai','Zechariah':'Zechariah','Malachi':'Malachi',
 'Matthew':'Matthew','Mark':'Mark','Luke':'Luke','John':'John','Acts':'Acts','Romans':'Romans',
 '1 Corinthians':'1 Corinthians','2 Corinthians':'2 Corinthians','Galatians':'Galatians',
 'Ephesians':'Ephesians','Philippians':'Philippians','Colossians':'Colossians','1 Thessalonians':'1 Thessalonians',
 '2 Thessalonians':'2 Thessalonians','1 Timothy':'1 Timothy','2 Timothy':'2 Timothy','Titus':'Titus',
 'Philemon':'Philemon','Hebrews':'Hebrews','James':'James','1 Peter':'1 Peter','2 Peter':'2 Peter',
 '1 John':'1 John','2 John':'2 John','3 John':'3 John','Jude':'Jude','Revelation':'Revelation',
}
names = sorted(BOOKS, key=len, reverse=True)
pat = re.compile('(' + '|'.join(re.escape(n) for n in names) + r')\s+(\d{1,3})(?:\s*[:.]\s*(\d{1,3}(?:\s*[-–]\s*\d{1,3})?(?:,\s*\d{1,3})*))?')
NAMEPAT = '|'.join(n.replace(' ', r'\s+') for n in names)
tpat = re.compile(r'(' + NAMEPAT + r')\s+(\d{1,3})')

hits = []
allvids = sorted(v[:-4] for v in os.listdir(f'{BASE}/clean') if v.endswith('.txt'))
for vid in allvids:
    text = open(f'{BASE}/clean/{vid}.txt', encoding='utf-8').read()
    found = {}
    for m in pat.finditer(text):
        book = BOOKS[m.group(1)]
        ch = int(m.group(2))
        v = (m.group(3) or '').strip()
        key = (book, ch, v)
        if key not in found:
            s = max(0, m.start()-250); e = min(len(text), m.end()+250)
            found[key] = re.sub(r'\s+', ' ', text[s:e].strip())
    t = titles.get(vid, '')
    tm = tpat.search(t)
    tref = None
    if tm:
        tname = re.sub(r'\s+', ' ', tm.group(1))
        book = BOOKS.get(tname, tname)
        rest = t[tm.end(1):]
        mm = re.match(r'\s*\|?\s*([\d,]+)', rest)
        if mm:
            tok = mm.group(1)
            if ':' in rest[:mm.end()]:
                verse = re.sub(r'\s+', '', tok)
                ch = int(tok.split(':', 1)[0])
            else:
                ch = int(tok.split(',')[0])
                verse = ''
            tref = {'book': book, 'ch': ch, 'verse': verse, 'raw': book + ' ' + tok}
    if found or tref:
        hits.append({'id': vid, 'title': t,
                     'refs': [list(k) for k in found.keys()],
                     'ctx': {'|'.join(str(x) for x in k): c for k, c in found.items()},
                     'tref': tref})

with open(f'{BASE}/batches/hits.json', 'w') as f:
    json.dump(hits, f, indent=1)
nlines = sum(len(h['refs']) + (1 if h['tref'] else 0) for h in hits)
print('videos with refs:', len(hits), '/', len(allvids), ' potential citation lines:', nlines)
