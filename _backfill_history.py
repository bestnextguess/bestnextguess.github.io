# One-time download of every past Wordle answer into history.txt ("puzzle-number word" per line),
# from the same NYT puzzle feed the daily update uses. Slow on purpose (about one request a second).
# Safe to run again: it skips puzzles already in history.txt and only fills the gaps.
# It never fetches a puzzle that could still be in play anywhere in the world.
import json, os, re, sys, time, urllib.request
from datetime import date, datetime, timedelta, timezone

START = date(2021, 6, 19)                      # Wordle #0
OUT = 'history.txt'
UA = 'Mozilla/5.0 (compatible; bestnextguess-history/1.0; +https://bestnextguess.com)'

def load(path):
    got = {}
    if os.path.exists(path):
        for line in open(path):
            p = line.split()
            if len(p) == 2 and p[0].isdigit() and re.fullmatch('[a-z]{5}', p[1]): got[int(p[0])] = p[1]
    return got

def save(got):
    tmp = OUT + '.tmp'
    with open(tmp, 'w') as f:
        for n in sorted(got): f.write(f'{n} {got[n]}\n')
    os.replace(tmp, OUT)

def fetch(day, opener=urllib.request.urlopen):
    url = f'https://www.nytimes.com/svc/wordle/v2/{day.isoformat()}.json'
    for attempt in range(3):
        try:
            with opener(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=20) as r:
                w = str(json.load(r).get('solution', '')).lower()
            return w if re.fullmatch('[a-z]{5}', w) else None
        except Exception as e:
            print(f'  {day}: attempt {attempt + 1} failed ({e})', flush=True)
            time.sleep(5 * (attempt + 1))
    return None

def main(opener=urllib.request.urlopen, pause=0.8, now=None):
    now = now or datetime.now(timezone.utc)
    last = (now - timedelta(hours=12)).date() - timedelta(days=1)   # yesterday everywhere on Earth
    got = load(OUT)
    for n, w in load('log.txt').items(): got.setdefault(n, w)      # the daily log already has the latest days
    missing = []
    day, new = START, 0
    while day <= last:
        n = (day - START).days
        if n not in got:
            w = fetch(day, opener)
            if w: got[n] = w; new += 1
            else: missing.append(n)
            if new and new % 100 == 0: save(got); print(f'{new} answers saved so far (up to #{n})', flush=True)
            time.sleep(pause)
        day += timedelta(days=1)
    save(got)
    print(f'Done: {len(got)} puzzles in {OUT} ({new} new). Missing: {missing if missing else "none"}')
    return got, missing

if __name__ == '__main__':
    main()
