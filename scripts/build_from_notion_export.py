import html
import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
from zoneinfo import ZoneInfo

SITE_ROOT = Path(__file__).resolve().parents[1]
SRC = (SITE_ROOT / 'notion_docs').resolve()
OUT = SITE_ROOT.resolve()
DATA_DIR = (SITE_ROOT / 'data').resolve()
CSS_VERSION = str(int(time.time()))

if not SRC.exists():
    raise SystemExit('notion_docs not found')

# Rebuild generated site outputs only (keep source/docs/scripts under site/)
generated_dirs = [
    OUT / "content",
    OUT / "daily",
    OUT / "pages",
    OUT / "assets",
]
generated_files = [
    OUT / "index.html",
    OUT / "daily.html",
    OUT / "resume.html",
    OUT / "video-coding.html",
]

for d in generated_dirs:
    if d.exists():
        shutil.rmtree(d)

for f in generated_files:
    if f.exists():
        f.unlink()

OUT.mkdir(parents=True, exist_ok=True)

# Discover markdown files
md_files = sorted(
    p for p in SRC.rglob('*.md')
    if ':Zone.Identifier' not in p.name
)

BLOG_INDEX_KEY = "CryptoSherry's Blog 77b891042f264fea9326e33ad53f0b2b.md"
VIDEO_PAGE_KEY = "Sherry's CryptoSphere 39e39671913048038a812f16e739c273.md"
PODCAST_PAGE_KEY = "CryptoSherry's Live Podcast Series fc580b55f6004fe1a40ae816e4d4a0ca.md"

if not md_files:
    raise SystemExit('No markdown files found in notion_docs')

# Root markdown (homepage exported at notion_docs/*.md)
root_candidates = [p for p in md_files if p.parent == SRC]
root_md = root_candidates[0] if root_candidates else md_files[0]

DISPLAY_NAME_MAP = {
    "CryptoSherry's Blog": "Blog",
    "Publications and Reposting": "Publications",
    "Sherry's CryptoSphere": "Video",
    "CryptoSherry's Live Podcast Series": "Podcast",
}

PAGE_TITLE_OVERRIDE = {
    "Publications and Reposting": "Publications & Reposting",
}

ET = ZoneInfo("America/New_York")

DAILY_AI = [
    {
        "id": "ai-2026-03-05-mcp-hub",
        "date": "2026-03-05",
        "generated_at_utc": "2026-03-05T14:00:00Z",
        "source_platform": "github",
        "source_url": "https://github.com/modelcontextprotocol/servers",
        "title": "MCP Servers Hub",
        "description": "A practical index of production-ready MCP servers for tool-calling and workflow automation.",
        "description_zh": "一个实用的 MCP 服务器索引，聚焦可用于工具调用和工作流自动化的生产级实现。",
        "summary": "Strong signal from ecosystem adoption, clear docs, and active maintenance. Good fit for agent tooling builders.",
        "summary_zh": "生态采用度高、文档完整、维护活跃，适合做 Agent 工具链与集成的开发者参考。",
        "tags": ["mcp", "tool-calling", "workflow"],
        "category": "Tooling",
        "updated_at": "2026-03-05T12:10:00Z",
        "score_raw": 17500,
    },
    {
        "id": "ai-2026-03-04-ragflow",
        "date": "2026-03-04",
        "generated_at_utc": "2026-03-04T14:00:00Z",
        "source_platform": "github",
        "source_url": "https://github.com/infiniflow/ragflow",
        "title": "RAGFlow",
        "description": "Open-source RAG workflow stack with retrieval pipelines and enterprise-ready controls.",
        "description_zh": "开源 RAG 工作流方案，包含检索管道与企业级控制能力。",
        "summary": "Useful for teams building document-grounded assistants with explicit workflow control.",
        "summary_zh": "适合需要文档检索增强并强调流程可控性的团队。",
        "tags": ["rag", "llm", "workflow"],
        "category": "Skill / Workflow",
        "updated_at": "2026-03-04T10:30:00Z",
        "score_raw": 52000,
    },
    {
        "id": "ai-2026-03-03-langgraph",
        "date": "2026-03-03",
        "generated_at_utc": "2026-03-03T14:00:00Z",
        "source_platform": "github",
        "source_url": "https://github.com/langchain-ai/langgraph",
        "title": "LangGraph",
        "description": "Stateful orchestration for long-running, tool-enabled LLM agents.",
        "description_zh": "支持长任务与工具调用的有状态 LLM Agent 编排框架。",
        "summary": "Widely adopted for agent runtime design, especially when memory and retries matter.",
        "summary_zh": "在 Agent 运行时设计中使用广泛，尤其适用于需要记忆和重试机制的场景。",
        "tags": ["agent", "llm-agent", "langchain"],
        "category": "Agent Framework",
        "updated_at": "2026-03-03T08:05:00Z",
        "score_raw": 21000,
    },
]

DAILY_MARKET = [
    {
        "id": "market-2026-03-05-01",
        "date": "2026-03-05",
        "generated_at_utc": "2026-03-05T14:00:00Z",
        "source_platform": "x",
        "source_url": "https://x.com/",
        "title": "ETH L2 activity accelerated as fee compression continued this week.",
        "title_zh": "本周 ETH L2 活跃度继续提升，手续费压缩趋势延续。",
        "summary": "Discussion centers on sequencing economics, DA costs, and bridge retention.",
        "summary_zh": "讨论焦点集中在排序器经济模型、数据可用性成本与跨链留存。",
        "tags": ["ETH", "L2", "DeFi"],
        "engagement": 18400,
    },
    {
        "id": "market-2026-03-05-02",
        "date": "2026-03-05",
        "generated_at_utc": "2026-03-05T14:00:00Z",
        "source_platform": "reddit",
        "source_url": "https://www.reddit.com/r/ethereum/",
        "title": "Developers debated modular rollup UX trade-offs in mainstream onboarding.",
        "title_zh": "开发者围绕模块化 Rollup 在主流用户 onboarding 中的体验权衡展开讨论。",
        "summary": "Most comments highlight wallet abstraction and failed-tx recovery as key blockers.",
        "summary_zh": "多数评论认为钱包抽象与失败交易恢复是关键瓶颈。",
        "tags": ["Ethereum", "L2", "UX"],
        "engagement": 9200,
    },
    {
        "id": "market-2026-03-05-03",
        "date": "2026-03-05",
        "generated_at_utc": "2026-03-05T14:00:00Z",
        "source_platform": "x",
        "source_url": "https://x.com/",
        "title": "DePIN projects saw rising mentions as AI inference demand moved to edge supply.",
        "title_zh": "随着 AI 推理需求向边缘供给迁移，DePIN 项目讨论热度上升。",
        "summary": "Narrative focus shifted to verifiable compute and sustainable node economics.",
        "summary_zh": "叙事重心转向可验证算力与可持续节点经济模型。",
        "tags": ["DePIN", "AI x Crypto", "Infrastructure"],
        "engagement": 8700,
    },
]


def load_data_list(path: Path, fallback: list[dict]) -> list[dict]:
    if not path.exists():
        return fallback
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return fallback


DAILY_AI = load_data_list(DATA_DIR / "daily_ai.json", DAILY_AI)
DAILY_AI_HISTORY = load_data_list(DATA_DIR / "daily_ai_history.json", DAILY_AI)
DAILY_MARKET = load_data_list(DATA_DIR / "daily_market.json", DAILY_MARKET)


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r'\.[^.]+$', '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or 'page'


# Assign each markdown file a unique output html path under site/pages/
md_to_html_rel = {}
used = set()
for md in md_files:
    rel = md.relative_to(SRC)
    # keep some hierarchy in filename for readability and uniqueness
    stem = slugify('/'.join(rel.with_suffix('').parts))
    out_rel = Path('pages') / f'{stem}.html'
    i = 2
    while str(out_rel) in used:
        out_rel = Path('pages') / f'{stem}-{i}.html'
        i += 1
    used.add(str(out_rel))
    md_to_html_rel[md.resolve()] = out_rel

# Copy assets (images/files) preserving folder structure under site/content/
for src_path in SRC.rglob('*'):
    if src_path.is_dir():
        continue
    if ':Zone.Identifier' in src_path.name:
        continue
    if src_path.suffix.lower() == '.md':
        continue
    rel = src_path.relative_to(SRC)
    dest = OUT / 'content' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dest)


# Find top nav items from root markdown links
def parse_root_links(md_text: str, current_md: Path):
    items = []
    pat = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    for m in pat.finditer(md_text):
        label = m.group(1).strip()
        link = m.group(2).strip()
        if link.startswith('http://') or link.startswith('https://') or link.startswith('#'):
            continue
        target = resolve_local_path(link, current_md)
        if target and target.suffix.lower() == '.md' and target.exists():
            items.append((DISPLAY_NAME_MAP.get(label, label), target.resolve()))
    # dedupe preserve order
    seen = set()
    out = []
    for label, tgt in items:
        key = str(tgt)
        if key in seen:
            continue
        seen.add(key)
        out.append((label, tgt))
    return out


def resolve_local_path(link: str, current_md: Path):
    clean = link.split('#')[0].split('?')[0]
    if not clean:
        return None
    decoded = unquote(clean)
    p = Path(decoded)
    if p.is_absolute():
        return None
    # notion export links are relative to root folder in many files, try both
    cand1 = (current_md.parent / p).resolve()
    if cand1.exists():
        return cand1
    cand2 = (SRC / p).resolve()
    if cand2.exists():
        return cand2
    return cand1


def is_youtube_url(url: str) -> bool:
    return ('youtu.be/' in url) or ('youtube.com/watch' in url)


def extract_youtube_id(url: str) -> str:
    if 'youtu.be/' in url:
        tail = url.split('youtu.be/', 1)[1]
        return tail.split('?', 1)[0].split('&', 1)[0].strip('/')
    if 'youtube.com/watch' in url and 'v=' in url:
        tail = url.split('v=', 1)[1]
        return tail.split('&', 1)[0].strip('/')
    return ''


def render_youtube_card(title: str, url: str) -> str:
    video_id = extract_youtube_id(url)
    thumb = f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg' if video_id else ''
    safe_title = apply_text_styles(html.escape(title))
    safe_url = html.escape(url)
    safe_thumb = html.escape(thumb)
    return (
        '<article class="yt-card">'
        '<div class="yt-body">'
        f'<h3 class="yt-title">{safe_title}</h3>'
        '<p class="yt-desc">Watch this episode on YouTube.</p>'
        f'<a class="yt-link" href="{safe_url}" target="_blank" rel="noopener">'
        '<span class="yt-icon" aria-hidden="true"></span>'
        f'{safe_url}'
        '</a>'
        '</div>'
        f'<a class="yt-thumb-wrap" href="{safe_url}" target="_blank" rel="noopener">'
        f'<img class="yt-thumb" src="{safe_thumb}" alt="{html.escape(title)} thumbnail" loading="lazy" width="480" height="360" />'
        '</a>'
        '</article>'
    )


def inline_format(text: str, current_md: Path, current_html_rel: Path):
    placeholders = {}
    idx = 0

    def hold(s: str) -> str:
        nonlocal idx
        key = f'@@P{idx}@@'
        placeholders[key] = s
        idx += 1
        return key

    # images first
    def img_sub(m):
        alt = html.escape(m.group(1).strip())
        link = m.group(2).strip()
        href = map_link(link, current_md, current_html_rel, for_image=True)
        return hold(f'<img src="{html.escape(href)}" alt="{alt}" loading="lazy" width="1200" height="675" />')

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', img_sub, text)

    # links
    def link_sub(m):
        label_raw = m.group(1).strip()
        href_raw = m.group(2).strip()
        href = map_link(href_raw, current_md, current_html_rel, for_image=False)
        label = apply_text_styles(label_raw)
        if is_youtube_url(href):
            return hold(
                f'<a class="youtube-inline" href="{html.escape(href)}" target="_blank" rel="noopener">'
                '<span class="yt-icon" aria-hidden="true"></span>'
                f'{label}'
                '</a>'
            )
        target = ' target="_blank" rel="noopener"' if href.startswith('http://') or href.startswith('https://') else ''
        return hold(f'<a href="{html.escape(href)}"{target}>{label}</a>')

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_sub, text)

    escaped = html.escape(text)
    escaped = apply_text_styles(escaped)

    for k, v in placeholders.items():
        escaped = escaped.replace(k, v)
    return escaped


def apply_text_styles(text: str):
    # Bold/italic/code minimal support
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
    return text


def normalize_heading_text(text: str) -> str:
    # Headings should keep consistent typographic weight; remove markdown emphasis markers.
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # Remove leftover emphasis markers like trailing "**" or "****"
    text = text.replace('*', '')
    return re.sub(r'\s+', ' ', text).strip()


def map_link(link: str, current_md: Path, current_html_rel: Path, for_image: bool):
    if link.startswith('http://') or link.startswith('https://') or link.startswith('mailto:'):
        return link

    # keep anchors
    if link.startswith('#'):
        return link

    # split query/hash
    base = link
    frag = ''
    if '#' in base:
        base, h = base.split('#', 1)
        frag = '#' + h
    query = ''
    if '?' in base:
        base, q = base.split('?', 1)
        query = '?' + q

    target = resolve_local_path(base, current_md)
    if target is None:
        return link

    if target.suffix.lower() == '.md' and target.exists():
        target_html_rel = md_to_html_rel.get(target.resolve())
        if target_html_rel:
            return os.path.relpath(target_html_rel, current_html_rel.parent).replace('\\', '/') + frag

    # local asset file
    rel_content = Path('content') / target.relative_to(SRC)
    return os.path.relpath(rel_content, current_html_rel.parent).replace('\\', '/') + query + frag


def md_to_html(md_text: str, current_md: Path, current_html_rel: Path):
    lines = md_text.splitlines()
    if "Publications and Reposting" in current_md.name:
        lines = [ln for ln in lines if not re.search(r'(?i)\bpublish(?:ed)?\s+on\b', ln)]
    out = []
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append('</ul>')
            in_ul = False
        if in_ol:
            out.append('</ol>')
            in_ol = False

    for raw in lines:
        line = raw.rstrip('\n')
        s = line.strip()

        if not s:
            close_lists()
            continue

        # headings
        hm = re.match(r'^(#{1,6})\s+(.*)$', s)
        if hm:
            close_lists()
            level = len(hm.group(1))
            heading_text = normalize_heading_text(hm.group(2))
            heading_text = PAGE_TITLE_OVERRIDE.get(heading_text, heading_text)
            out.append(f'<h{level}>{inline_format(heading_text, current_md, current_html_rel)}</h{level}>')
            continue

        # Remove publication date lines in Publications page
        if "Publications and Reposting" in current_md.name and re.match(r'(?i)^published on\\b', s):
            continue

        # ordered list
        om = re.match(r'^\d+[\.)]\s+(.*)$', s)
        if om:
            if in_ul:
                out.append('</ul>')
                in_ul = False
            if not in_ol:
                out.append('<ol>')
                in_ol = True
            out.append(f'<li>{inline_format(om.group(1), current_md, current_html_rel)}</li>')
            continue

        # unordered list
        um = re.match(r'^[-*+]\s+(.*)$', s)
        if um:
            if in_ol:
                out.append('</ol>')
                in_ol = False
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            out.append(f'<li>{inline_format(um.group(1), current_md, current_html_rel)}</li>')
            continue

        close_lists()

        # standalone youtube link card
        ytm = re.match(r'^\[([^\]]+)\]\((https?://[^)]+)\)$', s)
        if ytm and is_youtube_url(ytm.group(2).strip()):
            out.append(render_youtube_card(ytm.group(1).strip(), ytm.group(2).strip()))
            continue

        # Clean up duplicated article-title link block in Blog index:
        # keep "Read more" links and the single publications link.
        if current_md.name == BLOG_INDEX_KEY:
            lm = re.match(r'^\[([^\]]+)\]\(([^)]+)\)$', s)
            if lm:
                label_raw = lm.group(1).strip()
                label_plain = re.sub(r'[*_`]+', '', label_raw).strip().lower()
                keep = (
                    label_plain.startswith("read more")
                    or "article publications and reposting" in label_plain
                )
                if not keep:
                    continue

        # blockquote
        if s.startswith('>'):
            out.append(f'<blockquote>{inline_format(s.lstrip('> ').strip(), current_md, current_html_rel)}</blockquote>')
            continue

        # standalone image line
        if s.startswith('!['):
            out.append(f'<p class="media">{inline_format(s, current_md, current_html_rel)}</p>')
            continue

        out.append(f'<p>{inline_format(s, current_md, current_html_rel)}</p>')

    close_lists()
    return '\n'.join(out)


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Syne:wght@500;600;700;800&display=swap');

:root {
  --bg: #eef1f7;
  --surface: #ffffff;
  --ink: #121826;
  --muted: #4b5567;
  --line: #d8deeb;
  --blue: #1f6fff;
  --blue-soft: #e8f0ff;
  --focus: #1f6fff;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Manrope", "PingFang SC", "Helvetica Neue", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(1100px 450px at 88% -8%, #dbe7ff 0%, transparent 58%),
    radial-gradient(920px 340px at 8% 4%, #f8fbff 0%, transparent 60%),
    linear-gradient(180deg, #f5f7fc 0%, #edf0f6 100%),
    var(--bg);
}
.container { width: min(1120px, calc(100% - 2rem)); margin: 0 auto; }
.top {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(14px) saturate(170%);
  background: rgba(244, 247, 253, 0.72);
  border-bottom: 1px solid rgba(173, 186, 214, 0.45);
}
.top-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: .75rem;
  padding: .72rem 0;
}
.brand {
  text-decoration: none;
  color: var(--ink);
  font-family: "Syne", sans-serif;
  font-weight: 700;
  letter-spacing: .02em;
}
.top-actions {
  display: flex;
  align-items: center;
  gap: .55rem;
}
.nav { display: flex; flex-wrap: wrap; gap: .35rem; }
.nav a {
  text-decoration: none;
  color: var(--ink);
  border: 1px solid transparent;
  border-radius: 999px;
  padding: .34rem .74rem;
  font-size: .86rem;
  transition: background .22s ease, border-color .22s ease, transform .22s ease;
}
.nav a:hover {
  border-color: #c3d1ee;
  background: rgba(255,255,255,.96);
  transform: translateY(-1px);
}
.lang-toggle {
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
  color: #182133;
  font-size: .78rem;
  font-weight: 600;
  padding: .38rem .72rem;
  cursor: pointer;
}
.lang-toggle:hover { border-color: #bcc8e5; }
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  z-index: 1000;
  background: #0f172a;
  color: #fff;
  text-decoration: none;
  padding: .45rem .68rem;
  border-radius: 8px;
}
.skip-link:focus-visible {
  left: .8rem;
  top: .6rem;
}
.nav a:focus-visible,
.social-btn:focus-visible,
.section-card:focus-visible,
.yt-link:focus-visible,
.youtube-inline:focus-visible,
.lang-toggle:focus-visible,
a:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}
main { padding: 1.2rem 0 2rem; }
article {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(249,251,255,.94));
  padding: 1.2rem;
  box-shadow: 0 16px 44px rgba(27, 44, 89, .10);
}
h1, h2, h3 { font-family: "Manrope", "PingFang SC", "Helvetica Neue", sans-serif; letter-spacing: .005em; }
.brand { font-family: "Syne", "Manrope", sans-serif; letter-spacing: .01em; }
h1 {
  font-size: 2.02rem;
  line-height: 1.28;
  margin: .4rem 0 .8rem;
  padding-top: .06em;
  padding-bottom: .14em;
  text-wrap: balance;
  overflow: visible;
}
h2 {
  font-size: 1.45rem;
  line-height: 1.3;
  margin: 1.1rem 0 .65rem;
  padding-top: .03em;
  padding-bottom: .06em;
  overflow: visible;
}
h3 { font-size: 1.15rem; line-height: 1.32; margin: 1rem 0 .5rem; padding-bottom: .03em; overflow: visible; }
h1, h2, h3, h4, h5, h6 { scroll-margin-top: 88px; }
p, li { line-height: 1.7; color: #2d3240; }
a { color: var(--blue); }
ul, ol { padding-left: 1.2rem; }
img { max-width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--line); }
.media img { width: min(100%, 760px); }
blockquote {
  margin: .8rem 0;
  border-left: 3px solid #d2d7df;
  padding: .2rem .8rem;
  color: #4f5868;
  background: #fafbfc;
}
code {
  background: #f2f3f6;
  border: 1px solid #e5e8ef;
  border-radius: 6px;
  padding: .08rem .34rem;
}
.cards { display: grid; gap: .7rem; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
.card {
  display: block;
  text-decoration: none;
  color: var(--ink);
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 12px;
  padding: .72rem;
}
.card:hover { border-color: #cfd6e2; }
.card h3 { margin: 0; font-size: 1rem; }
.small { color: var(--muted); font-size: .87rem; margin-top: .3rem; }
.exp { border: 1px solid var(--line); border-radius: 12px; padding: .8rem; margin: .7rem 0; }
.exp-head { display: flex; justify-content: space-between; gap: .8rem; flex-wrap: wrap; }
.time { color: var(--muted); font-size: .86rem; }
/* Keep heading rhythm consistent in list-heavy pages like Blog */
article h2, article h3, article h4 {
  font-weight: 600;
  letter-spacing: 0;
}
.youtube-inline {
  display: inline-flex;
  align-items: center;
  gap: .38rem;
  color: #1e2431;
  text-decoration: none;
}
.youtube-inline:hover { color: #c11b1b; }
.yt-icon {
  width: 15px;
  height: 11px;
  border-radius: 3px;
  background: #ff0000;
  position: relative;
  display: inline-block;
}
.yt-icon::before {
  content: "";
  position: absolute;
  left: 5px;
  top: 2.4px;
  width: 0;
  height: 0;
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
  border-left: 5px solid #fff;
}
.yt-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 250px;
  gap: .9rem;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  margin: .7rem 0;
  background: #fff;
}
.yt-body { padding: .78rem .92rem; }
.yt-title { margin: 0 0 .42rem; font-size: 1.03rem; }
.yt-desc { margin: 0 0 .56rem; color: #576072; font-size: .92rem; line-height: 1.48; }
.yt-link {
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  color: #202533;
  text-decoration: none;
  font-size: .9rem;
  word-break: break-all;
}
.yt-thumb-wrap {
  display: block;
  height: 100%;
}
.yt-thumb {
  width: 100%;
  height: 100%;
  min-height: 128px;
  object-fit: cover;
  border: 0;
  border-left: 1px solid var(--line);
  border-radius: 0;
}
.hero {
  border: 1px solid var(--line);
  border-radius: 20px;
  background:
    radial-gradient(500px 220px at 88% 8%, rgba(120, 155, 255, .20), transparent 60%),
    radial-gradient(480px 220px at -8% 0%, rgba(134, 166, 255, .18), transparent 62%),
    linear-gradient(150deg, #f3f7ff 0%, #ffffff 54%, #f3f8ff 100%);
  padding: 1.1rem 1.1rem 1.25rem;
  margin-bottom: .95rem;
  position: relative;
  overflow: hidden;
}
.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: linear-gradient(130deg, transparent 0%, rgba(255,255,255,.36) 45%, transparent 70%);
  pointer-events: none;
}
.hero h1 { margin: .2rem 0 .65rem; }
.hero p { margin: .38rem 0; max-width: 76ch; }
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  align-items: center;
  gap: 1rem;
}
.hero-avatar-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
}
.hero-avatar {
  width: 200px;
  height: 200px;
  border-radius: 20px;
  object-fit: cover;
  border: 1px solid #d1dcf6;
  box-shadow: 0 14px 28px rgba(24, 42, 86, .18);
}
.hero-actions {
  margin-top: .72rem;
  display: flex;
  align-items: center;
  gap: .55rem;
}
.social-btn {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  font-size: .95rem;
  box-shadow: 0 8px 16px rgba(23, 65, 156, .22);
  transition: transform .22s ease, box-shadow .22s ease, filter .22s ease;
}
.calendly-btn { background: #006bff; }
.calendly-btn:hover {
  background: #0055cc;
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 12px 24px rgba(14, 58, 160, .28);
}
.calendly-icon {
  width: 18px;
  height: 18px;
  display: block;
}
.section-links {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff, #f8faff);
  padding: .88rem;
}
.section-cards {
  display: grid;
  gap: .72rem;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.section-card {
  display: block;
  text-decoration: none;
  color: #1e2634;
  border: 1px solid #d0daf0;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff, #f9fbff);
  padding: .75rem .78rem;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}
.section-card:hover {
  border-color: #9cb3e8;
  transform: translateY(-3px);
  box-shadow: 0 14px 30px rgba(19, 35, 73, .12);
}
.section-head {
  display: flex;
  align-items: center;
  gap: .5rem;
}
.section-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: var(--blue-soft);
  border: 1px solid #cfe0ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}
.section-icon svg { width: 16px; height: 16px; stroke: #1e40af; fill: none; stroke-width: 1.9; stroke-linecap: round; stroke-linejoin: round; }
.section-title {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
}
.section-desc {
  margin: .5rem 0 0;
  font-size: .88rem;
  line-height: 1.45;
  color: #5a6578;
}
.feed-layout {
  margin-top: .95rem;
  display: grid;
  gap: .78rem;
}
.feed-board {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: linear-gradient(165deg, #ffffff, #f4f8ff);
  padding: .9rem;
}
.feed-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .78rem;
}
.feed-card {
  border: 1px solid #cfdaf3;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  padding: .8rem;
}
.feed-label {
  margin: 0;
  font-size: .78rem;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: #4d5d7e;
  font-family: "Exo 2", sans-serif;
}
.feed-title {
  margin: .3rem 0 .45rem;
  font-size: 1.08rem;
}
.feed-meta {
  display: flex;
  flex-wrap: wrap;
  gap: .35rem;
  margin: .45rem 0 .6rem;
}
.chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  border: 1px solid #d5def5;
  background: #f5f8ff;
  color: #3b4f7a;
  font-size: .74rem;
  padding: .16rem .52rem;
}
.feed-item {
  display: block;
  border: 1px solid #d7def0;
  border-radius: 12px;
  background: #fff;
  text-decoration: none;
  color: inherit;
  padding: .74rem .8rem;
  margin: .55rem 0 0;
}
.feed-item:hover {
  border-color: #9ab0e8;
  box-shadow: 0 12px 24px rgba(28, 49, 95, .10);
}
.feed-item h3 {
  margin: 0 0 .35rem;
  font-size: 1rem;
}
.ai-history-scroll {
  margin-top: .2rem;
  max-height: 520px;
  overflow-y: auto;
  padding-right: .2rem;
}
.ai-history-scroll::-webkit-scrollbar {
  width: 8px;
}
.ai-history-scroll::-webkit-scrollbar-thumb {
  background: #c9d6f4;
  border-radius: 999px;
}
.market-list { margin: .5rem 0 0; padding: 0; list-style: none; }
.market-list li + li { margin-top: .55rem; }
.market-link {
  display: block;
  border: 1px solid #d7def0;
  border-radius: 10px;
  padding: .62rem .7rem;
  text-decoration: none;
  color: #1f2b42;
}
.market-link:hover { border-color: #9fb2e4; background: #f8fbff; }
.market-card {
  border: 1px solid #cfdbf6;
  border-radius: 10px;
  padding: .62rem .7rem;
  color: #1f2b42;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  min-width: 0;
  overflow: hidden;
}
.market-card p { margin: .28rem 0; }
.market-meta-line {
  margin-top: .35rem;
  display: flex;
  flex-wrap: wrap;
  gap: .35rem;
}
.market-source a {
  display: inline;
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-all;
}
.disclaimer {
  margin: .65rem 0 0;
  padding: .55rem .7rem;
  font-size: .82rem;
  color: #5b657b;
  background: #f8f9fc;
  border: 1px dashed #c7d0e4;
  border-radius: 10px;
}
.mini-note {
  font-size: .79rem;
  color: #5f6c88;
}
.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: .55rem;
  margin-top: .7rem;
}
.btn-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid #b8c8eb;
  background: #eef4ff;
  color: #1f3d7a;
  font-weight: 600;
  text-decoration: none;
  padding: .42rem .8rem;
  font-size: .82rem;
}
.btn-chip:hover { border-color: #94aee5; background: #e2ecff; }
.vc-grid {
  display: grid;
  gap: .72rem;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}
.vc-card {
  border: 1px solid #d7def0;
  border-radius: 12px;
  background: #fff;
  padding: .75rem .78rem;
}
.vc-card h3 { margin: 0 0 .38rem; font-size: 1.02rem; }
.vc-card p { margin: .25rem 0 .45rem; }
.vc-card .chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: .33rem;
}
.vc-video-grid {
  display: grid;
  gap: .72rem;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
.vc-video {
  display: block;
  border: 1px solid #d7def0;
  border-radius: 12px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  background: #fff;
}
.vc-video:hover {
  border-color: #9fb2e4;
  box-shadow: 0 10px 20px rgba(28, 49, 95, .08);
}
.vc-video img {
  width: 100%;
  height: 168px;
  object-fit: cover;
  border: 0;
  border-bottom: 1px solid #d7def0;
  border-radius: 0;
}
.vc-video-body { padding: .68rem .75rem .74rem; }
.vc-video-body h3 { margin: 0 0 .35rem; font-size: .98rem; }
@media (max-width: 820px) {
  .top-inner { flex-direction: column; align-items: flex-start; }
  .top-actions { width: 100%; flex-wrap: wrap; }
  .yt-card { grid-template-columns: 1fr; }
  .yt-thumb { border-left: 0; border-top: 1px solid var(--line); min-height: 180px; }
  .hero-grid { grid-template-columns: 1fr; }
  .hero-avatar { width: 150px; height: 150px; border-radius: 14px; }
  .feed-grid { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
@media (prefers-reduced-motion: no-preference) {
  .hero,
  .feed-board,
  .section-links {
    animation: rise-in .6s ease both;
  }
  .feed-board { animation-delay: .05s; }
  .section-links { animation-delay: .1s; }
}
@keyframes rise-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
"""

(OUT / 'assets').mkdir(exist_ok=True)
(OUT / 'assets' / 'style.css').write_text(CSS, encoding='utf-8')

root_text = root_md.read_text(encoding='utf-8', errors='ignore')
nav_items = parse_root_links(root_text, root_md)


def nav_html(current_html_rel: Path):
    home_href = os.path.relpath(Path("index.html"), current_html_rel.parent).replace("\\", "/")
    vibe_href = os.path.relpath(Path("video-coding.html"), current_html_rel.parent).replace("\\", "/")
    about_href = os.path.relpath(Path("resume.html"), current_html_rel.parent).replace("\\", "/")
    nav_map = {}
    for label, target in nav_items:
        if label in {"Publications", "Podcast"}:
            continue
        href = os.path.relpath(md_to_html_rel[target.resolve()], current_html_rel.parent).replace('\\', '/')
        nav_map[label] = href

    parts = [f'<a href="{home_href}">Home</a>']
    if "Blog" in nav_map:
        parts.append(f'<a href="{nav_map["Blog"]}">Blog</a>')
    if "Video" in nav_map:
        parts.append(f'<a href="{nav_map["Video"]}">Video</a>')
    parts.append(f'<a href="{vibe_href}">Vibe Coding</a>')
    parts.append(f'<a href="{about_href}">About Me</a>')
    return ''.join(parts)


def page_shell(title: str, body_html: str, current_html_rel: Path):
    css_base = os.path.relpath(Path('assets/style.css'), current_html_rel.parent).replace('\\', '/')
    css_href = f"{css_base}?v={CSS_VERSION}"
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <meta name=\"theme-color\" content=\"#eef1f7\" />
    <title>{html.escape(title)} | CryptoSherry</title>
    <link rel=\"stylesheet\" href=\"{css_href}\" />
  </head>
  <body>
    <a class=\"skip-link\" href=\"#main-content\">Skip to content</a>
    <header class=\"top\">
      <div class=\"container top-inner\">
        <a class=\"brand\" href=\"{os.path.relpath(Path('index.html'), current_html_rel.parent).replace('\\', '/')}\">CryptoSherry</a>
        <div class=\"top-actions\">
          <nav class=\"nav\">{nav_html(current_html_rel)}</nav>
          <button class=\"lang-toggle\" type=\"button\" aria-label=\"Toggle language\" data-lang-toggle>EN / 中文</button>
        </div>
      </div>
    </header>
    <main id=\"main-content\" class=\"container\">
      <article>
        {body_html}
      </article>
    </main>
    <script>
      (function () {{
        const key = "cryptosherry-lang";
        const btn = document.querySelector("[data-lang-toggle]");
        const applyLang = (lang) => {{
          document.documentElement.setAttribute("lang", lang === "zh" ? "zh-CN" : "en");
          document.body.dataset.lang = lang;
          document.querySelectorAll("[data-i18n-zh]").forEach((el) => {{
            const en = el.getAttribute("data-i18n-en");
            const zh = el.getAttribute("data-i18n-zh");
            el.textContent = lang === "zh" ? zh : en;
          }});
          if (btn) {{
            btn.textContent = lang === "zh" ? "中文 / EN" : "EN / 中文";
          }}
        }};
        let current = localStorage.getItem(key) || "en";
        applyLang(current);
        if (btn) {{
          btn.addEventListener("click", () => {{
            current = current === "en" ? "zh" : "en";
            localStorage.setItem(key, current);
            applyLang(current);
          }});
        }}
      }})();
    </script>
  </body>
</html>
"""


def i18n_text(en_text: str, zh_text: str) -> str:
    en = html.escape(en_text)
    zh = html.escape(zh_text)
    return f'<span data-i18n-en="{en}" data-i18n-zh="{zh}">{en}</span>'


def replace_first_paragraphs(html_body: str, replacements: list[str]) -> str:
    out = html_body
    for repl in replacements:
        out = re.sub(r'<p>.*?</p>', repl, out, count=1, flags=re.S)
    return out


def generate_linkedin_description(title: str) -> str:
    t = title.lower()
    if "w3ai" in t and "agent" in t:
        return "Explains how W3AI supports the rapid growth of AI agents with practical infrastructure and onchain coordination."
    if "federated learning" in t and "w3ai" in t:
        return "Outlines how decentralized federated learning can run on W3AI with privacy-preserving collaboration and distributed model updates."
    if "decentralized ai inference" in t and "w3ai" in t:
        return "Explores how W3AI can lead decentralized AI inference through scalable onchain coordination and distributed compute."
    if "depin" in t and "smollm" in t:
        return "Breaks down how AIOZ DePIN nodes can power SmolLM workloads with distributed compute and efficient delivery."
    return "A practical analysis on AI and Web3 building trends with real-world product and infrastructure takeaways."


def linkedin_post_block(title: str, url: str) -> str:
    desc = generate_linkedin_description(title)
    return (
        f'<h3>{html.escape(title)}</h3>\n'
        f'<p>{html.escape(desc)}</p>\n'
        f'<p><a href="{html.escape(url)}" target="_blank" rel="noopener">Read More</a></p>\n'
    )

def dedupe_blog_latest_posts(html_body: str, duplicate_titles: list[str]) -> str:
    dup_set = {t.strip().lower() for t in duplicate_titles if t.strip()}
    post_block_re = re.compile(
        r'(?s)<h3>(?P<title>.*?)</h3>\s*<p>.*?</p>\s*<p><a .*?>Read [Mm]ore</a></p>'
    )

    seen_count: dict[str, int] = {}

    def _replace(match: re.Match[str]) -> str:
        title = re.sub(r'<.*?>', '', html.unescape(match.group('title'))).strip().lower()
        # Keep the first occurrence (newly injected); remove later duplicates.
        if title in dup_set:
            seen_count[title] = seen_count.get(title, 0) + 1
            if seen_count[title] >= 2:
                return ''
        return match.group(0)

    return post_block_re.sub(_replace, html_body)

def remove_blog_posts_by_title(html_body: str, titles_to_remove: list[str]) -> str:
    remove_set = {t.strip().lower() for t in titles_to_remove if t.strip()}
    post_block_re = re.compile(
        r'(?s)<h3>(?P<title>.*?)</h3>\s*<p>.*?</p>\s*<p><a .*?>Read [Mm]ore</a></p>'
    )

    def _replace(match: re.Match[str]) -> str:
        title = re.sub(r'<.*?>', '', html.unescape(match.group('title'))).strip().lower()
        if title in remove_set:
            return ''
        return match.group(0)

    return post_block_re.sub(_replace, html_body)

def keep_external_blog_posts_only(html_body: str) -> str:
    post_block_re = re.compile(
        r'(?s)<h3>(?P<title>.*?)</h3>\s*<p>.*?</p>\s*<p><a href="(?P<href>.*?)".*?>Read [Mm]ore</a></p>'
    )

    def _replace(match: re.Match[str]) -> str:
        href = html.unescape(match.group('href')).strip().lower()
        if href.startswith('http://') or href.startswith('https://'):
            return match.group(0)
        return ''

    return post_block_re.sub(_replace, html_body)

def sort_blog_latest_posts(html_body: str) -> str:
    # Newest -> oldest for recently added external posts.
    # For all other posts, keep original relative order.
    # User-provided publish dates (newest -> oldest):
    # 2025-01-16: How W3AI Will Support the AI Agents Boom
    # 2024-09-20: How Decentralized Federated Learning Will Work on W3AI
    # 2024-09-12: How W3AI will Spearhead Decentralized AI Inference
    # 2024-09-07: The Future of Generative AI: How W3AI Fits In
    # 2024-08-11: How AIOZ DePIN Nodes Power SmolLM
    recent_order = {
        "how w3ai support ai agents boom": 0,
        "how w3ai will support the ai agents boom": 0,
        "how decentralized federated learning will work on w3ai": 1,
        "how w3ai will spearhead decentralized ai inference": 2,
        "the future of generative ai: how w3ai fits in": 3,
        "how aioz depin nodes power smollm": 4,
    }

    marker = re.search(
        r'(?s)(<h2>.*?Latest Posts.*?</h2>)(?P<section>.*?)(<h3><a href="[^"]*publications[^"]*">Article Publications and Reposting</a></h3>)',
        html_body,
        flags=re.I,
    )
    if not marker:
        return html_body

    header = marker.group(1)
    section = marker.group("section")
    footer_anchor = marker.group(3)

    block_re = re.compile(
        r'(?s)(<h3>(?P<title>.*?)</h3>\s*<p>.*?</p>\s*<p><a href=".*?">Read [Mm]ore</a></p>)'
    )
    blocks = []
    for i, m in enumerate(block_re.finditer(section)):
        title_raw = re.sub(r"<.*?>", "", html.unescape(m.group("title"))).strip().lower()
        blocks.append((i, title_raw, m.group(1)))
    if not blocks:
        return html_body

    sorted_blocks = sorted(
        blocks,
        key=lambda x: (recent_order.get(x[1], 10_000), x[0]),
    )
    new_section = "\n".join(b[2] for b in sorted_blocks) + "\n\n"

    replacement = header + new_section + footer_anchor
    return html_body[: marker.start()] + replacement + html_body[marker.end() :]


# Build converted markdown pages
podcast_md = next((m for m in md_files if m.name == PODCAST_PAGE_KEY), None)
for md in md_files:
    rel_html = md_to_html_rel[md.resolve()]
    out_path = OUT / rel_html
    out_path.parent.mkdir(parents=True, exist_ok=True)
    md_text = md.read_text(encoding='utf-8', errors='ignore')
    body = md_to_html(md_text, md, rel_html)
    if md.name == VIDEO_PAGE_KEY and podcast_md is not None:
        podcast_text = podcast_md.read_text(encoding='utf-8', errors='ignore')
        podcast_body = md_to_html(podcast_text, podcast_md, rel_html)
        # Remove top H1 from appended content to avoid duplicated page titles.
        podcast_body = re.sub(r'^<h1>.*?</h1>\s*', '', podcast_body, count=1, flags=re.S)
        body = body + '\n<hr />\n<h2>Podcast Highlights</h2>\n' + podcast_body
    if md.name == BLOG_INDEX_KEY:
        body = re.sub(r'^<h1>.*?</h1>', f'<h1>{i18n_text("CryptoSherry\'s Blog", "CryptoSherry 的博客")}</h1>', body, count=1, flags=re.S)
        body = replace_first_paragraphs(
            body,
            [f'<p>{i18n_text("Writing on crypto, AI, and onchain product growth, from trend notes to deeper analysis.", "聚焦加密、AI 与链上增长，从趋势速记到深度分析。")}</p>'],
        )
        body = re.sub(r'<h2>.*?Latest Posts.*?</h2>', f'<h2>{i18n_text("Latest Posts", "最新文章")}</h2>', body, count=1, flags=re.S)
        linkedin_blocks = (
            linkedin_post_block(
                "How W3AI Support AI Agents Boom",
                "https://www.linkedin.com/pulse/how-w3ai-support-ai-agents-boom-sherry-wu-d39ac",
            )
            + linkedin_post_block(
                "How AIOZ DePIN Nodes Power SmolLM",
                "https://www.linkedin.com/pulse/how-aioz-depin-nodes-power-smollm-sherry-wu-wrncc",
            )
            + linkedin_post_block(
                "How Decentralized Federated Learning Will Work on W3AI",
                "https://www.linkedin.com/pulse/how-decentralized-federated-learning-work-w3ai-sherry-wu-npcpc",
            )
            + linkedin_post_block(
                "How W3AI will Spearhead Decentralized AI Inference",
                "https://www.linkedin.com/pulse/how-w3ai-spearhead-decentralized-ai-inference-sherry-wu-kczec",
            )
        )
        body = re.sub(
            r'(<h2>.*?</h2>)',
            r'\1\n' + linkedin_blocks,
            body,
            count=1,
            flags=re.S,
        )
        body = sort_blog_latest_posts(body)
        body = dedupe_blog_latest_posts(
            body,
            [
                "How W3AI Support AI Agents Boom",
                "How AIOZ DePIN Nodes Power SmolLM",
            ],
        )
        body = remove_blog_posts_by_title(
            body,
            [
                "Why AI should be Integrated with DePIN Solutions",
                "DePIN+AI: Crypto's Answer to Centralized Monopolies",
            ],
        )
        body = re.sub(
            r'(<h3>The Future of Generative AI: How W3AI Fits In</h3>\s*<p>.*?</p>\s*<p><a href=")[^"]+(".*?>Read More</a></p>)',
            r'\1https://www.linkedin.com/pulse/future-generative-ai-how-w3ai-fits-sherry-wu-lwhhc\2',
            body,
            count=1,
            flags=re.S,
        )
    if md.name == VIDEO_PAGE_KEY:
        body = re.sub(r'^<h1>.*?</h1>', f'<h1>{i18n_text("Sherry\'s CryptoSphere", "Sherry 的 CryptoSphere")}</h1>', body, count=1, flags=re.S)
        body = re.sub(
            r'(^<h1>.*?</h1>)\s*<p>.*?</p>',
            (
                r'\1'
                + f'<p>{i18n_text("Short videos and explainers on crypto, AI and blockchain, covering market narratives, onchain mechanics, and builder takeaways.", "用短视频解读加密, AI与区块链，覆盖市场叙事、链上机制与 builder 视角。")}</p>'
                + f'<p>{i18n_text("From quick updates to deeper dives, each episode is designed to be practical and easy to follow.", "从快速更新到深度拆解，内容更实用也更易跟上。")}</p>'
            ),
            body,
            count=1,
            flags=re.S,
        )

    title = md.stem
    m = re.search(r'^#\s+(.+)$', md_text, re.M)
    if m:
        title = normalize_heading_text(m.group(1).strip())
    title = PAGE_TITLE_OVERRIDE.get(title, title)

    out_path.write_text(page_shell(title, body, rel_html), encoding='utf-8')

# Build Home page with only major sections + about page
ICON_MAP = {
    "Blog": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4l10-10-4-4L4 16v4z"/><path d="M13 7l4 4"/></svg>',
    "Publications": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h10a3 3 0 0 1 3 3v13H8a3 3 0 0 0-3 3V4z"/><path d="M8 4v16"/><path d="M11 8h5"/><path d="M11 12h5"/></svg>',
    "Video": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="14" height="14" rx="2"/><path d="M10 9l4 3-4 3z"/><path d="M17 10l4-2v8l-4-2z"/></svg>',
    "Podcast": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12a7 7 0 0 1 14 0"/><path d="M8 12a4 4 0 0 1 8 0"/><path d="M12 13v7"/><circle cx="12" cy="11" r="1.6"/></svg>',
    "About CryptSherry": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 20c1.8-3.5 5-5 8-5s6.2 1.5 8 5"/></svg>',
}
DESC_FALLBACK = {
    "Blog": "Latest writing on crypto, AI, and builder perspectives.",
    "Publications": "Selected reposts and external publications across crypto media platforms.",
    "Video": "Videos on crypto trends, from explainers to deeper dives.",
    "Podcast": "Live sessions and podcast conversations around ecosystem growth and strategy.",
    "About CryptSherry": "Background, experience, and focus areas across Web3 and AI.",
}


def extract_intro_from_md(md_path: Path) -> str:
    lines = md_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if s.startswith('#'):
            continue
        if s.startswith('!['):
            continue
        if re.match(r'^\[[^\]]+\]\([^)]+\)$', s):
            continue
        if re.match(r'^[-*+]\s+', s):
            continue
        if re.match(r'^\d+[\.)]\s+', s):
            continue
        if re.search(r'(?i)\bpublish(?:ed)?\s+on\b', s):
            continue
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', s)
        s = normalize_heading_text(s)
        if s:
            return s[:165] + ('...' if len(s) > 165 else '')
    return ''


def item_slug(title: str) -> str:
    return slugify(title)


def daily_ai_href(item: dict) -> str:
    return f"daily/{item['date']}/ai/{item_slug(item['title'])}/index.html"


def daily_market_href(item: dict) -> str:
    return f"daily/{item['date']}/market/{item_slug(item['title'])}/index.html"

def market_keywords(item: dict) -> list[str]:
    title = (item.get("title") or "")
    summary = (item.get("summary") or "")
    source_platform = (item.get("source_platform") or "").strip().lower()
    text = f"{title} {summary}"
    lower_text = text.lower()

    stop = {
        "daily", "march", "april", "may", "june", "july", "august", "september",
        "october", "november", "december", "would", "have", "from", "with", "this",
        "that", "into", "instead", "credit", "card", "discussion", "general", "crypto",
        "reddit", "today", "news", "update", "breaking", "report", "says", "say",
        "over", "under", "after", "before", "against", "about", "their", "there",
        "they", "them", "been", "being", "while", "where", "when", "what", "which",
        "accuses", "signs", "bill", "would", "could", "should", "will", "via",
    }
    domain_priority = [
        "bitcoin", "btc", "ethereum", "eth", "solana", "defi", "rwa", "stablecoin",
        "etf", "layer2", "l2", "depin", "ai", "agent", "mcp",
    ]
    domain_alias = {
        "bitcoins": "bitcoin",
        "eth": "ethereum",
        "btc": "bitcoin",
        "layer-2": "layer2",
        "l2s": "layer2",
        "stablecoins": "stablecoin",
    }

    def normalize_kw(tok: str) -> str:
        t = tok.strip().lower().lstrip("#$")
        t = re.sub(r"[^a-z0-9+ ]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            return ""
        if t.replace(" ", "").isdigit():
            return ""
        compact = t.replace(" ", "")
        if len(compact) < 2 or len(compact) > 24:
            return ""
        return domain_alias.get(t, t)

    seen: set[str] = set()
    out: list[str] = []

    def add_kw(raw: str) -> None:
        if len(out) >= 3:
            return
        kw = normalize_kw(raw)
        if not kw or kw in stop or kw in seen:
            return
        seen.add(kw)
        out.append(kw)

    # 0) High-priority extraction requested by user.
    # 0.1 One person name only: choose the most repeated proper-name phrase.
    person_name_stop = {
        "daily crypto", "daily general", "crypto clarity", "credit card",
        "stop cop", "bitcoin", "ethereum", "cryptocurrency", "reddit",
    }
    name_counts: dict[str, int] = {}
    name_order: list[str] = []
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", f"{title} {summary}"):
        raw_name = m.group(1).strip()
        name = re.sub(r"\s+", " ", raw_name).lower()
        if name in person_name_stop:
            continue
        if len(name) > 26:
            continue
        if name not in name_counts:
            name_counts[name] = 0
            name_order.append(name)
        name_counts[name] += 1
    if name_counts:
        best_name = sorted(name_order, key=lambda n: (-name_counts[n], name_order.index(n)))[0]
        add_kw(best_name)

    # 0.2 Prefer numeric signals from title.
    for raw in re.findall(r"\$?\d+(?:[.,]\d+)?(?:[kmbKMB%])?", title):
        add_kw(raw)
        if len(out) >= 3:
            break

    # 0.3 Prefer verbs from title.
    verb_lexicon = {
        "accuses", "signs", "drops", "torches", "files", "approves", "rejects",
        "launches", "builds", "buys", "sells", "surges", "falls", "rallies",
        "jumps", "plunges", "blocks", "bans", "adopts", "invests", "powers",
        "supports", "guides", "wins", "loses", "moves", "rotates", "prevents",
    }
    title_tokens = [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", title)]
    for tok in title_tokens:
        if tok in verb_lexicon or tok.endswith("ed") or tok.endswith("ing"):
            add_kw(tok)
            if len(out) >= 3:
                break

    # 1) Explicit symbols/hashtags first (useful for X/news).
    for raw in re.findall(r"[$#][A-Za-z0-9_]{2,}", text):
        add_kw(raw)

    # 2) Domain-priority entities from title/summary.
    for kw in domain_priority:
        if len(out) >= 3:
            break
        if re.search(rf"\b{re.escape(kw)}\b", lower_text):
            add_kw(kw)

    # 3) Source-aware hint as fallback signal.
    if len(out) < 3:
        if source_platform == "reddit":
            add_kw("reddit")
        elif source_platform == "x":
            add_kw("x")
        elif source_platform:
            add_kw(source_platform)

    # 4) Tags next.
    if len(out) < 3:
        for tag in (item.get("tags") or []):
            add_kw(str(tag))
            if len(out) >= 3:
                break

    # 5) General token fill from title first, then summary.
    if len(out) < 3:
        for raw in re.findall(r"[A-Za-z0-9+#]{2,}", title):
            add_kw(raw)
            if len(out) >= 3:
                break
    if len(out) < 3:
        for raw in re.findall(r"[A-Za-z0-9+#]{2,}", summary):
            add_kw(raw)
            if len(out) >= 3:
                break

    # Final hard fallback.
    if not out:
        out = [normalize_kw(str(t)) for t in (item.get("tags") or []) if normalize_kw(str(t))]
    if not out:
        out = ["market"]
    return out[:3]

def market_summary_html(item: dict) -> str:
    title = (item.get("title") or "").strip()
    summary = (item.get("summary") or "").strip()
    if not summary:
        return ""
    normalize = lambda s: re.sub(r"\s+", " ", s).strip(" .,!?:;").lower()
    if normalize(title) == normalize(summary):
        return ""
    return f'<p>{i18n_text(summary, item.get("summary_zh", summary))}</p>'


def smart_truncate_ui(text: str, max_chars: int = 140) -> str:
    raw = re.sub(r"\s+", " ", (text or "").strip())
    if len(raw) <= max_chars:
        return raw
    cut = raw[:max_chars]
    boundary = cut.rfind(" ")
    if boundary >= int(max_chars * 0.6):
        cut = cut[:boundary]
    return cut.rstrip(" ,.;:!?") + "..."


def ai_desc_html(item: dict) -> str:
    en = smart_truncate_ui(str(item.get("description") or ""))
    zh = smart_truncate_ui(str(item.get("description_zh") or en), 90)
    return i18n_text(en, zh)

def source_label(name: str) -> str:
    raw = (name or "").strip().lower()
    if raw == "github":
        return "GitHub"
    if raw == "reddit":
        return "Reddit"
    if raw == "x":
        return "X"
    return name or "Source"


section_items = []
for label, target in nav_items:
    if label in {"Publications", "Podcast"}:
        continue
    href = md_to_html_rel[target.resolve()]
    icon = ICON_MAP.get(label, "")
    desc = extract_intro_from_md(target) or DESC_FALLBACK.get(label, "")
    if label == "Publications":
        desc = DESC_FALLBACK.get(label, desc)
    section_items.append(f'''
      <a class="section-card" href="{href.as_posix()}">
        <div class="section-head">
          <span class="section-icon" aria-hidden="true">{icon}</span>
          <h3 class="section-title">{html.escape(label)}</h3>
        </div>
        <p class="section-desc">{html.escape(desc)}</p>
      </a>
    ''')

section_items.append('''
  <a class="section-card" href="video-coding.html">
    <div class="section-head">
      <span class="section-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 8l-4 4 4 4"/><path d="M16 8l4 4-4 4"/><path d="M14 4l-4 16"/></svg></span>
      <h3 class="section-title">Vibe Coding</h3>
    </div>
    <p class="section-desc">Hands-on coding for practical AI and Web3 builder workflows.</p>
  </a>
''')
section_items.append(f'''
  <a class="section-card" href="resume.html">
    <div class="section-head">
      <span class="section-icon" aria-hidden="true">{ICON_MAP["About CryptSherry"]}</span>
      <h3 class="section-title">About Me</h3>
    </div>
    <p class="section-desc">{html.escape(DESC_FALLBACK["About CryptSherry"])}</p>
  </a>
''')

latest_ai = DAILY_AI[0] if DAILY_AI else {
    "id": "ai-fallback",
    "date": datetime.now(ET).date().isoformat(),
    "generated_at_utc": datetime.utcnow().isoformat() + "Z",
    "source_platform": "github",
    "source_url": "https://github.com",
    "title": "No AI recommendation available",
    "description": "Data pipeline fallback item.",
    "description_zh": "当前暂无可用推荐，展示兜底项。",
    "summary": "No qualified candidate in the latest run.",
    "summary_zh": "本次抓取未命中合格候选。",
    "tags": ["fallback"],
    "category": "Tooling",
    "updated_at": "",
    "score_raw": 0,
}
ai_history = DAILY_AI_HISTORY
latest_market_date = DAILY_MARKET[0]["date"] if DAILY_MARKET else latest_ai["date"]
today_market = [item for item in DAILY_MARKET if item.get("date") == latest_market_date][:3]

def ai_history_item_html(item: dict) -> str:
    tags = item.get("tags") or []
    tags_html = " / ".join(html.escape(str(tag)) for tag in tags) if tags else "-"
    return f'''
      <article class="feed-item">
        <h3>{html.escape(item["title"])}</h3>
        <p>{ai_desc_html(item)}</p>
        <div class="feed-meta">
          <span class="chip">{html.escape(item.get("date", "-"))} ET</span>
          <span class="chip">{html.escape(item.get("category", "-"))}</span>
          <span class="chip">score {item.get("score_raw", 0)}</span>
        </div>
        <p>{i18n_text(item.get("summary", ""), item.get("summary_zh", item.get("summary", "")))}</p>
        <p class="mini-note">Source: <a href="{html.escape(item.get("source_url", "https://github.com"))}" target="_blank" rel="noopener">{html.escape(source_label(item.get("source_platform", "GitHub")))}</a></p>
        <p class="mini-note">Tags: {tags_html}</p>
      </article>
    '''

ai_history_html = "".join(
    ai_history_item_html(item)
    for item in ai_history
)
if not ai_history_html:
    ai_history_html = '<p class="mini-note">No history yet. Check back tomorrow after 09:00 ET.</p>'

market_items_html = "".join(
    f'''
      <li>
        <article class="market-card">
          <strong>{i18n_text(item["title"], item["title_zh"])}</strong>
          {market_summary_html(item)}
          <p><strong>{i18n_text("Keywords", "关键词")}:</strong> {html.escape(", ".join(market_keywords(item)))}</p>
          <div class="market-meta-line">
            <span class="chip">{html.escape(item["date"])} ET</span>
            <span class="chip">{html.escape(item["source_platform"])}</span>
            <span class="chip">engagement {item["engagement"]}</span>
          </div>
          <p class="market-source"><strong>Source:</strong> <a href="{html.escape(item["source_url"])}" target="_blank" rel="noopener">{html.escape(item["source_url"])}</a></p>
          <p><strong>Tags:</strong> {' / '.join(html.escape(tag) for tag in item["tags"])}</p>
        </article>
      </li>
    '''
    for item in today_market
)

home_body = f"""
<section class="hero">
  <div class="hero-grid">
    <div>
      <h1>{i18n_text("CryptoSherry's Corner", "CryptoSherry 的角落")}</h1>
      <p>{i18n_text("Insights for Web3 and AI builders, from Bitcoin and EthDev to DeFi, stablecoins, RWAs, and practical AI agent workflows.", "面向 Web3 与 AI builder 的洞察，覆盖比特币、EthDev、DeFi、稳定币、RWA 与实用的 AI agent 工作流。")}</p>
      <p>{i18n_text("Follow what’s emerging, what’s shipping, and how teams are building onchain.", "追踪正在出现的新趋势、正在落地的产品，以及团队如何构建链上应用。")}</p>
      <div class="hero-actions">
        <a class="social-btn calendly-btn" href="https://calendly.com/imsherry/new-meeting" target="_blank" rel="noopener" aria-label="Calendly">
          <svg class="calendly-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" fill="#ffffff"/>
            <path d="M12 5.4a6.6 6.6 0 1 0 4.7 11.2l-1.7-1.8A4 4 0 1 1 12 8h6.6v2.6H12a1.4 1.4 0 1 0 0 2.8H22V5.4H12z" fill="#006bff"/>
          </svg>
        </a>
      </div>
    </div>
    <div class="hero-avatar-wrap">
      <img class="hero-avatar" src="https://media.licdn.com/dms/image/v2/D5603AQHLXuPzOtxHAA/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1718284291289?e=2147483647&amp;v=beta&amp;t=VX-fuq-CffaPs3mR0jaayDASUICQWptNg4EpfcQLNP0" alt="CryptoSherry portrait" width="200" height="200" loading="eager" fetchpriority="high" />
    </div>
  </div>
</section>
<section class="feed-layout">
  <section class="feed-board">
    <h2>{i18n_text("Today's Picks", "今日精选")}</h2>
    <div class="feed-grid">
      <section class="feed-card">
        <p class="feed-label">{i18n_text("Daily AI Pick", "每日 AI 精选")}</p>
        <h3 class="feed-title">{html.escape(latest_ai["title"])}</h3>
        <p>{ai_desc_html(latest_ai)}</p>
        <div class="feed-meta">
          <span class="chip">{html.escape(latest_ai["category"])}</span>
          <span class="chip">{html.escape(latest_ai["date"])} ET</span>
          <span class="chip">score {latest_ai["score_raw"]}</span>
        </div>
        <p class="mini-note">Source: <a href="{html.escape(latest_ai["source_url"])}" target="_blank" rel="noopener">GitHub</a></p>
        <h3>{i18n_text("Daily AI History (Last 7 Days)", "每日 AI 历史记录（近 7 天）")}</h3>
        <div class="ai-history-scroll">{ai_history_html}</div>
      </section>
      <section class="feed-card">
        <p class="feed-label">{i18n_text("Daily Market Top 3", "每日市场 Top 3")}</p>
        <ul class="market-list">{market_items_html}</ul>
        <p class="disclaimer">{i18n_text("Not investment advice. Please verify external links before taking action.", "非投资建议。请在采取行动前核实外部链接信息。")}</p>
      </section>
    </div>
  </section>
</section>
<section class="section-links">
  <div class="section-cards">{''.join(section_items)}</div>
</section>
"""
(OUT / 'index.html').write_text(page_shell('Home', home_body, Path('index.html')), encoding='utf-8')

daily_redirect_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="refresh" content="0; url=index.html" />
    <title>Redirecting | CryptoSherry</title>
    <script>window.location.replace("index.html");</script>
  </head>
  <body>
    <p>Daily Picks moved to Home. Redirecting...</p>
    <p><a href="index.html">Go to Home</a></p>
  </body>
</html>
"""
(OUT / "daily.html").write_text(daily_redirect_html, encoding="utf-8")

skill_links = [
    ("OpenAI Skills Catalog", "https://github.com/openai/skills", "Curated and system-ready skill packs.", ["skills", "catalog"]),
    ("UI/UX Pro Max Skill", "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill", "UI/UX design intelligence and implementation references.", ["ui", "ux", "design"]),
    ("Claude Skills Pack", "https://github.com/alirezarezvani/claude-skills", "Reusable Claude-oriented skill modules.", ["agent", "skills"]),
    ("Anthropic Skills Library", "https://github.com/anthropics/skills", "Anthropic-maintained skills examples and structure.", ["anthropic", "library"]),
    ("AI Agents Skills Collection", "https://github.com/hoodini/ai-agents-skills", "Agent-focused skill collection with practical patterns.", ["ai-agent", "workflow"]),
    ("AI Agent Skills Repository", "https://github.com/skillcreatorai/Ai-Agent-Skills", "Community repository for agent capabilities.", ["agent", "tools"]),
    ("AI Research Skills Library", "https://github.com/Orchestra-Research/AI-Research-SKILLs", "Research-oriented skill packs and templates.", ["research", "skills"]),
    ("Letta Skills", "https://github.com/letta-ai/skills", "Memory-driven agent skills and examples.", ["letta", "memory"]),
    ("Prompt Engineering Guide", "https://github.com/dair-ai/Prompt-Engineering-Guide", "Prompt methods and practical usage patterns.", ["prompt", "guide"]),
    ("Model Context Protocol (MCP) Servers", "https://github.com/modelcontextprotocol/servers", "Server implementations for MCP integrations.", ["mcp", "servers"]),
]

video_links = [
    ("Agentic AI Engineering: Complete 4-Hour Workshop", "https://www.youtube.com/watch?v=LSk5KaEGVk4"),
    ("LangChain Full Crash Course - AI Agents in Python", "https://www.youtube.com/watch?v=J7j5tCB_y4w"),
    ("End-to-end AI Agent Project with LangChain | Full Walkthrough", "https://www.youtube.com/watch?v=AO6WbXTeDow"),
    ("LangGraph Complete Course for Beginners", "https://www.youtube.com/watch?v=jGg_1h0qzaM"),
    ("Agentic AI With Langgraph And MCP Crash Course - Part 1", "https://www.youtube.com/watch?v=dIb-DujRNEo"),
    ("Build AI Agents in 10 Minutes with CrewAI", "https://www.youtube.com/watch?v=lTwDAHVznlU"),
    ("CrewAI Tutorial | Agentic AI Tutorial", "https://www.youtube.com/watch?v=G42J2MSKyc8"),
    ("Agentic AI With Autogen Crash Course", "https://www.youtube.com/watch?v=yDpV_jgO93c"),
    ("Deep Dive into LLMs like ChatGPT (Karpathy)", "https://www.youtube.com/watch?v=7xTGNNLPyMI"),
    ("How I use LLMs (Karpathy)", "https://www.youtube.com/watch?v=EWvNQjAaOHw"),
]

skills_cards_html = "".join(
    f"""
    <article class="vc-card">
      <h3>{html.escape(title)}</h3>
      <p>{html.escape(desc)}</p>
      <div class="chip-row">{''.join(f'<span class="chip">{html.escape(tag)}</span>' for tag in tags)}</div>
      <div class="btn-row"><a class="btn-chip" href="{html.escape(url)}" target="_blank" rel="noopener">View on GitHub</a></div>
    </article>
    """
    for title, url, desc, tags in skill_links
)

video_cards_html = "".join(
    f"""
    <a class="vc-video" href="{html.escape(url)}" target="_blank" rel="noopener">
      <img src="https://i.ytimg.com/vi/{html.escape(extract_youtube_id(url))}/hqdefault.jpg" alt="{html.escape(title)} thumbnail" loading="lazy" width="480" height="360" />
      <div class="vc-video-body">
        <h3>{html.escape(title)}</h3>
        <p class="mini-note">Watch on YouTube</p>
      </div>
    </a>
    """
    for title, url in video_links
)

video_coding_body = f"""
<h1>Vibe Coding</h1>
<p>Featured AI skills and tutorial videos for builders.</p>
<p class="mini-note">A curated selection of GitHub skills and YouTube tutorials, refreshed regularly.</p>

<section class="feed-board">
  <h2>Featured AI Skills</h2>
  <p>Reusable skill packs, agent tooling, and workflow references.</p>
  <div class="vc-grid">{skills_cards_html}</div>
</section>

<section class="feed-board">
  <h2>Featured AI Tutorial Video</h2>
  <p>Practical walkthroughs for agent workflows, tool integration, and LLM fundamentals.</p>
  <div class="vc-video-grid">{video_cards_html}</div>
</section>

<section class="feed-board">
  <h2>Want more featured picks?</h2>
  <p>Explore Daily AI and Daily Market picks on the homepage.</p>
  <div class="btn-row">
    <a class="btn-chip" href="index.html">Back to Home</a>
  </div>
</section>
"""
(OUT / "video-coding.html").write_text(page_shell("Video Coding", video_coding_body, Path("video-coding.html")), encoding="utf-8")

for item in DAILY_AI:
    rel = Path(daily_ai_href(item))
    detail_body = f"""
<h1>{html.escape(item["title"])}</h1>
<p>{i18n_text(item["description"], item["description_zh"])}</p>
<div class="feed-meta">
  <span class="chip">{html.escape(item["date"])} ET</span>
  <span class="chip">{html.escape(item["category"])}</span>
  <span class="chip">score {item["score_raw"]}</span>
</div>
<p>{i18n_text(item["summary"], item["summary_zh"])}</p>
<p><strong>Source:</strong> <a href="{html.escape(item["source_url"])}" target="_blank" rel="noopener">{html.escape(item["source_platform"])}</a></p>
<p><strong>Tags:</strong> {' / '.join(html.escape(tag) for tag in item["tags"])}</p>
<p class="mini-note">content_time: {html.escape(item["updated_at"])} • generated_at_utc: {html.escape(item["generated_at_utc"])}</p>
"""
    out_path = OUT / rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page_shell(item["title"], detail_body, rel), encoding="utf-8")

# Build resume page
resume_body = """
<h1>Sherry Wu</h1>
<p>Web3 and AI growth lead with 4+ years of go-to-market execution across content strategy, ecosystem partnerships, media visibility, and community activation.</p>

<h2>Experience</h2>
<div class=\"exp\">
  <div class=\"exp-head\"><strong>Head of Growth - AIOZ Network</strong><span class=\"time\">2024 - Present</span></div>
  <ul>
    <li>Own brand narrative and content strategy for product milestones and listing communications.</li>
    <li>Lead growth execution on X to improve qualified reach and engagement.</li>
    <li>Secure media visibility across CoinDesk, Cointelegraph, and Blockworks.</li>
    <li>Drive ecosystem partnerships with Avalanche, Aptos, and Neo.</li>
  </ul>
</div>
<div class=\"exp\">
  <div class=\"exp-head\"><strong>CMO - Aboard Exchange</strong><span class=\"time\">2023 - 2024</span></div>
  <ul>
    <li>Led exchange growth strategy and campaign design, resulting in 200K+ user growth.</li>
    <li>Executed campaigns with Arbitrum, zkSync, and Polygon zkEVM, driving 700M+ trading volume.</li>
  </ul>
</div>
<div class=\"exp\">
  <div class=\"exp-head\"><strong>Head of Operations - iPollo AI</strong><span class=\"time\">2022 - 2023</span></div>
  <ul>
    <li>Owned execution of iPollo Meta Girl Party at HK Web3 Festival.</li>
    <li>Delivered 1,000+ RSVPs with 10+ partners and 20+ sponsors.</li>
    <li>Built branding and influencer collaboration strategy for a NASDAQ-listed AI infrastructure company.</li>
  </ul>
</div>
<div class=\"exp\">
  <div class=\"exp-head\"><strong>Project Manager - ND Labs</strong><span class=\"time\">2021 - 2022</span></div>
  <ul>
    <li>Managed NFT and GameFi launches from planning through go-live and community activation.</li>
    <li>Co-developed ecosystem events with the Filecoin Foundation.</li>
  </ul>
</div>

<h2>Education & Certifications</h2>
<ul>
  <li>B.A. in Marketing, Shanghai Finance University</li>
  <li>CFA Charterholder</li>
  <li>Securities Qualification</li>
  <li>Private Equity Certificate</li>
</ul>
"""
(OUT / 'resume.html').write_text(page_shell('Resume', resume_body, Path('resume.html')), encoding='utf-8')

print(f'Generated {len(md_files)} markdown pages -> HTML in {OUT}')
print('Root markdown:', root_md.relative_to(SRC))
print('Home nav items:', len(nav_items))
