#!/usr/bin/env python3
"""BJUT admissions public-news index: source-preserving, best-effort collection."""
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'news.json'
CN = timezone(timedelta(hours=8))
UA = {'User-Agent': 'Mozilla/5.0 (compatible; BJUTAdmissionsMonitor/1.1; public education index)'}
KEYWORDS = ('2027', '硕士', '招生', '推免', '考研', '交通运输', '849', '复试', '统考', '报名', '考试', '大纲')
OFFICIAL = ['https://yanzhao.bjut.edu.cn/', 'https://yanzhao.bjut.edu.cn/info/1019/18194.htm', 'https://yanzhao.bjut.edu.cn/info/1019/18201.htm']
QUERIES = [
    'site:yanzhao.bjut.edu.cn 北京工业大学 2027 交通运输 招生',
    '北京工业大学 城市交通学院 2027 考研 849 经验',
    'site:zhihu.com 北京工业大学 城市交通学院 考研 交通运输',
    'site:bilibili.com 北京工业大学 交通运输 考研 849',
    'site:tieba.baidu.com 北京工业大学 交通运输 考研',
    'site:xiaohongshu.com 北京工业大学 城市交通学院 2027 考研',
    'site:xiaohongshu.com 北京工业大学 交通运输 849',
    'site:mp.weixin.qq.com 北京工业大学 城市交通学院 2027 考研',
    'site:mp.weixin.qq.com 北京工业大学 交通运输 849 考研',
]

def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()

def valid_url(url):
    return url.startswith('https://') and not any(x in url for x in ('javascript:', 'login.', 'signin'))

def item_id(url):
    return hashlib.sha256(url.encode()).hexdigest()[:18]

def fetch(url):
    r = requests.get(url, headers=UA, timeout=18)
    r.raise_for_status()
    raw = r.content
    # Some government/university sites omit the charset; requests defaults to Latin-1.
    # Decode bytes explicitly instead of trusting a missing/wrong HTTP charset.
    preferred = ['utf-8-sig', 'gb18030']
    match = re.search(br'charset\s*=\s*["\']?([\w\-]+)', raw[:4096], re.I)
    if match:
        declared = match.group(1).decode('ascii', errors='ignore').lower()
        if declared in ('gbk', 'gb2312', 'gb18030'):
            preferred = ['gb18030', 'utf-8-sig']
    for encoding in preferred:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')

def mojibake(text):
    # Existing database entries may contain UTF-8 decoded incorrectly as Latin-1.
    text = text or ''
    return any(tok in text for tok in ('å\x8c', 'äº', 'ç¡', 'æ\x8b', 'å¹', 'å¤', 'é\x80', 'ã\x80', 'ï¼')) or text.count('å') >= 2

def official_records():
    results = []
    for homepage in OFFICIAL:
        try:
            soup = BeautifulSoup(fetch(homepage), 'html.parser')
            for a in soup.select('a[href]'):
                name = clean(a.get_text(' ', strip=True))
                href = urljoin(homepage, a.get('href', ''))
                host = urlparse(href).hostname or ''
                if not (host == 'bjut.edu.cn' or host.endswith('.bjut.edu.cn')) or not valid_url(href):
                    continue
                if not (8 <= len(name) <= 125) or not any(k in name for k in KEYWORDS):
                    continue
                if not any(k in name for k in ('2027', '交通', '硕士', '推免')):
                    continue
                if mojibake(name):
                    continue
                results.append(dict(id=item_id(href), title=name, published='', source='北工大官方网页', category='official', summary='官方网页索引：请点击原文核对适用年份、专业和发布日期。', url=href, verified=False))
        except Exception as exc:
            print(f'[WARN] official {homepage}: {exc}', file=sys.stderr)
    return results

def rss_records():
    results = []
    for query in QUERIES:
        url = 'https://www.bing.com/search?format=rss&q=' + quote(query)
        try:
            xml = BeautifulSoup(fetch(url), 'xml')
            for entry in xml.find_all('item')[:12]:
                title = clean(entry.title.get_text() if entry.title else '')
                link = clean(entry.link.get_text() if entry.link else '')
                desc = clean(BeautifulSoup(entry.description.get_text() if entry.description else '', 'html.parser').get_text())
                combined = title + ' ' + desc
                if not valid_url(link) or len(title) < 5 or mojibake(title):
                    continue
                if not any(k in combined for k in ('北工大', '北京工业大学', '城市交通学院')):
                    continue
                if not any(k in combined for k in ('考研', '交通运输', '交通工程', '城市交通学院', '849', '2027', '硕士招生')):
                    continue
                host = urlparse(link).hostname or ''
                official = host == 'bjut.edu.cn' or host.endswith('.bjut.edu.cn')
                results.append(dict(id=item_id(link), title=title[:160], published='', source=host, category='official' if official else 'discussion', summary=desc[:280] or '公开搜索结果，内容未经独立核实。', url=link, verified=False))
        except Exception as exc:
            print(f'[WARN] search {query}: {exc}', file=sys.stderr)
    return results

def run():
    old = json.loads(DB.read_text(encoding='utf-8')) if DB.exists() else {'items': []}
    records = {x['url']: x for x in old.get('items', []) if x.get('url') and (x.get('verified') or not mojibake(x.get('title', '')))}
    fresh = official_records() + rss_records()
    for item in fresh:
        if item['url'] in records:
            previous = records[item['url']]
            if previous.get('verified'):
                continue
            item['published'] = previous.get('published') or item['published']
        records[item['url']] = item
    entries = list(records.values())
    entries.sort(key=lambda x: (x.get('published') or '', x.get('category') == 'official'), reverse=True)
    now = datetime.now(CN).isoformat(timespec='seconds')
    status = 'ok' if fresh else 'no_new_fetch_results'
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.write_text(json.dumps({'updated_at': now, 'status': status, 'fetched_count': len(fresh), 'items': entries[:500]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{now}: {len(fresh)} retrieved, {len(entries[:500])} retained')

if __name__ == '__main__':
    run()
