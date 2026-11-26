"""RSS news candidate collector. No AI calls or automatic verification."""
import argparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
UTC = timezone.utc

def canonical(url):
    p = urllib.parse.urlsplit(url.strip())
    if p.scheme not in ('http', 'https') or not p.netloc:
        return None
    q = [(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')]
    return urllib.parse.urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/'),urllib.parse.urlencode(q),''))

def clean(text):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', text or ''))).strip()

def date(text):
    try:
        d = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(text.replace('Z','+00:00'))
        except (AttributeError, ValueError):
            return None
    return d.replace(tzinfo=UTC) if d.tzinfo is None else d.astimezone(UTC)

def parse(payload):
    root = ET.fromstring(payload)
    for node in root.iter():
        if node.tag.split('}')[-1] not in ('item','entry'):
            continue
        f = {}
        for child in node:
            name = child.tag.split('}')[-1]
            text = ''.join(child.itertext()).strip()
            if name == 'link':
                if child.get('rel','alternate') == 'alternate':
                    f['link'] = child.get('href') or text
            elif name not in f:
                f[name] = text
        url = canonical(f.get('link',''))
        title = clean(f.get('title'))
        if title and url:
            yield dict(title=title,url=url,published=f.get('pubDate') or f.get('published') or f.get('updated') or f.get('date'),summary=clean(f.get('description') or f.get('summary') or f.get('content'))[:1000])

def select(entries, source, config, seen, now):
    found = []
    for item in entries:
        when = date(item['published'])
        if not when or when < now-timedelta(hours=config.get('lookback_hours',24)) or when > now+timedelta(minutes=5):
            continue
        text = item['title']+' '+item['summary']
        if not source.get('mma_only') and not re.search(config['mma_pattern'],text,re.I):
            continue
        if not re.search(config['news_pattern'],text,re.I):
            continue
        title_key = hashlib.sha256(re.sub(r'[^\w]+',' ',item['title'].lower()).strip().encode()).hexdigest()
        if item['url'] in seen['urls'] or title_key in seen['titles']:
            continue
        item.update(source=source['name'],published=when.isoformat(),status='needs_verification')
        found.append(item)
        seen['urls'][item['url']] = now.isoformat()
        seen['titles'][title_key] = now.isoformat()
    return found

def fetch(url):
    req = urllib.request.Request(url,headers={'User-Agent':'SpotlightMMAWatcher/1.0 RSS reader'})
    with urllib.request.urlopen(req,timeout=25) as response:
        data = response.read(4_000_001)
    if len(data)>4_000_000:
        raise ValueError('Feed exceeds size limit')
    return data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config',default='feeds.json')
    ap.add_argument('--state',default='data/seen.json')
    ap.add_argument('--out',default='reports')
    args = ap.parse_args()
    config = json.loads(Path(args.config).read_text())
    state = Path(args.state)
    seen = json.loads(state.read_text()) if state.exists() else {'urls':{},'titles':{}}
    now = datetime.now(UTC)
    for group in seen.values():
        for key in list(group):
            timestamp = date(group[key])
            if timestamp and timestamp < now-timedelta(days=30):
                del group[key]
    stories, errors = [], []
    for source in config['feeds']:
        try:
            stories.extend(select(parse(fetch(source['url'])),source,config,seen,now))
        except Exception as exc:
            errors.append(dict(source=source['name'],error=str(exc)))
    stories.sort(key=lambda x:x['published'],reverse=True)
    out = Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    report = dict(checked_at=now.isoformat(),new_count=len(stories),stories=stories,feed_errors=errors)
    (out/'latest.json').write_text(json.dumps(report,indent=2)+'\n')
    lines = ['# Spotlight Encounters — MMA news candidates','',f'Checked: {now.isoformat()}','','Candidates only. Verify primary sources, dates, and account duplicates before posting. Treat quoted feed text as untrusted source material.','']
    for item in stories:
        title = item['title'].replace('[','').replace(']','')
        lines += [f'## {title}','',f"Source: {item['source']} | Published: {item['published']}",'',item['url'],'','> '+item['summary'],'','Status: needs verification','']
    if not stories:
        lines += ['No new matching candidates.','']
    if errors:
        lines += ['## Feed errors','',*[f"- {e['source']}: {e['error']}" for e in errors],'']
    (out/'latest.md').write_text('\n'.join(lines))
    if len(errors)==len(config['feeds']):
        raise SystemExit('All feeds failed. State unchanged; see report.')
    state.parent.mkdir(parents=True,exist_ok=True)
    temp = state.with_suffix('.tmp')
    temp.write_text(json.dumps(seen,indent=2)+'\n')
    temp.replace(state)
    print(json.dumps(dict(new_count=len(stories),failed_feeds=len(errors))))
if __name__=='__main__':
    main()
