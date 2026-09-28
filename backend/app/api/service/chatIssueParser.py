# encoding: UTF-8
"""Parse Feishu/Doubao daily issue markdown into day sessions + items."""
import re


DAY_HEADER_RE = re.compile(
    r'^#{1,3}\s*(?P<label>\d{1,2}\s*月\s*\d{1,2}\s*日(?:（[^）]+）|\([^)]+\))?)\s*$',
    re.M,
)
# **1. title** or 1. title or - title
ITEM_HEADER_RE = re.compile(
    r'^(?:\*\*)?\s*(?P<num>\d+)\s*[\.、．]\s*(?P<title>.+?)(?:\*\*)?\s*$',
    re.M,
)
BULLET_RE = re.compile(r'^[-*•]\s+(?P<title>.+)\s*$', re.M)
IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')


def parse_chat_issue_markdown(text):
    """Return list of {dayLabel, title, items:[{title, detail, sourceRef, images}]}."""
    if not text or not str(text).strip():
        return []
    raw = str(text).replace('\r\n', '\n').replace('\r', '\n').strip()
    day_spans = _split_by_day(raw)
    sessions = []
    for day_label, body in day_spans:
        items = _parse_items(body)
        if not items:
            continue
        sessions.append({
            'dayLabel': day_label or '',
            'title': _session_title(day_label, items),
            'items': items,
            'rawText': body.strip(),
        })
    if sessions:
        return sessions
    # no day headers: single session
    items = _parse_items(raw)
    if not items:
        items = _fallback_paragraphs(raw)
    if not items:
        return []
    return [{
        'dayLabel': '',
        'title': '聊天问题导入',
        'items': items,
        'rawText': raw,
    }]


def _split_by_day(text):
    matches = list(DAY_HEADER_RE.finditer(text))
    if not matches:
        return [('', text)]
    spans = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        spans.append((m.group('label').replace(' ', ''), text[start:end]))
    # content before first day header
    prefix = text[:matches[0].start()].strip()
    if prefix:
        spans.insert(0, ('', prefix))
    return spans


def _session_title(day_label, items):
    if day_label:
        return '聊天问题 · {}'.format(day_label)
    if items:
        return '聊天问题 · {}'.format((items[0].get('title') or '导入')[:40])
    return '聊天问题导入'


def _parse_items(body):
    matches = list(ITEM_HEADER_RE.finditer(body or ''))
    items = []
    if matches:
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            detail = (body[start:end] or '').strip()
            detail = detail.strip('-').strip()
            images = [u for _, u in IMAGE_RE.findall(detail)]
            items.append({
                'title': _clean_title(m.group('title')),
                'detail': detail,
                'sourceRef': m.group('num'),
                'images': images,
                'suggestType': _guess_type(m.group('title'), detail),
            })
        return items
    # bullet list fallback
    for m in BULLET_RE.finditer(body or ''):
        title = _clean_title(m.group('title'))
        if not title or title.startswith('#'):
            continue
        items.append({
            'title': title[:500],
            'detail': '',
            'sourceRef': '',
            'images': [],
            'suggestType': _guess_type(title, ''),
        })
    return items


def _fallback_paragraphs(text):
    chunks = [c.strip() for c in re.split(r'\n\s*\n', text) if c.strip()]
    items = []
    for idx, chunk in enumerate(chunks, start=1):
        lines = [ln.strip() for ln in chunk.split('\n') if ln.strip() and not ln.strip().startswith('---')]
        if not lines:
            continue
        title = _clean_title(lines[0])[:500]
        if not title:
            continue
        detail = '\n'.join(lines[1:]).strip()
        items.append({
            'title': title,
            'detail': detail,
            'sourceRef': str(idx),
            'images': [u for _, u in IMAGE_RE.findall(chunk)],
            'suggestType': _guess_type(title, detail),
        })
    return items


def _clean_title(title):
    t = (title or '').strip()
    t = re.sub(r'^\*\*|\*\*$', '', t).strip()
    t = re.sub(r'^【[^】]*】\s*', '', t)
    return t[:500]


def _guess_type(title, detail):
    blob = '{} {}'.format(title or '', detail or '')
    if re.search(r'用例|回归|测试点', blob):
        return 'case'
    if re.search(r'体验|优化|体验|文案|导航', blob) and not re.search(r'报错|失败|400|bug|缺陷|刷不出|置空', blob, re.I):
        return 'both'
    return 'bug'
