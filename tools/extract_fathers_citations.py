#!/usr/bin/env python3
"""Extract scripture citations from CCEL Church Fathers texts."""

import os, re, sqlite3
from collections import defaultdict

BASE = "/Users/martinschoffstall/.hermes/fathers"
TEXT_DIR = os.path.join(BASE, "texts")
SECTION_DIR = os.path.join(BASE, "sections")
DB_PATH = os.path.join(BASE, "citations.db")

# Priority volumes to process (use existing sections files)
VOLUMES_TO_PROCESS = ['anf01', 'anf03', 'anf04', 'anf02', 'anf05', 'anf06', 'anf07', 'anf08', 'anf09']

BOOK_MAP = {
    # full names (ANF/NPNF cite both ways: 'John i.' and 'Joh. i.')
    'Genesis': 'Genesis', 'Exodus': 'Exodus', 'Leviticus': 'Leviticus', 'Numbers': 'Numbers',
    'Deuteronomy': 'Deuteronomy', 'Joshua': 'Joshua', 'Judges': 'Judges', 'Ruth': 'Ruth',
    'Samuel': '2 Samuel', 'Kings': '2 Kings', 'Chronicles': '2 Chronicles',
    'Ezra': 'Ezra', 'Nehemiah': 'Nehemiah', 'Esther': 'Esther', 'Job': 'Job',
    'Psalms': 'Psalms', 'Psalm': 'Psalms', 'Proverbs': 'Proverbs', 'Proverb': 'Proverbs',
    'Ecclesiastes': 'Ecclesiastes', 'Song': 'Song of Solomon', 'Isaiah': 'Isaiah',
    'Jeremiah': 'Jeremiah', 'Lamentations': 'Lamentations', 'Ezekiel': 'Ezekiel',
    'Daniel': 'Daniel', 'Hosea': 'Hosea', 'Joel': 'Joel', 'Amos': 'Amos',
    'Obadiah': 'Obadiah', 'Jonah': 'Jonah', 'Micah': 'Micah', 'Nahum': 'Nahum',
    'Habakkuk': 'Habakkuk', 'Zephaniah': 'Zephaniah', 'Haggai': 'Haggai',
    'Zechariah': 'Zechariah', 'Malachi': 'Malachi',
    'Matthew': 'Matthew', 'Mark': 'Mark', 'Luke': 'Luke', 'John': 'John',
    'Acts': 'Acts', 'Romans': 'Romans', 'Corinthians': '2 Corinthians',
    'Galatians': 'Galatians', 'Ephesians': 'Ephesians', 'Philippians': 'Philippians',
    'Colossians': 'Colossians', 'Thessalonians': '2 Thessalonians', 'Timothy': '2 Timothy',
    'Titus': 'Titus', 'Philemon': 'Philemon', 'Hebrews': 'Hebrews', 'James': 'James',
    'Peter': '2 Peter', 'Jude': 'Jude', 'Revelation': 'Revelation',
    # abbreviations
    'Gen': 'Genesis', 'Gen.': 'Genesis',
    'Ex': 'Exodus', 'Exo': 'Exodus', 'Ex.': 'Exodus', 'Exod': 'Exodus', 'Exod.': 'Exodus',
    'Lev': 'Leviticus', 'Lev.': 'Leviticus',
    'Num': 'Numbers', 'Num.': 'Numbers',
    'Deut': 'Deuteronomy', 'Deu': 'Deuteronomy', 'Deut.': 'Deuteronomy',
    'Josh': 'Joshua', 'Jos': 'Joshua', 'Josh.': 'Joshua',
    'Judg': 'Judges', 'Jdg': 'Judges', 'Judg.': 'Judges',
    'Ruth': 'Ruth',
    '1Sa': '1 Samuel', '1Sam': '1 Samuel', '1Sa.': '1 Samuel', '1 Sam': '1 Samuel',
    '2Sa': '2 Samuel', '2Sam': '2 Samuel', '2Sa.': '2 Samuel', '2 Sam': '2 Samuel',
    '1Ki': '1 Kings', '1Kgs': '1 Kings', '1Ki.': '1 Kings', '1 Kgs': '1 Kings',
    '2Ki': '2 Kings', '2Kgs': '2 Kings', '2Ki.': '2 Kings', '2 Kgs': '2 Kings',
    '1Ch': '1 Chronicles', '1Chr': '1 Chronicles', '1Ch.': '1 Chronicles',
    '2Ch': '2 Chronicles', '2Chr': '2 Chronicles', '2Ch.': '2 Chronicles',
    'Ezra': 'Ezra', 'Ezr': 'Ezra', 'Ezra.': 'Ezra', 'Ezr.': 'Ezra',
    'Neh': 'Nehemiah', 'Neh.': 'Nehemiah',
    'Esth': 'Esther', 'Esth.': 'Esther', 'Esther': 'Esther',
    'Job': 'Job', 'Job.': 'Job',
    'Psa': 'Psalms', 'Ps': 'Psalms', 'Psa.': 'Psalms', 'Ps.': 'Psalms',
    'Prov': 'Proverbs', 'Pro': 'Proverbs', 'Prov.': 'Proverbs',
    'Eccl': 'Ecclesiastes', 'Ecc': 'Ecclesiastes', 'Eccl.': 'Ecclesiastes', 'Ecc.': 'Ecclesiastes',
    'Song': 'Song of Solomon', 'Song.': 'Song of Solomon',
    'Cant': 'Song of Solomon', 'Cant.': 'Song of Solomon',
    'Isa': 'Isaiah', 'Isa.': 'Isaiah', 'Isai': 'Isaiah', 'Isai.': 'Isaiah',
    'Jer': 'Jeremiah', 'Jer.': 'Jeremiah', 'Jerem': 'Jeremiah',
    'Lam': 'Lamentations', 'Lam.': 'Lamentations',
    'Ezek': 'Ezekiel', 'Eze': 'Ezekiel', 'Ezek.': 'Ezekiel', 'Ezk': 'Ezekiel',
    'Dan': 'Daniel', 'Dan.': 'Daniel', 'Dn': 'Daniel',
    'Hos': 'Hosea', 'Hos.': 'Hosea',
    'Joe': 'Joel', 'Joe.': 'Joel', 'Jl': 'Joel',
    'Amo': 'Amos', 'Amo.': 'Amos', 'Am': 'Amos',
    'Oba': 'Obadiah', 'Oba.': 'Obadiah',
    'Jon': 'Jonah', 'Jon.': 'Jonah', 'Jnh': 'Jonah',
    'Mic': 'Micah', 'Mic.': 'Micah',
    'Nah': 'Nahum', 'Nah.': 'Nahum',
    'Hab': 'Habakkuk', 'Hab.': 'Habakkuk',
    'Zep': 'Zephaniah', 'Zep.': 'Zephaniah',
    'Hag': 'Haggai', 'Hag.': 'Haggai',
    'Zec': 'Zechariah', 'Zec.': 'Zechariah',
    'Mal': 'Malachi', 'Mal.': 'Malachi',
    'Mat': 'Matthew', 'Matt': 'Matthew', 'Mat.': 'Matthew', 'Matt.': 'Matthew', 'Mt': 'Matthew',
    'Mrk': 'Mark', 'Mark': 'Mark', 'Mrk.': 'Mark', 'Mr.': 'Mark', 'Mk': 'Mark',
    'Luk': 'Luke', 'Luk.': 'Luke', 'Lk': 'Luke', 'Lk.': 'Luke',
    'Joh': 'John', 'Joh.': 'John', 'Jn': 'John', 'Jn.': 'John',
    'Acts': 'Acts', 'Acts.': 'Acts', 'Ac': 'Acts',
    'Rom': 'Romans', 'Rom.': 'Romans',
    '1Co': '1 Corinthians', '1Cor': '1 Corinthians', '1Co.': '1 Corinthians', '1Cor.': '1 Corinthians', '1Cor': '1 Corinthians',
    '2Co': '2 Corinthians', '2Cor': '2 Corinthians', '2Co.': '2 Corinthians', '2Cor.': '2 Corinthians',
    'Gal': 'Galatians', 'Gal.': 'Galatians',
    'Eph': 'Ephesians', 'Eph.': 'Ephesians',
    'Php': 'Philippians', 'Phil': 'Philippians', 'Php.': 'Philippians', 'Phil.': 'Philippians',
    'Col': 'Colossians', 'Col.': 'Colossians',
    '1Th': '1 Thessalonians', '1Thes': '1 Thessalonians', '1Th.': '1 Thessalonians',
    '2Th': '2 Thessalonians', '2Thes': '2 Thessalonians', '2Th.': '2 Thessalonians',
    '1Ti': '1 Timothy', '1Tim': '1 Timothy', '1Ti.': '1 Timothy',
    '2Ti': '2 Timothy', '2Tim': '2 Timothy', '2Ti.': '2 Timothy',
    'Tit': 'Titus', 'Tit.': 'Titus',
    'Phm': 'Philemon', 'Philem': 'Philemon', 'Phm.': 'Philemon',
    'Heb': 'Hebrews', 'Heb.': 'Hebrews',
    'Jas': 'James', 'Jas.': 'James',
    '1Pe': '1 Peter', '1Pet': '1 Peter', '1Pe.': '1 Peter',
    '2Pe': '2 Peter', '2Pet': '2 Peter', '2Pe.': '2 Peter',
    '1Jo': '1 John', '1Jn': '1 John', '1Jo.': '1 John', '1Jn.': '1 John',
    '2Jo': '2 John', '2Jn': '2 John', '2Jo.': '2 John', '2Jn.': '2 John',
    '3Jo': '3 John', '3Jn': '3 John', '3Jo.': '3 John', '3Jn.': '3 John',
    'Jud': 'Jude', 'Jude': 'Jude', 'Jud.': 'Jude',
    'Rev': 'Revelation', 'Rev.': 'Revelation', 'Revel': 'Revelation',
    'Apoc': 'Revelation', 'Apoc.': 'Revelation',
}

OT_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth',
            '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
            'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes', 'Song of Solomon',
            'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
            'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi']

NT_BOOKS = ['Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians',
            'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
            '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter',
            '1 John', '2 John', '3 John', 'Jude', 'Revelation']

VOLUMES = [
    'anf01', 'anf02', 'anf03', 'anf04', 'anf05', 'anf06', 'anf07', 'anf08', 'anf09', 'anf10',
    'npnf101', 'npnf102', 'npnf103', 'npnf104', 'npnf105', 'npnf106', 'npnf107', 'npnf108',
    'npnf109', 'npnf110', 'npnf111', 'npnf112', 'npnf113', 'npnf114',
    'npnf201', 'npnf202', 'npnf203', 'npnf204', 'npnf205', 'npnf206', 'npnf207', 'npnf208',
    'npnf209', 'npnf210', 'npnf211', 'npnf212', 'npnf213', 'npnf214',
]

def resolve_ref(abbr):
    if abbr in BOOK_MAP:
        return BOOK_MAP[abbr]
    for k, v in BOOK_MAP.items():
        if k.rstrip('.') == abbr or abbr.rstrip('.') == k:
            return v
    return abbr

def roman_to_int(s):
    s = s.lower().rstrip('.')
    if not s:
        return 0
    roman_vals = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
    result = 0
    prev = 0
    for ch in reversed(s):
        val = roman_vals.get(ch, 0)
        if val < prev:
            result -= val
        else:
            result += val
        prev = val
    return result if result > 0 else 0

def load_sections_from_file(vol):
    """Load section map from existing .sections file with various formats."""
    sections = []
    section_file = os.path.join(SECTION_DIR, f"{vol}.sections")
    if not os.path.exists(section_file):
        return sections
    with open(section_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse: <line_num> <father> <work_key> <work_title>
            # Format 1: "115 Tertullian: Introduction" -> father=Tertullian, work=introduction
            # Format 2: "1201 The Apology (Tertullian)" -> father=Tertullian, work=apology
            # Format 3: "21 The Apostolic Fathers / Justin Martyr / Irenaeus (composite)" -> composite
            # Format 4: "58:  Introductory Note" -> generic
            
            # Extract leading line number
            m = re.match(r'^(\d+)\s*(?::)?\s*(.*)', line)
            if not m:
                continue
            
            line_num = int(m.group(1))
            rest = m.group(2).strip()
            
            father = "Unknown"
            work_key = "unknown"
            work_title = rest
            
            # Try to extract father from "(Father)" or "Father:" pattern
            if ' (Tertullian)' in rest or 'Tertullian: ' in rest:
                father = 'Tertullian'
                rest = rest.replace(' (Tertullian)', '').replace('Tertullian: ', '')
            if ' (Athenagoras)' in rest or 'Athenagoras: ' in rest:
                father = 'Athenagoras'
                rest = rest.replace(' (Athenagoras)', '').replace('Athenagoras: ', '')
            if ' (Minucius Felix)' in rest or 'Minucius Felix: ' in rest:
                father = 'Minucius Felix'
                rest = rest.replace(' (Minucius Felix)', '').replace('Minucius Felix: ', '')
            if ' (Hermas)' in rest or 'Hermas: ' in rest:
                father = 'Hermas'
                rest = rest.replace(' (Hermas)', '').replace('Hermas: ', '')
            if ' (Theophilus)' in rest or 'Theophilus: ' in rest:
                father = 'Theophilus'
                rest = rest.replace(' (Theophilus)', '').replace('Theophilus: ', '')
            if ' (Clement)' in rest or 'Clement: ' in rest:
                father = 'Clement of Rome'
                rest = rest.replace(' (Clement)', '').replace('Clement: ', '')
            if ' (Hippolytus)' in rest or 'Hippolytus: ' in rest:
                father = 'Hippolytus'
                rest = rest.replace(' (Hippolytus)', '').replace('Hippolytus: ', '')
            if ' (Cyprian)' in rest or 'Cyprian: ' in rest:
                father = 'Cyprian'
                rest = rest.replace(' (Cyprian)', '').replace('Cyprian: ', '')
            if ' (Gregory Thaumaturgus)' in rest or 'Gregory Thaumaturgus: ' in rest:
                father = 'Gregory Thaumaturgus'
                rest = rest.replace(' (Gregory Thaumaturgus)', '').replace('Gregory Thaumaturgus: ', '')
            if ' (Melito)' in rest or 'Melito: ' in rest:
                father = 'Melito'
                rest = rest.replace(' (Melito)', '').replace('Melito: ', '')
            if ' (Justin Martyr)' in rest or 'Justin Martyr: ' in rest:
                father = 'Justin Martyr'
                rest = rest.replace(' (Justin Martyr)', '').replace('Justin Martyr: ', '')
            if ' (Irenaeus)' in rest or 'Irenaeus: ' in rest:
                father = 'Irenaeus'
                rest = rest.replace(' (Irenaeus)', '').replace('Irenaeus: ', '')
            if ' (Tatian)' in rest or 'Tatian: ' in rest:
                father = 'Tatian'
                rest = rest.replace(' (Tatian)', '').replace('Tatian: ', '')
            if ' (Commodianus)' in rest or 'Commodianus: ' in rest:
                father = 'Commodianus'
                rest = rest.replace(' (Composianus)', '').replace('Commodianus: ', '')
            if ' (Origen)' in rest or 'Origen: ' in rest:
                father = 'Origen'
                rest = rest.replace(' (Origen)', '').replace('Origen: ', '')
            if ' (Meliton)' in rest or 'Meliton: ' in rest:
                father = 'Meliton'
                rest = rest.replace(' (Meliton)', '').replace('Meliton: ', '')
            if ' (Anonymous)' in rest or 'Anonymous: ' in rest:
                father = 'Anonymous'
                rest = rest.replace(' (Anonymous)', '').replace('Anonymous: ', '')
            
            # For composite entries like "The Apostolic Fathers / Justin Martyr / Irenaeus (composite)"
            if 'composite' in rest.lower():
                fathers = re.findall(r'[A-Z][a-zA-Z\s-]+(?=\s*/\s*| \(composite\))', rest)
                if fathers:
                    father = fathers[0].strip()
                    work_key = 'composite'
                rest = rest.split('/')[0].strip()
            
            # For format "58:  Introductory Note" - skip generic markers
            if re.match(r'^Introductory|^Table of|^CCEL|^Index', rest, re.IGNORECASE):
                continue
            if rest.lower() in ('introductory note', 'table of contents', 'index'):
                continue
            
            # Clean up work title
            work_title = re.sub(r'\s*\([^)]*\)', '', rest).strip()
            if not work_title:
                work_title = rest
            
            # Generate work_key from title
            if work_key == "unknown":
                work_key = re.sub(r'[^a-z0-9]', '_', work_title.lower())
                work_key = re.sub(r'_+', '_', work_key).strip('_')
            
            if work_title:
                sections.append((line_num, father, work_key, work_title))
    
    return sections

def main():
    print("Phase 1: Loading existing sections...")
    
    # Ensure DB has correct schema
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if citations table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='citations'")
    if not c.fetchone():
        c.execute("CREATE TABLE citations (id INTEGER PRIMARY KEY AUTOINCREMENT, father TEXT, work TEXT, volume TEXT, scripture_ref TEXT, citation_text TEXT, source_line INTEGER)")
        conn.commit()
        print("  Created citations table")
    
    # Also create sections table if missing
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sections'")
    if not c.fetchone():
        c.execute("CREATE TABLE sections (vol TEXT, line_num INTEGER, father TEXT, work_key TEXT, work_title TEXT)")
        conn.commit()
        print("  Created sections table")
    
    print("\nPhase 2: Extracting citations...")
    
    total_citations = 0
    resolved_citations = 0
    skipped = 0
    vol_stats = {}
    
    # Build pattern for all abbreviations (longest first for regex).
    # ANF/NPNF refs use roman chapter + arabic OR roman verse: "Tit. iii. 1", "Isa. liii. 5", "Ps. cx. 1".
    abbr_list = sorted(BOOK_MAP.keys(), key=len, reverse=True)
    # chapter roman, verse arabic or roman
    abbr_pattern = r'\b(' + '|'.join(re.escape(a) for a in abbr_list) + r')\.?\s+([ivxlcdm]+)\s*\.?\s*(\d+|[ivxlcdm]+)'
    
    for vol in VOLUMES_TO_PROCESS:
        fpath = os.path.join(TEXT_DIR, vol + '.txt')
        if not os.path.exists(fpath):
            print(f"  SKIP {vol}: file missing")
            continue
        
        sections = load_sections_from_file(vol)
        if not sections:
            print(f"  SKIP {vol}: no sections found")
            continue
        
        print(f"  Processing {vol} ({len(sections)} sections)...")
        
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        vol_citations = 0
        vol_resolved = 0
        vol_skipped = 0
        
        # Build section lookup: sorted by line_num
        section_lookup = sorted(sections, key=lambda x: x[0])
        
        # Use a set to dedup by (father, work, verse_ref, source_line)
        seen = set()
        
        # Track current section context
        cur_father = "Unknown"
        cur_work_key = "Unknown"
        cur_work_title = "Unknown"
        cur_section_idx = 0
        
        for i, line in enumerate(lines):
            line_num = i + 1
            line_stripped = line.strip()
            
            # Advance to next section if line_num matches
            while cur_section_idx < len(section_lookup) and section_lookup[cur_section_idx][0] <= line_num:
                cur_father = section_lookup[cur_section_idx][1]
                cur_work_key = section_lookup[cur_section_idx][2]
                cur_work_title = section_lookup[cur_section_idx][3]
                cur_section_idx += 1
            
            # Skip separator lines
            if line_stripped.startswith('     __'):
                continue
            
            # Skip index/meta lines
            if 'INDEX OF' in line_stripped:
                continue
            
            # Find all scripture references
            ref_matches = list(re.finditer(abbr_pattern, line, re.IGNORECASE))
            
            if ref_matches:
                for m in ref_matches:
                    match_text = m.group(0)
                    book_abbr = m.group(1)  # capture group 1 is the abbreviation itself
                    book = resolve_ref(book_abbr)
                    chapter_int = roman_to_int(m.group(2))
                    verse_raw = m.group(3)
                    verse_int = int(verse_raw) if verse_raw.isdigit() else roman_to_int(verse_raw)
                    
                    if chapter_int == 0 and verse_int == 0:
                        vol_skipped += 1
                        continue
                    
                    verse_ref = f"{book} {chapter_int}:{verse_int}"
                    dedup_key = (cur_father, cur_work_key, verse_ref, line_num)
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)
                    
                    citation_text = line_stripped[:200].replace('\n', ' ')
                    
                    c.execute(
                        "INSERT INTO citations (father, work, volume, scripture_ref, citation_text, source_line) VALUES (?, ?, ?, ?, ?, ?)",
                        (cur_father, cur_work_key, vol, verse_ref, citation_text, line_num)
                    )
                    vol_citations += 1
                    vol_resolved += 1
            
            # Also check for inline prose citations: "it is written" etc.
            prose_pats = [
                re.compile(r'(?:\bthe\s+scripture\s+saith\b|\bscripture\s+saith\b|\bit\s+is\s+written\b|"it is written"\b|\bsaith\s+the\s+lord\b|\bthe\s+lord\s+saith\b|\bprophet\s+saith\b|\bisaias\s+saieth\b)', re.IGNORECASE),
            ]
            for pp in prose_pats:
                if pp.search(line_stripped):
                    # Try to find a book reference on this line
                    book_match = re.search(r'(?:' + '|'.join(re.escape(a) for a in abbr_list) + r')\.\s*([ivxlcdm]+)\s*\.?\s*([ivxlcdm]+)', line_stripped, re.IGNORECASE)
                    if book_match:
                        book = resolve_ref(book_match.group(0).split('.')[0])
                        chapter_int = roman_to_int(book_match.group(1))
                        verse_int = roman_to_int(book_match.group(2))
                        if chapter_int > 0 and verse_int > 0:
                            verse_ref = f"{book} {chapter_int}:{verse_int}"
                            dedup_key = (cur_father, cur_work_key, verse_ref, line_num)
                            if dedup_key not in seen:
                                seen.add(dedup_key)
                                citation_text = line_stripped[:200].replace('\n', ' ')
                                c.execute(
                                    "INSERT INTO citations (father, work, volume, scripture_ref, citation_text, source_line) VALUES (?, ?, ?, ?, ?, ?)",
                                    (cur_father, cur_work_key, vol, verse_ref, citation_text, line_num)
                                )
                                vol_citations += 1
                                vol_resolved += 1
        
        vol_stats[vol] = (vol_citations, vol_resolved, vol_skipped)
        total_citations += vol_citations
        resolved_citations += vol_resolved
        skipped += vol_skipped
        print(f"    {vol}: {vol_citations} citations (resolved: {vol_resolved}, skipped: {vol_skipped})")
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM citations")
    total_db = c.fetchone()[0]
    
    print(f"\nTotal citations in DB: {total_db}")
    print(f"Volumes processed: {len(vol_stats)}")
    
    # Phase 4: Write per-book output files
    print("\nPhase 4: Writing per-book output files...")
    otc_dir = os.path.join(BASE, "..", "otcitations")
    ot_dir = os.path.join(otc_dir, "ot")
    nt_dir = os.path.join(otc_dir, "nt")
    os.makedirs(ot_dir, exist_ok=True)
    os.makedirs(nt_dir, exist_ok=True)
    
    files_written_ot = 0
    files_written_nt = 0
    
    all_books = OT_BOOKS + NT_BOOKS
    for book in all_books:
        book_dir = os.path.join(otc_dir, "ot" if book in OT_BOOKS else "nt", book)
        os.makedirs(book_dir, exist_ok=True)
        out_file = os.path.join(book_dir, "fathers.citation")
        
        c.execute("SELECT father, work, volume, scripture_ref, citation_text, source_line FROM citations WHERE scripture_ref LIKE ?",
                 (book + " %",))
        rows = c.fetchall()
        
        if rows:
            with open(out_file, 'w') as f:
                for row in rows:
                    father, work, vol, ref, cite_text, src_line = row
                    f.write(f"{ref} | {father}, {work} ({vol}): {cite_text[:150]}\n")
            
            if book in OT_BOOKS:
                files_written_ot += 1
            else:
                files_written_nt += 1
            print(f"  {'OT' if book in OT_BOOKS else 'NT'} {book}: {len(rows)} citations")
        else:
            print(f"  {'OT' if book in OT_BOOKS else 'NT'} {book}: 0 citations")
    
    conn.close()
    print(f"\nDone! OT files: {files_written_ot}, NT files: {files_written_nt}")

if __name__ == '__main__':
    main()
