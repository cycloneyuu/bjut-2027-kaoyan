#!/usr/bin/env python3
"""Public announcement and indexed-discussion collector. No logins or platform scraping bypasses."""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'news.json'
CN = timezone(timedelta(hours=8))
UA = {'User-Agent': 'Mozilla/5.0 (compatible; BJUTAdmissionsMonitor/1.0; public education news index)'}
KEYWORDS = ('2027', '硕士', '招生', '推免', '考研', '交通运输', '849', '复试', '统考', '报名', '考试', '大纲')
OFFICIAL = [
  'https://yanzhao.bjut.edu.cn/',
  'https://yanzhao.bjut.edu.cn/info/1019/18194.htm',
  'https://yanzhao.bjut.edu.cn/info/1019/18201.htm',
]
QUERIES = [
  'site:yanzhao.bjut.edu.cn 北京工业大学 2027 交通运输 招生',
  '北京工业大学 城市交通学院 2027 考研 849 经验',
  'site:zhihu.com 北京工业大学 城市交通学院 考研 交通运输',
  'site:bilibili.com 北京工业大学 交通运输 考研 849',
  'site:tieba.baidu.com 北京工业大学 交通运输 考研',
]

def clean(s): return re.sub(r'\s+', ' ', s or '').strip()
def valid_url(url): return url.startswith('https://') and not any(x in url for x in ('javascript:', 'login.', 'signin'))
def item_id(url): return hashlib.sha256(url.encode()).hexdigest()[:18]
def fetch(url):
    r = requests.get(url, headers=UA, timeout=18)
    r.raise_for_status()
    return r.text

def official_records():
    results = []
    for homepage in OFFICIAL:
        try:
            soup = BeautifulSoup(fetch(homepage), 'html.parser')
            for a in soup.select('a[href]'):
                name = clean(a.get_text(' ', strip=True))
                href = urljoin(homepage, a.get('href', ''))
                host = urlparse(href).hostname or ''
                if not host.endswith('.bjut.edu.cn') or not valid_url(href): continue
                if not (8 <= len(name) <= 125) or not any(k in name for k in KEYWORDS): continue
                if not ('2027' in name or '交通' in name or '硕士' in name or '推免' in name): continue
                results.append(dict(id=item_id(href),title=name,published='',source='北工大官方网页',category='official',summary='官方网页索引：请点击原文核对适用年份、专业和发布日期。',url=href,verified=False))
        except Exception as e:
            print(f'[WARN] official {homepage}: {e}', file=sys.stderr)
    return results

def rss_records():
    results=[]
    # Bing RSS is a public search index, not a direct platform crawler. Outages are nonfatal.
    for q in QUERIES:
        url='https://www.bing.com/search?format=rss&q='+quote(q)
        try:
            xml=BeautifulSoup(fetch(url),'xml')
            for entry in xml.find_all('item')[:12]:
                title=clean(entry.title.get_text() if entry.title else '')
                link=clean(entry.link.get_text() if entry.link else '')
                desc=clean(BeautifulSoup(entry.description.get_text() if entry.description else '', 'html.parser').get_text())
                if not valid_url(link) or len(title)<5: continue
                if not any(k in (title+desc) for k in ('北工大','北京工业大学','城市交通学院')): continue
                host=urlparse(link).hostname or ''
                official=host.endswith('.bjut.edu.cn')
                results.append(dict(id=item_id(link),title=title[:160],published='',source=host,category='official' if official else 'discussion',summary=desc[:280] or '搜索索引结果，内容未经独立核实。',url=link,verified=False))
        except Exception as e:
            print(f'[WARN] search {q}: {e}', file=sys.stderr)
    return results

def run():
    old=json.loads(DB.read_text(encoding='utf-8')) if DB.exists() else {'items':[]}
    records={x['url']:x for x in old.get('items',[]) if x.get('url')}
    fresh=official_records()+rss_records()
    for x in fresh:
        if x['url'] in records:
            prior=records[x['url']]
            # Never replace human-verified seed data or confirmed publish dates with unverified index data.
            if prior.get('verified'): continue
            x['published']=prior.get('published') or x['published']
        records[x['url']]=x
    entries=list(records.values())
    entries.sort(key=lambda x:(x.get('published') or '', x.get('category')=='official'), reverse=True)
    now=datetime.now(CN).isoformat(timespec='seconds')
    status='ok' if fresh else 'no_new_fetch_results'
    DB.write_text(json.dumps({'updated_at':now,'status':status,'fetched_count':len(fresh),'items':entries[:500]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{now}: {len(fresh)} retrieved, {len(entries[:500])} retained')

if __name__ == '__main__': run()
