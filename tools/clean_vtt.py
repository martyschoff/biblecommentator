import os, glob, re
def clean(vtt):
    with open(vtt, encoding='utf-8', errors='replace') as f:
        data = f.read()
    data = data.split('WEBVTT',1)
    data = data[1] if len(data)>1 else data[0]
    txts=[]
    for ln in data.splitlines():
        t = ln.strip()
        if not t: continue
        if '-->' in t: continue                    # cue timestamp
        if re.match(r'^(Kind|Language)', t): continue
        if '<' in t and re.search(r'\d{2}:\d{2}:\d{2}', t):
            continue                                # word-by-word markers
        t = re.sub(r'\s+',' ', t).strip()
        if not t: continue
        txts.append(t)
    res=[]
    for t in txts:
        if res and res[-1]==t: continue
        res.append(t)
    return '\n'.join(res)

outdir='/Users/martinschoffstall/.hermes/ntwright/clean'
os.makedirs(outdir, exist_ok=True)
n=0; tot=0
for vtt in sorted(glob.glob('/Users/martinschoffstall/.hermes/ntwright/transcripts/*.vtt')):
    vid = os.path.basename(vtt).replace('.en.vtt','')
    txt = clean(vtt)
    with open(f'{outdir}/{vid}.txt','w', encoding='utf-8') as f:
        f.write(txt+'\n')
    n+=1; tot+=len(txt.split())
print('cleaned', n, 'files,', tot, 'words')
