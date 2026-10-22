# Builds answers.html ("Has it been a Wordle answer?") from history.txt + log.txt and the template
# _answers.tpl.html. Run by the daily GitHub Action after it adds yesterday's answer.
# Files starting with "_" are not published by GitHub Pages.
import html, json, os, re, sys
from datetime import date, datetime, timedelta, timezone

START = date(2021, 6, 19)          # Wordle #0
REPEATS_FROM = 1689                # Feb 2, 2026: first reused answer

def read_pairs(path):
    got = {}
    if os.path.exists(path):
        for line in open(path):
            p = line.split()
            if len(p) == 2 and p[0].isdigit() and re.fullmatch('[a-z]{5}', p[1]): got[int(p[0])] = p[1]
    return got

def day(n): return START + timedelta(days=n)
def fmt(n): d = day(n); return f"{d:%b} {d.day}, {d.year}"

def build(now=None, out='answers.html'):
    if not os.path.exists('history.txt'):
        print('history.txt not found yet: skipping the past-answers page'); return False
    now = now or datetime.now(timezone.utc)
    cutoff = ((now - timedelta(hours=12)).date() - START).days          # first puzzle that may still be in play
    hist = read_pairs('history.txt'); hist.update(read_pairs('log.txt'))
    hist = {n: w for n, w in hist.items() if n < cutoff}               # never show a puzzle still in play
    if not hist: print('no answers yet'); return False
    latest = max(hist)
    uses = {}
    for n in sorted(hist): uses.setdefault(hist[n], []).append(n)
    since = [n for n in hist if n >= REPEATS_FROM]
    reps = sum(1 for n in since if uses[hist[n]][0] < n)
    one_in = round(len(since) / reps) if reps else 0
    # answer list for "could it still be picked?" (taken from the main page's own data)
    ans = []
    try:
        m = re.search(r'const DATA = (\{.*?\});\n', open('index.html', encoding='utf-8').read(), re.S)
        ans = json.loads(m.group(1))['ans'] if m else []
    except Exception as e:
        print('could not read the answer list from index.html:', e)
    # A-Z list
    parts, letters = [], []
    for L in 'abcdefghijklmnopqrstuvwxyz':
        ws = sorted(w for w in uses if w[0] == L)
        if not ws: continue
        letters.append(f'<a href="#L-{L.upper()}">{L.upper()}</a>')
        items = []
        for w in ws:
            ns = uses[w]
            when = ' and '.join(f'#{n} ({fmt(n)})' for n in ns)
            tag = ' <span class="pill py">repeat</span>' if len(ns) > 1 else ''
            items.append(f'<li><b>{w.upper()}</b>{tag}<span>{when}</span></li>')
        parts.append(f'<h3 id="L-{L.upper()}">{L.upper()}</h3>\n<ul class="words">\n' + '\n'.join(items) + '\n</ul>')
    data = {'u': uses, 'a': ans, 'latest': latest, 'start': START.isoformat()}
    rep = {
        '__COUNT__': f'{len(hist):,}', '__WORDS__': f'{len(uses):,}', '__LATEST__': f'{latest:,}',
        '__LATESTDATE__': fmt(latest), '__REPN__': str(reps), '__REPTOTAL__': str(len(since)),
        '__ONEIN__': str(one_in), '__LETTERS__': ' '.join(letters), '__LIST__': '\n'.join(parts),
        '__DATA__': json.dumps(data, separators=(',', ':')),
    }
    t = open('_answers.tpl.html', encoding='utf-8').read()
    for k, v in rep.items(): t = t.replace(k, v)
    left = re.findall(r'__[A-Z]+__', t)
    if left: print('unfilled placeholders:', left); return False
    open(out, 'w', encoding='utf-8').write(t)
    print(f'answers.html: {len(hist)} puzzles through #{latest}, {len(uses)} words, {reps} repeats of {len(since)} since #{REPEATS_FROM}')
    return True

if __name__ == '__main__':
    sys.exit(0 if build() is not None else 1)
