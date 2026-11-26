"""Keep pending candidates readable through GitHub's file connector between checks."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

def merge(previous, latest, now):
    cutoff = now - timedelta(days=7)
    entries = {}
    for item in previous + latest:
        when = datetime.fromisoformat(item['published'])
        if when >= cutoff:
            entries[item['url']] = item
    return sorted(entries.values(), key=lambda item: item['published'], reverse=True)

if __name__ == '__main__':
    data = Path('data')
    path = data/'candidates.json'
    previous = json.loads(path.read_text()) if path.exists() else []
    report = json.loads(Path('reports/latest.json').read_text())
    candidates = merge(previous, report['stories'], datetime.now(timezone.utc))
    path.write_text(json.dumps(candidates, indent=2)+'\n')
    for name in ('latest.json', 'latest.md'):
        (data/name).write_text((Path('reports')/name).read_text())
