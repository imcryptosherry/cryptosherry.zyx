#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ETXML
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

AI_DAILY_PATH = DATA_DIR / "daily_ai.json"
AI_HISTORY_PATH = DATA_DIR / "daily_ai_history.json"
MARKET_DAILY_PATH = DATA_DIR / "daily_market.json"
MARKET_HISTORY_PATH = DATA_DIR / "daily_market_history.json"
OVERRIDE_PATH = DATA_DIR / "override.json"

ET = ZoneInfo("America/New_York")
GITHUB_API = "https://api.github.com"
BLACKLIST = ("airdrop", "guaranteed", "free money", "稳赚", "稳赚不赔")
AI_HARD_BLACKLIST = (
    "airdrop",
    "giveaway",
    "free money",
    "referral",
    "gambling",
    "casino",
    "nsfw",
    "adult",
    "seo",
)
AI_LOW_VALUE_PATTERNS = (
    "awesome",
    "collection",
    "resources",
    "prompt list",
    "prompt engineering list",
    "curated list",
    "template only",
)
AI_TOPIC_MAP = {
    "agents": ("agent", "ai-agent", "autogen", "crew", "langgraph"),
    "inference": ("inference", "serving", "vllm", "tgi"),
    "finetuning": ("finetuning", "lora", "dpo", "sft"),
    "alignment": ("alignment", "rlhf", "safety"),
    "eval": ("eval", "evaluation", "benchmark"),
    "reranking": ("reranking", "rerank"),
    "retrieval": ("rag", "retrieval"),
    "vector-db": ("qdrant", "pgvector", "chroma", "vector"),
    "llmops": ("llmops", "observability", "monitoring"),
    "guardrails": ("guardrails", "policy", "moderation"),
    "local-llm": ("ollama", "local llm"),
    "deployment": ("deployment", "docker", "kubernetes"),
    "app-framework": ("langchain", "framework", "sdk"),
    "memory": ("memory", "state"),
    "prompt-infra": ("prompt", "tool-calling", "mcp"),
}
AI_RELEVANCE_PRIORITY = (
    "agents",
    "inference",
    "finetuning",
    "alignment",
    "eval",
    "reranking",
    "retrieval",
    "vector-db",
    "llmops",
    "guardrails",
    "local-llm",
    "deployment",
    "app-framework",
    "memory",
    "prompt-infra",
)
MARKET_TITLE_BLACKLIST = ("daily crypto discussion", "daily general discussion")
MARKET_FINAL_BLACKLIST = (
    "daily crypto discussion",
    "daily general discussion",
    "megathread",
    "open thread",
    "weekend thread",
    "airdrop",
    "giveaway",
    "referral",
)
MARKET_MEME_PATTERNS = (
    "to the moon",
    "wen",
    "gm ",
    "shitpost",
    "meme",
    "lfg",
)
MARKET_RECAP_PATTERNS = (
    "market recap",
    "daily recap",
    "morning recap",
    "market wrap",
)
MARKET_PROMO_PATTERNS = (
    "join now",
    "sign up",
    "use my code",
    "follow for",
)
ASSET_TERMS = ("btc", "bitcoin", "eth", "ethereum", "sol", "solana", "bnb", "xrp")
NARRATIVE_TERMS = (
    "etf",
    "staking",
    "unlock",
    "exploit",
    "hack",
    "bridge",
    "regulation",
    "treasury",
    "flows",
    "layer2",
    "l2",
    "restaking",
    "stablecoin",
)
ACTION_TERMS = (
    "launch",
    "approve",
    "raise",
    "integrate",
    "unlock",
    "exploit",
    "announce",
    "ship",
    "acquire",
    "vote",
    "deploy",
    "file",
    "sign",
    "ban",
    "block",
)
SOURCE_QUALITY_BASE = {
    "x": 0.58,
    "reddit": 0.62,
    "coindesk": 0.9,
    "cointelegraph": 0.82,
    "the block": 0.88,
}
TOPICS = [
    "agent",
    "ai-agent",
    "llm",
    "llm-agent",
    "rag",
    "tool-calling",
    "autogen",
    "langchain",
    "mcp",
    "prompt-engineering",
    "workflow",
    "ai-tools",
    "generative-ai",
    "transformers",
    "ollama",
    "vllm",
    "finetuning",
    "lora",
    "dpo",
    "reranking",
    "pgvector",
    "qdrant",
    "chroma",
    "llmops",
    "guardrails",
]
REDDIT_WHITELIST = [
    "CryptoCurrency",
    "ethereum",
    "Bitcoin",
    "defi",
    "solana",
    "ethdev",
    "cryptotechnology",
    "blockchain",
]
CORE_KEYWORDS = ["btc", "eth", "l1", "l2", "defi", "depin"]
LOW_PRIORITY_KEYWORDS = ["ai x crypto", "ai", "crypto ai"]
ALL_KEYWORDS = CORE_KEYWORDS + LOW_PRIORITY_KEYWORDS
AI_DESC_MAX_CHARS = 140
NEWS_FALLBACK_SOURCES = [
    ("coindesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("cointelegraph", "https://cointelegraph.com/rss"),
    ("the block", "https://www.theblock.co/rss.xml"),
]


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_et() -> str:
    return datetime.now(ET).date().isoformat()


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def parse_date_ymd(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8", errors="ignore"))


def get_text(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="ignore")


def ensure_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except Exception:
        return []


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


class Translator:
    def __init__(self):
        self.cache: dict[str, str] = {}
        self.headers = {"User-Agent": "CryptoSherryDailyBot/1.0"}

    def to_zh(self, text: str) -> str:
        raw = (text or "").strip()
        if not raw:
            return raw
        if re.search(r"[\u4e00-\u9fff]", raw):
            return raw
        if raw in self.cache:
            return self.cache[raw]
        query = urllib.parse.urlencode(
            {
                "client": "gtx",
                "sl": "en",
                "tl": "zh-CN",
                "dt": "t",
                "q": raw,
            }
        )
        url = f"https://translate.googleapis.com/translate_a/single?{query}"
        try:
            payload = get_json(url, headers=self.headers)
            segments = payload[0] if isinstance(payload, list) and payload else []
            translated = "".join(seg[0] for seg in segments if isinstance(seg, list) and seg)
            out = translated.strip() or raw
        except Exception:
            out = raw
        self.cache[raw] = out
        time.sleep(0.05)
        return out


@dataclass
class RepoCandidate:
    full_name: str
    html_url: str
    stars: int
    pushed_at: str | None
    updated_at: str | None
    created_at: str | None
    description: str
    topics: list[str]


class GitHubCollector:
    def __init__(self, token: str | None):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "CryptoSherryDailyBot/1.0",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def fetch_trending_names(self, limit: int = 200) -> list[str]:
        html_text = get_text("https://github.com/trending?since=daily", headers=self.headers)
        pairs = re.findall(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', html_text)
        uniq: list[str] = []
        seen: set[str] = set()
        blocked_owners = {"sponsors", "topics", "collections", "trending", "features", "marketplace"}
        for repo in pairs:
            if repo.lower().endswith("/stargazers"):
                continue
            owner = repo.split("/", 1)[0].lower()
            if owner in blocked_owners:
                continue
            if repo in seen:
                continue
            seen.add(repo)
            uniq.append(repo)
            if len(uniq) >= limit:
                break
        return uniq

    def fetch_repo_detail(self, full_name: str) -> RepoCandidate | None:
        try:
            data = get_json(f"{GITHUB_API}/repos/{full_name}", headers=self.headers)
        except Exception:
            return None
        return RepoCandidate(
            full_name=data.get("full_name", full_name),
            html_url=data.get("html_url", f"https://github.com/{full_name}"),
            stars=int(data.get("stargazers_count", 0) or 0),
            pushed_at=data.get("pushed_at"),
            updated_at=data.get("updated_at"),
            created_at=data.get("created_at"),
            description=(data.get("description") or "").strip(),
            topics=list(data.get("topics") or []),
        )

    def fetch_topic_candidates(self, per_topic_max: int = 30) -> list[RepoCandidate]:
        results: list[RepoCandidate] = []
        seen: set[str] = set()
        for topic in TOPICS:
            page = 1
            collected = 0
            while collected < per_topic_max and page <= 3:
                q = urllib.parse.quote(f"topic:{topic}")
                url = (
                    f"{GITHUB_API}/search/repositories?q={q}"
                    f"&sort=updated&order=desc&per_page=30&page={page}"
                )
                try:
                    payload = get_json(url, headers=self.headers)
                except Exception:
                    break
                items = payload.get("items") or []
                if not items:
                    break
                for it in items:
                    full_name = it.get("full_name")
                    if not full_name or full_name in seen:
                        continue
                    seen.add(full_name)
                    results.append(
                        RepoCandidate(
                            full_name=full_name,
                            html_url=it.get("html_url", f"https://github.com/{full_name}"),
                            stars=int(it.get("stargazers_count", 0) or 0),
                            pushed_at=it.get("pushed_at"),
                            updated_at=it.get("updated_at"),
                            created_at=it.get("created_at"),
                            description=(it.get("description") or "").strip(),
                            topics=list(it.get("topics") or []),
                        )
                    )
                    collected += 1
                    if collected >= per_topic_max:
                        break
                page += 1
        return results

    def fetch_latest_release_time(self, full_name: str) -> str | None:
        try:
            data = get_json(f"{GITHUB_API}/repos/{full_name}/releases/latest", headers=self.headers)
            return data.get("published_at")
        except Exception:
            return None

    def fetch_readme_text(self, full_name: str) -> str:
        try:
            payload = get_json(f"{GITHUB_API}/repos/{full_name}/readme", headers=self.headers)
            download_url = payload.get("download_url")
            if not download_url:
                return ""
            return get_text(download_url, headers=self.headers)
        except Exception:
            return ""


def classify_repo(repo: RepoCandidate) -> str:
    tset = {t.lower() for t in repo.topics}
    text = f"{repo.full_name} {repo.description}".lower()
    if "agent" in text or "autogen" in tset or "llm-agent" in tset:
        return "Agent Framework"
    if "workflow" in tset or "rag" in tset:
        return "Skill / Workflow"
    if "sdk" in text or "cli" in text or "mcp" in tset or "tool-calling" in tset:
        return "Tooling"
    return "Model / Demo"


def soft_quality_pass(repo: RepoCandidate, readme: str) -> bool:
    text = f"{repo.description} {readme[:1200]}".lower()
    if any(word in text for word in BLACKLIST):
        return False
    if len(readme.strip()) < 260:
        return False
    if "usage" not in text and "install" not in text and "quickstart" not in text:
        return False
    return True


def smart_truncate(text: str, max_chars: int) -> str:
    raw = re.sub(r"\s+", " ", (text or "").strip())
    if len(raw) <= max_chars:
        return raw
    cut = raw[:max_chars]
    # Prefer word boundary if available.
    boundary = cut.rfind(" ")
    if boundary >= int(max_chars * 0.6):
        cut = cut[:boundary]
    return cut.rstrip(" ,.;:!?") + "..."


def auto_ai_description(repo: RepoCandidate) -> str:
    base = repo.full_name
    topics = [t for t in repo.topics if t]
    if topics:
        topic_part = ", ".join(topics[:3])
        return f"{base} focuses on {topic_part}, with practical workflows for builders."
    return f"{base} is a trending GitHub project with practical workflows for builders."


def relaxed_quality_pass(repo: RepoCandidate, readme: str) -> bool:
    text = f"{repo.full_name} {repo.description} {readme[:800]}".lower()
    if any(word in text for word in BLACKLIST):
        return False
    if repo.stars < 20:
        return False
    # Relaxed: allow concise README if topic/title clearly matches AI workflow.
    if len(readme.strip()) < 120:
        topic_text = " ".join(repo.topics).lower()
        if not any(k in f"{text} {topic_text}" for k in ["agent", "llm", "rag", "mcp", "transformer", "ai"]):
            return False
    return True


def ai_topic_categories(repo: RepoCandidate, readme: str) -> list[str]:
    text = f"{repo.full_name} {repo.description} {' '.join(repo.topics)} {readme[:1000]}".lower()
    cats: list[str] = []
    for cat, keys in AI_TOPIC_MAP.items():
        if any(re.search(rf"\b{re.escape(k)}\b", text) for k in keys):
            cats.append(cat)
    if not cats:
        cats.append("app-framework")
    return cats[:3]


def ai_quality_flags(repo: RepoCandidate, readme: str) -> list[str]:
    text = f"{repo.full_name} {repo.description} {' '.join(repo.topics)} {readme[:1200]}".lower()
    flags: list[str] = []
    if any(k in text for k in AI_HARD_BLACKLIST):
        flags.append("blacklist_match")
    if any(k in text for k in AI_LOW_VALUE_PATTERNS):
        flags.append("low_value_repo_type")
    if len(readme.strip()) < 120:
        flags.append("thin_readme")
    if repo.stars < 15:
        flags.append("low_momentum")
    if not any(k in text for k in ("agent", "llm", "ai", "transformer", "inference", "rag", "mcp")):
        flags.append("weak_ai_relevance")
    return sorted(set(flags))


def ai_freshness_tier(repo: RepoCandidate, content_time: datetime | None, release_time: datetime | None, now_utc: datetime, trending_hit: bool) -> str:
    created = parse_dt(repo.created_at)
    if created and now_utc - created <= timedelta(hours=24):
        return "high:new_repo_24h"
    if release_time and now_utc - release_time <= timedelta(hours=24):
        return "high:release_24h"
    if trending_hit and content_time and now_utc - content_time <= timedelta(hours=24):
        return "high:trending_24h"
    if content_time and now_utc - content_time <= timedelta(hours=48):
        return "medium:update_48h"
    return "low:metadata_update"


def ai_signal_type(repo: RepoCandidate, release_time: datetime | None, freshness_tier: str, trending_hit: bool, now_utc: datetime) -> str:
    created = parse_dt(repo.created_at)
    if created and now_utc - created <= timedelta(hours=24):
        return "new_project"
    if freshness_tier.startswith("high:trending") and trending_hit:
        return "new_project"
    if release_time is not None or freshness_tier.startswith("medium:") or freshness_tier.startswith("high:release"):
        return "fresh_development"
    return "fresh_development"


def ai_relevance_score(categories: list[str]) -> float:
    if not categories:
        return 0.4
    scores = []
    for c in categories:
        try:
            idx = AI_RELEVANCE_PRIORITY.index(c)
        except ValueError:
            idx = len(AI_RELEVANCE_PRIORITY)
        scores.append(max(0.2, 1.0 - 0.05 * idx))
    return max(0.0, min(1.0, sum(scores) / len(scores)))


def load_override_for_today() -> dict[str, Any]:
    if not OVERRIDE_PATH.exists():
        return {}
    try:
        payload = json.loads(OVERRIDE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("date") != today_et():
        return {}
    return payload


def generate_daily_ai(collector: GitHubCollector, translator: Translator) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    now_utc = datetime.now(timezone.utc)
    window_start = now_utc - timedelta(hours=24)
    history_raw = ensure_list(AI_HISTORY_PATH)
    history: list[dict[str, Any]] = []
    seen_dates: set[str] = set()
    for rec in history_raw:
        d = str(rec.get("date") or "")
        if not d or d in seen_dates:
            continue
        seen_dates.add(d)
        history.append(rec)
    if history and history[0].get("date") == today_et():
        locked = dict(history[0])
        locked["generated_at_utc"] = locked.get("generated_at_utc") or iso_utc_now()
        return locked, history, {
            "source": "history_locked_today",
            "candidate_count": 0,
            "trending_count": 0,
            "topic_count": 0,
        }
    old_recent = {
        rec.get("source_url", "").rstrip("/")
        for rec in history
        if parse_dt(rec.get("generated_at_utc")) and parse_dt(rec.get("generated_at_utc")) >= now_utc - timedelta(days=7)
    }
    recent_categories: list[str] = []
    for rec in history[:3]:
        cats = rec.get("topic_categories")
        if isinstance(cats, list):
            recent_categories.extend([str(c) for c in cats if c])
    dominant_category = ""
    dominant_count = 0
    if recent_categories:
        counts: dict[str, int] = {}
        for c in recent_categories:
            counts[c] = counts.get(c, 0) + 1
        dominant_category, dominant_count = max(counts.items(), key=lambda kv: kv[1])

    trending_names = collector.fetch_trending_names(limit=200)
    trending_set = set(trending_names)
    trending_candidates: list[RepoCandidate] = []
    for full_name in trending_names[:120]:
        repo = collector.fetch_repo_detail(full_name)
        if repo:
            trending_candidates.append(repo)

    topic_candidates = collector.fetch_topic_candidates(per_topic_max=20)

    merged: dict[str, RepoCandidate] = {}
    for repo in trending_candidates + topic_candidates:
        merged[repo.full_name] = repo

    strict_pool: list[dict[str, Any]] = []
    relaxed_pool: list[dict[str, Any]] = []
    for repo in merged.values():
        if repo.stars < 5:
            continue
        if repo.html_url.rstrip("/") in old_recent:
            continue
        rel_time_str = collector.fetch_latest_release_time(repo.full_name)
        rel_time = parse_dt(rel_time_str)
        content_time = rel_time or parse_dt(repo.pushed_at or repo.updated_at)
        if not content_time:
            continue

        readme = collector.fetch_readme_text(repo.full_name)
        categories = ai_topic_categories(repo, readme)
        flags = ai_quality_flags(repo, readme)
        freshness_tier = ai_freshness_tier(repo, content_time, rel_time, now_utc, repo.full_name in trending_set)

        topic_hit_count = sum(1 for t in repo.topics if str(t).lower() in TOPICS)
        utility_base = 0.6
        cls = classify_repo(repo)
        if cls in {"Agent Framework", "Tooling"}:
            utility_base = 0.85
        elif cls == "Skill / Workflow":
            utility_base = 0.75
        if any(k in readme.lower() for k in ("usage", "quickstart", "example", "install")):
            utility_base = min(1.0, utility_base + 0.1)

        quality_base = 0.35
        if len(readme.strip()) >= 260:
            quality_base += 0.2
        if "license" in readme.lower():
            quality_base += 0.15
        if repo.stars >= 100:
            quality_base += 0.15
        quality_base = max(0.0, min(1.0, quality_base))

        freshness_score = 0.35
        if freshness_tier.startswith("high:"):
            freshness_score = 1.0
        elif freshness_tier.startswith("medium:"):
            freshness_score = 0.7

        item = {
            "repo": repo,
            "content_time": content_time,
            "release_time": rel_time,
            "readme": readme,
            "categories": categories,
            "flags": flags,
            "freshness_tier": freshness_tier,
            "freshness_score": freshness_score,
            "relevance_score": ai_relevance_score(categories),
            "utility_score": utility_base,
            "quality_score": quality_base,
            "topic_hit_count": topic_hit_count,
            "trending_hit": repo.full_name in trending_set,
        }
        item["signal_type"] = ai_signal_type(repo, rel_time, freshness_tier, bool(item["trending_hit"]), now_utc)
        item["is_metadata_only"] = freshness_tier.startswith("low:")

        if window_start <= content_time <= now_utc and soft_quality_pass(repo, readme):
            if "blacklist_match" not in flags and "low_value_repo_type" not in flags:
                strict_pool.append(item)

        relaxed_window_start = now_utc - timedelta(hours=72)
        if relaxed_window_start <= content_time <= now_utc and relaxed_quality_pass(repo, readme):
            if "blacklist_match" not in flags:
                relaxed_pool.append(item)

    def apply_ai_scores(pool: list[dict[str, Any]]) -> None:
        if not pool:
            return
        stars = [int(it["repo"].stars) for it in pool]
        lo = min(stars)
        hi = max(stars)
        for it in pool:
            star = float(int(it["repo"].stars))
            star_norm = 0.5 if hi <= lo else (star - lo) / (hi - lo)
            momentum = 0.55 * star_norm
            if it["trending_hit"]:
                momentum += 0.25
            momentum += min(0.2, 0.05 * int(it["topic_hit_count"]))
            momentum = max(0.0, min(1.0, momentum))
            it["momentum_score"] = momentum
            base_final = (
                0.30 * float(it["freshness_score"])
                + 0.25 * float(it["momentum_score"])
                + 0.20 * float(it["relevance_score"])
                + 0.15 * float(it["utility_score"])
                + 0.10 * float(it["quality_score"])
            )
            penalty = 0.0
            # Weak freshness should not win unless momentum+utility are very strong.
            if bool(it.get("is_metadata_only")) and (float(it["momentum_score"]) < 0.75 or float(it["utility_score"]) < 0.75):
                penalty += 0.18
            primary_cat = str(it["categories"][0]) if it["categories"] else ""
            if dominant_category and dominant_count >= 2 and primary_cat == dominant_category:
                penalty += 0.15
            # Penalty for category repetition in recent 7d history.
            recent_same = 0
            for rec in history:
                cats = rec.get("topic_categories")
                if isinstance(cats, list) and primary_cat and primary_cat in cats:
                    recent_same += 1
            if recent_same >= 2:
                penalty += min(0.12, 0.04 * (recent_same - 1))
            it["repetition_penalty"] = penalty
            it["final_score"] = max(0.0, min(1.0, base_final - penalty))

    apply_ai_scores(strict_pool)
    apply_ai_scores(relaxed_pool)
    strict_pool.sort(key=lambda it: float(it.get("final_score") or 0.0), reverse=True)
    relaxed_pool.sort(key=lambda it: float(it.get("final_score") or 0.0), reverse=True)

    selected: dict[str, Any] | None = strict_pool[0] if strict_pool else None
    relaxed_source = "github_live"
    if not selected and relaxed_pool:
        selected = relaxed_pool[0]
        relaxed_source = "github_relaxed_72h"

    selected_repo: RepoCandidate | None = selected["repo"] if selected else None
    selected_time: datetime | None = selected["content_time"] if selected else None

    # Fallback tier-1: widen freshness window to 72h + relaxed quality gates.
    if not selected_repo:
        relaxed_source = "github_live"

    # Fallback tier-2: if API/detail calls are sparse, still pick a fresh trending repo name.
    if not selected_repo and trending_names:
        for full_name in trending_names:
            url = f"https://github.com/{full_name}"
            if url.rstrip("/") in old_recent:
                continue
            selected_repo = RepoCandidate(
                full_name=full_name,
                html_url=url,
                stars=0,
                pushed_at=None,
                updated_at=None,
                created_at=None,
                description=f"Trending repository: {full_name}",
                topics=[],
            )
            selected_time = now_utc
            relaxed_source = "github_trending_fallback"
            break

    fallback_used = False
    if not selected_repo:
        fallback_used = True
        if history:
            latest = history[0]
            daily_pick = dict(latest)
            daily_pick["date"] = today_et()
            daily_pick["generated_at_utc"] = iso_utc_now()
            daily_pick["fallback_used"] = True
            return daily_pick, history, {
                "source": "fallback_history",
                "candidate_count": 0,
            }
        raise RuntimeError("No AI candidate and no history fallback available")

    selected_meta = selected or {
        "categories": ["app-framework"],
        "flags": [],
        "freshness_tier": "low:metadata_update",
        "final_score": 0.0,
        "freshness_score": 0.0,
        "momentum_score": 0.0,
        "relevance_score": 0.0,
        "utility_score": 0.0,
        "quality_score": 0.0,
        "repetition_penalty": 0.0,
    }
    raw_description = (selected_repo.description or "").strip()
    # Use GitHub description first, but constrain length and quality for UI readability.
    if not raw_description or len(raw_description) < 18:
        raw_description = auto_ai_description(selected_repo)
    description = smart_truncate(raw_description, AI_DESC_MAX_CHARS)
    summary = "Selected via mixed AI signal scoring with freshness, relevance, utility, quality, and anti-repetition controls."
    if str(selected_meta.get("freshness_tier", "")).startswith("high:"):
        summary = "High-priority freshness signal (new release/new repo/trending) with strong practical relevance."
    tags = [t for t in selected_repo.topics[:3]] or ["ai", "github"]
    topic_categories = list(selected_meta.get("categories") or ["app-framework"])
    selection_reason = "Balanced AI signal after quality filtering and anti-repetition."
    if float(selected_meta.get("freshness_score") or 0.0) >= 0.9:
        selection_reason = "High freshness signal with practical builder relevance."
    elif float(selected_meta.get("relevance_score") or 0.0) >= 0.8:
        selection_reason = "Strong audience relevance for AI builders."
    if str(selected_meta.get("signal_type") or "") == "new_project":
        selection_reason = "New project signal with high freshness and practical relevance."

    ai_item = {
        "id": f"ai-{today_et()}-{selected_repo.full_name.lower().replace('/', '-')}",
        "date": today_et(),
        "generated_at_utc": iso_utc_now(),
        "source_platform": "github",
        "source_url": selected_repo.html_url,
        "title": selected_repo.full_name,
        "description": description,
        "description_zh": translator.to_zh(description),
        "summary": summary,
        "summary_zh": translator.to_zh(summary),
        "tags": tags,
        "category": classify_repo(selected_repo),
        "topic_categories": topic_categories,
        "quality_flags": list(selected_meta.get("flags") or []),
        "freshness_tier": str(selected_meta.get("freshness_tier") or "low:metadata_update"),
        "selection_reason": selection_reason,
        "signal_type": str(selected_meta.get("signal_type") or "fresh_development"),
        "updated_at": selected_time.isoformat().replace("+00:00", "Z") if selected_time else (selected_repo.updated_at or ""),
        "score_raw": selected_repo.stars,
        "final_score": round(float(selected_meta.get("final_score") or 0.0), 4),
        "freshness_score": round(float(selected_meta.get("freshness_score") or 0.0), 4),
        "momentum_score": round(float(selected_meta.get("momentum_score") or 0.0), 4),
        "relevance_score": round(float(selected_meta.get("relevance_score") or 0.0), 4),
        "utility_score": round(float(selected_meta.get("utility_score") or 0.0), 4),
        "quality_score": round(float(selected_meta.get("quality_score") or 0.0), 4),
        "repetition_penalty": round(float(selected_meta.get("repetition_penalty") or 0.0), 4),
        "fallback_used": fallback_used,
    }

    new_history = [ai_item] + [h for h in history if h.get("id") != ai_item["id"]]
    new_history = new_history[:30]

    return ai_item, new_history, {
        "source": relaxed_source,
        "candidate_count": len(strict_pool),
        "strict_pool_count": len(strict_pool),
        "relaxed_pool_count": len(relaxed_pool),
        "trending_count": len(trending_candidates),
        "topic_count": len(topic_candidates),
        "dominant_recent_category": dominant_category,
        "dominant_recent_count": dominant_count,
        "selected_signal_type": str(selected_meta.get("signal_type") or ""),
        "selected_freshness_tier": str(selected_meta.get("freshness_tier") or ""),
    }


def reddit_posts_for_subreddit(subreddit: str, user_agent: str) -> list[dict[str, Any]]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t=day&limit=50"
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }
    try:
        payload = get_json(url, headers=headers)
    except Exception:
        return []
    children = ((payload.get("data") or {}).get("children") or [])
    posts = []
    for child in children:
        data = child.get("data") or {}
        title = (data.get("title") or "").strip()
        if not title:
            continue
        posts.append(
            {
                "source_platform": "reddit",
                "source_url": f"https://www.reddit.com{data.get('permalink', '')}",
                "title": title,
                "summary": title,
                "tags": [subreddit],
                "created_at": datetime.fromtimestamp(float(data.get("created_utc") or 0), tz=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "engagement": int(data.get("score") or 0) + 2 * int(data.get("num_comments") or 0),
            }
        )
    return posts


def x_recent_posts(token: str, query_keywords: list[str]) -> list[dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "CryptoSherryDailyBot/1.0",
    }
    query = "(" + " OR ".join(query_keywords) + ") lang:en -is:retweet"
    params = {
        "query": query,
        "max_results": "40",
        "tweet.fields": "created_at,public_metrics",  # type: ignore[dict-item]
    }
    url = "https://api.twitter.com/2/tweets/search/recent?" + urllib.parse.urlencode(params)
    try:
        payload = get_json(url, headers=headers)
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for tw in payload.get("data") or []:
        metrics = tw.get("public_metrics") or {}
        likes = int(metrics.get("like_count") or 0)
        retweets = int(metrics.get("retweet_count") or 0)
        replies = int(metrics.get("reply_count") or 0)
        views = int(metrics.get("impression_count") or 0)
        engagement = likes + 2 * retweets + 2 * replies + int(views / 500)
        tid = tw.get("id")
        text = (tw.get("text") or "").replace("\n", " ").strip()
        if not tid or not text:
            continue
        out.append(
            {
                "source_platform": "x",
                "source_url": f"https://x.com/i/web/status/{tid}",
                "title": text[:220],
                "summary": text[:220],
                "tags": ["X"],
                "created_at": tw.get("created_at"),
                "engagement": engagement,
            }
        )
    return out


def clean_html_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def rss_recent_posts(source_name: str, feed_url: str, user_agent: str) -> list[dict[str, Any]]:
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8",
    }
    try:
        xml_text = get_text(feed_url, headers=headers)
        root = ETXML.fromstring(xml_text)
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        title = clean_html_text(item.findtext("title") or "")
        link = (item.findtext("link") or "").strip()
        summary = clean_html_text(item.findtext("description") or title)
        pub = (item.findtext("pubDate") or "").strip()
        created_at = None
        if pub:
            try:
                created_at = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            except Exception:
                created_at = None
        if not title or not link:
            continue
        tags = [clean_html_text(c.text or "") for c in item.findall("category") if (c.text or "").strip()]
        items.append(
            {
                "source_platform": source_name,
                "source_url": link,
                "title": title,
                "summary": summary or title,
                "tags": tags[:3] or [source_name],
                "created_at": created_at or iso_utc_now(),
                "engagement": 0,
            }
        )
    return items


def keep_within_24h(items: list[dict[str, Any]], now_utc: datetime) -> list[dict[str, Any]]:
    start = now_utc - timedelta(hours=24)
    out: list[dict[str, Any]] = []
    for it in items:
        created = parse_dt(it.get("created_at"))
        if created and start <= created <= now_utc:
            out.append(it)
    return out


def title_match(a: str, b: str) -> float:
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio()


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for item in items:
        dup = False
        for existing in kept:
            if item.get("source_url") == existing.get("source_url"):
                dup = True
                break
            if title_match(item.get("title", ""), existing.get("title", "")) >= 0.85:
                dup = True
                break
        if not dup:
            kept.append(item)
    return kept


def keyword_filter(items: list[dict[str, Any]], keywords: list[str] | None) -> list[dict[str, Any]]:
    if not keywords:
        return items
    lowered = [k.lower() for k in keywords]
    out: list[dict[str, Any]] = []
    for it in items:
        hay = f"{it.get('title', '')} {it.get('summary', '')}".lower()
        if any(k in hay for k in lowered):
            out.append(it)
    return out


def extract_topic_fields(item: dict[str, Any]) -> tuple[list[str], list[str], list[str], str]:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    assets = [a for a in ASSET_TERMS if re.search(rf"\b{re.escape(a)}\b", text)]
    narratives = [n for n in NARRATIVE_TERMS if re.search(rf"\b{re.escape(n)}\b", text)]
    actions = [a for a in ACTION_TERMS if re.search(rf"\b{re.escape(a)}\w*\b", text)]

    def canonical_asset(values: list[str]) -> str:
        if "bitcoin" in values:
            return "btc"
        if "ethereum" in values:
            return "eth"
        if "solana" in values:
            return "sol"
        return values[0] if values else "market"

    topic_parts = [canonical_asset(assets)]
    if narratives:
        topic_parts.append(narratives[0])
    if actions:
        topic_parts.append(actions[0])
    topic_key = " + ".join(topic_parts)
    return assets[:3], narratives[:3], actions[:3], topic_key


def assess_market_candidate(item: dict[str, Any]) -> tuple[str, list[str]]:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower().strip()
    title = (item.get("title") or "").lower().strip()
    flags: list[str] = []

    if any(k in text for k in MARKET_FINAL_BLACKLIST):
        flags.append("blacklist_match")
    if any(k in text for k in ("thread", "discussion")):
        flags.append("thread_like")
    if any(k in text for k in MARKET_PROMO_PATTERNS):
        flags.append("promo_like")
    if any(k in text for k in ("airdrop", "free money", "guaranteed")):
        flags.append("bait")
    if any(k in text for k in MARKET_MEME_PATTERNS):
        flags.append("meme_like")
    if any(k in text for k in MARKET_RECAP_PATTERNS):
        flags.append("repetitive")
    sentiment_only = any(k in text for k in ("bullish", "bearish", "moon", "pump")) and len(text.split()) < 14
    if sentiment_only:
        flags.append("low_context")

    if any(k in text for k in ("hack", "exploit", "etf", "regulation", "files", "approved", "launch")):
        content_type = "news"
    elif any(k in text for k in ("analysis", "deep dive", "breakdown", "because", "impact")):
        content_type = "analysis"
    elif any(k in text for k in ("i think", "opinion", "hot take", "in my view")):
        content_type = "opinion"
    elif "discussion" in title or "thread" in title:
        content_type = "discussion"
    elif any(k in text for k in ("meme", "lol", "shitpost")):
        content_type = "meme"
    elif any(k in text for k in ("airdrop", "giveaway", "referral", "join now")):
        content_type = "promo"
    elif any(k in text for k in ("recap", "market wrap")):
        content_type = "recap"
    else:
        content_type = "analysis"

    return content_type, sorted(set(flags))


def normalize_engagement(items: list[dict[str, Any]]) -> dict[str, float]:
    vals = [float(int(it.get("engagement") or 0)) for it in items]
    if not vals:
        return {}
    lo = min(vals)
    hi = max(vals)
    out: dict[str, float] = {}
    for it in items:
        key = str(it.get("source_url") or "")
        v = float(int(it.get("engagement") or 0))
        if hi <= lo:
            out[key] = 0.5
        else:
            out[key] = max(0.0, min(1.0, (v - lo) / (hi - lo)))
    return out


def source_quality_score(item: dict[str, Any]) -> float:
    source = str(item.get("source_platform") or "").strip().lower()
    base = SOURCE_QUALITY_BASE.get(source, 0.6)
    title = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    if source == "reddit":
        if "analysis" in title or "breakdown" in title:
            base += 0.05
        if "daily discussion" in title:
            base -= 0.2
    if source in {"coindesk", "cointelegraph", "the block"}:
        base += 0.04
    return max(0.0, min(1.0, base))


def info_density_score(item: dict[str, Any], assets: list[str], narratives: list[str], actions: list[str]) -> float:
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    text = f"{title} {summary}".lower()
    score = 0.25
    if re.search(r"\$?\d+(?:[.,]\d+)?(?:[kmbKMB%])?", text):
        score += 0.2
    if assets:
        score += 0.15
    if narratives:
        score += 0.15
    if actions:
        score += 0.15
    if any(k in text for k in ("because", "after", "due to", "impact", "caused", "driven by")):
        score += 0.1
    if len(title.split()) >= 8:
        score += 0.05
    return max(0.0, min(1.0, score))


def market_relevance_score(item: dict[str, Any], narratives: list[str], assets: list[str]) -> float:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    score = 0.35
    if narratives:
        score += 0.25
    if assets:
        score += 0.1
    if any(k in text for k in ("etf", "regulation", "upgrade", "mainnet", "hack", "exploit", "treasury", "flows", "unlock", "fees", "revenue")):
        score += 0.2
    if any(k in text for k in ("gm", "moon", "wen", "meme")):
        score -= 0.2
    return max(0.0, min(1.0, score))


def novelty_score(topic_key: str, history_market: list[dict[str, Any]], now_et: date) -> float:
    recent = [it for it in history_market if str(it.get("topic_key") or "") == topic_key]
    if not recent:
        return 1.0
    min_days = 999
    for it in recent:
        d = parse_date_ymd(str(it.get("date") or ""))
        if not d:
            continue
        delta = (now_et - d).days
        if delta >= 0:
            min_days = min(min_days, delta)
    if min_days == 999:
        return 0.7
    if min_days <= 1:
        return 0.2
    if min_days <= 3:
        return 0.45
    if min_days <= 7:
        return 0.65
    return 0.9


def generate_daily_market(x_token: str | None, translator: Translator) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    now_utc = datetime.now(timezone.utc)
    ua = "CryptoSherryDailyBot/1.0"
    today = datetime.now(ET).date()
    yesterday = (today - timedelta(days=1)).isoformat()

    def title_allowed(item: dict[str, Any]) -> bool:
        t = (item.get("title") or "").lower()
        return not any(b in t for b in MARKET_TITLE_BLACKLIST)

    def norm_title(value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    existing_market_raw = ensure_list(MARKET_DAILY_PATH)
    history_market_raw = ensure_list(MARKET_HISTORY_PATH)
    prev_day_items = [
        it
        for it in [*existing_market_raw, *history_market_raw]
        if str(it.get("date") or "") == yesterday
    ]
    if prev_day_items:
        seen_prev: set[str] = set()
        uniq_prev: list[dict[str, Any]] = []
        for it in prev_day_items:
            key = (str(it.get("source_url") or "").rstrip("/")) or norm_title(str(it.get("title") or ""))
            if key in seen_prev:
                continue
            seen_prev.add(key)
            uniq_prev.append(it)
        prev_day_items = uniq_prev

    prev_day_urls = {str(it.get("source_url") or "").rstrip("/") for it in prev_day_items if it.get("source_url")}
    prev_day_titles = {norm_title(str(it.get("title") or "")) for it in prev_day_items if it.get("title")}

    def repeated_prev_day(item: dict[str, Any]) -> bool:
        u = str(item.get("source_url") or "").rstrip("/")
        t = norm_title(str(item.get("title") or ""))
        if u and u in prev_day_urls:
            return True
        if t and t in prev_day_titles:
            return True
        return False

    reddit_pool: list[dict[str, Any]] = []
    for sub in REDDIT_WHITELIST:
        reddit_pool.extend(reddit_posts_for_subreddit(sub, ua))
    reddit_pool = keep_within_24h(reddit_pool, now_utc)
    reddit_pool = [it for it in reddit_pool if title_allowed(it) and not repeated_prev_day(it)]

    x_pool: list[dict[str, Any]] = []
    x_error = ""
    if x_token:
        x_pool = x_recent_posts(x_token, ["bitcoin", "ethereum", "depin", "defi", "layer2", "blockchain"])
        x_pool = keep_within_24h(x_pool, now_utc)
        x_pool = [it for it in x_pool if title_allowed(it) and not repeated_prev_day(it)]
        if not x_pool:
            x_error = "X token present but no result returned (query window/rate/auth)."
    else:
        x_error = "X_BEARER_TOKEN not set, fallback to Reddit fill strategy."

    def ranked(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(items, key=lambda x: int(x.get("engagement") or 0), reverse=True)

    reddit_strict = ranked(keyword_filter(reddit_pool, ALL_KEYWORDS))
    x_strict = ranked(keyword_filter(x_pool, ALL_KEYWORDS))

    selected: list[dict[str, Any]] = []
    selected.extend(x_strict[:2])
    selected.extend(reddit_strict[:1])

    if len(selected) < 3:
        remaining = ranked([*x_strict[2:], *reddit_strict[1:]])
        selected.extend(remaining[: 3 - len(selected)])

    if len(selected) < 3:
        relaxed_reddit = ranked(keyword_filter(reddit_pool, CORE_KEYWORDS))
        selected.extend(relaxed_reddit[: 3 - len(selected)])

    if len(selected) < 3:
        no_filter_reddit = ranked(keyword_filter(reddit_pool, None))
        selected.extend(no_filter_reddit[: 3 - len(selected)])

    selected = ranked(selected)
    selected = dedupe_items(selected)

    if len(selected) < 3:
        tail = dedupe_items(ranked([*x_pool, *reddit_pool]))
        for item in tail:
            if len(selected) >= 3:
                break
            if any(title_match(item.get("title", ""), s.get("title", "")) >= 0.85 for s in selected):
                continue
            selected.append(item)

    news_fallback_count = 0
    news_source_counts: dict[str, int] = {}
    if len(selected) < 3:
        for source_name, feed_url in NEWS_FALLBACK_SOURCES:
            if len(selected) >= 3:
                break
            feed_items = rss_recent_posts(source_name, feed_url, ua)
            feed_items = keep_within_24h(feed_items, now_utc)
            feed_items = [it for it in feed_items if title_allowed(it) and not repeated_prev_day(it)]
            news_source_counts[source_name] = len(feed_items)
            for item in feed_items:
                if len(selected) >= 3:
                    break
                if any(
                    item.get("source_url") == s.get("source_url")
                    or title_match(item.get("title", ""), s.get("title", "")) >= 0.85
                    for s in selected
                ):
                    continue
                selected.append(item)
                news_fallback_count += 1

    existing_market = [it for it in ensure_list(MARKET_DAILY_PATH) if title_allowed(it)]
    history_market = [it for it in ensure_list(MARKET_HISTORY_PATH) if title_allowed(it)]
    history_pool = dedupe_items(ranked([*existing_market, *history_market]))

    def within_days(item: dict[str, Any], days: int) -> bool:
        item_day = parse_date_ymd(str(item.get("date") or ""))
        if not item_day:
            return False
        delta = (datetime.now(ET).date() - item_day).days
        return 0 <= delta <= days

    history_fill_count = 0
    if len(selected) < 3:
        for days in (3, 5):
            if len(selected) >= 3:
                break
            for item in history_pool:
                if len(selected) >= 3:
                    break
                if not within_days(item, days):
                    continue
                if any(
                    item.get("source_url") == s.get("source_url")
                    or title_match(item.get("title", ""), s.get("title", "")) >= 0.85
                    or repeated_prev_day(item)
                    for s in selected
                ):
                    continue
                selected.append(item)
                history_fill_count += 1

    # Final hard filter + topic-level de-dup pass (output-stage gate).
    def is_hard_blocked(flags: list[str]) -> bool:
        hard = {"blacklist_match", "thread_like", "low_context", "repetitive", "bait", "promo_like", "meme_like"}
        return any(f in hard for f in flags)

    # Merge all available candidates so we can still fill to 3 after hard filtering.
    final_pool = dedupe_items(ranked([*selected, *x_pool, *reddit_pool, *history_pool]))
    today_et_date = datetime.now(ET).date()
    history_for_novelty = [it for it in history_market_raw if isinstance(it, dict)]
    eng_norm = normalize_engagement(final_pool)

    enriched_pool: list[dict[str, Any]] = []
    for item in final_pool:
        content_type, flags = assess_market_candidate(item)
        assets, narratives, actions, topic_key = extract_topic_fields(item)
        engagement_score = eng_norm.get(str(item.get("source_url") or ""), 0.5)
        novelty = novelty_score(topic_key, history_for_novelty, today_et_date)
        info_density = info_density_score(item, assets, narratives, actions)
        source_q = source_quality_score(item)
        market_rel = market_relevance_score(item, narratives, assets)
        final_score = (
            0.35 * engagement_score
            + 0.20 * novelty
            + 0.20 * info_density
            + 0.15 * source_q
            + 0.10 * market_rel
        )
        enriched = dict(item)
        enriched["content_type"] = content_type
        enriched["quality_flags"] = flags
        enriched["assets"] = assets
        enriched["narratives"] = narratives
        enriched["action_terms"] = actions
        enriched["topic_key"] = topic_key
        enriched["engagement_score"] = round(engagement_score, 4)
        enriched["novelty_score"] = round(novelty, 4)
        enriched["information_density_score"] = round(info_density, 4)
        enriched["source_quality_score"] = round(source_q, 4)
        enriched["market_relevance_score"] = round(market_rel, 4)
        enriched["final_score"] = round(final_score, 4)
        enriched_pool.append(enriched)
    final_pool = sorted(enriched_pool, key=lambda x: float(x.get("final_score") or 0.0), reverse=True)
    selected: list[dict[str, Any]] = []
    used_topics: set[str] = set()
    used_urls: set[str] = set()
    source_counts: dict[str, int] = {}
    asset_counts: dict[str, int] = {}
    opinion_count = 0

    def primary_asset(item: dict[str, Any]) -> str:
        assets = list(item.get("assets") or [])
        return str(assets[0]) if assets else "market"

    def high_info(item: dict[str, Any]) -> bool:
        return float(item.get("information_density_score") or 0.0) >= 0.6

    def is_candidate_eligible(item: dict[str, Any], strict: bool) -> bool:
        if not title_allowed(item) or repeated_prev_day(item):
            return False
        flags = list(item.get("quality_flags") or [])
        content_type = str(item.get("content_type") or "analysis")
        if strict:
            if is_hard_blocked(flags):
                return False
            if content_type not in {"news", "analysis", "opinion"}:
                return False
        else:
            if any(f in {"blacklist_match", "thread_like", "bait", "promo_like", "meme_like"} for f in flags):
                return False
        return True

    def can_add(item: dict[str, Any], require_new_topic: bool = True) -> bool:
        nonlocal opinion_count
        url = str(item.get("source_url") or "")
        topic_key = str(item.get("topic_key") or "market")
        content_type = str(item.get("content_type") or "analysis")
        if url and url in used_urls:
            return False
        if require_new_topic and topic_key in used_topics:
            return False
        if content_type == "opinion" and opinion_count >= 1:
            return False
        return True

    def register(item: dict[str, Any]) -> None:
        nonlocal opinion_count
        selected.append(item)
        url = str(item.get("source_url") or "")
        if url:
            used_urls.add(url)
        topic_key = str(item.get("topic_key") or "market")
        used_topics.add(topic_key)
        src = str(item.get("source_platform") or "").lower()
        source_counts[src] = source_counts.get(src, 0) + 1
        pa = primary_asset(item)
        asset_counts[pa] = asset_counts.get(pa, 0) + 1
        if str(item.get("content_type") or "") == "opinion":
            opinion_count += 1

    strict_pool = [it for it in final_pool if is_candidate_eligible(it, strict=True)]
    relaxed_pool = [it for it in final_pool if is_candidate_eligible(it, strict=False)]

    def pick_first(pool: list[dict[str, Any]], predicate) -> dict[str, Any] | None:
        for cand in pool:
            if can_add(cand) and predicate(cand):
                return cand
        return None

    # Pick 1: highest score with high info-density preferred.
    first = pick_first(strict_pool, lambda c: high_info(c))
    if not first:
        first = pick_first(strict_pool, lambda _c: True)
    if not first:
        first = pick_first(relaxed_pool, lambda _c: True)
    if first:
        register(first)

    # Pick 2: enforce topic diversity; different platform preferred.
    if len(selected) < 3:
        first_src = str(selected[0].get("source_platform") or "").lower() if selected else ""
        second = pick_first(strict_pool, lambda c: str(c.get("source_platform") or "").lower() != first_src)
        if not second:
            second = pick_first(strict_pool, lambda _c: True)
        if not second:
            second = pick_first(relaxed_pool, lambda _c: True)
        if second:
            register(second)

    # Pick 3: satisfy combination constraints as much as possible.
    if len(selected) < 3:
        need_high_info = not any(high_info(s) for s in selected)
        dominant_source = next(iter(source_counts.keys()), "")
        need_source_div = len(source_counts) == 1 and len(selected) >= 2
        dominant_asset = next(iter(asset_counts.keys()), "market")
        need_asset_div = len(asset_counts) == 1 and len(selected) >= 2

        def third_pref(c: dict[str, Any]) -> bool:
            if need_high_info and not high_info(c):
                return False
            if need_source_div and str(c.get("source_platform") or "").lower() == dominant_source:
                return False
            if need_asset_div and primary_asset(c) == dominant_asset:
                return False
            return True

        third = pick_first(strict_pool, third_pref)
        if not third:
            # Relax preference order but still try to diversify source.
            third = pick_first(
                strict_pool,
                lambda c: (not need_source_div) or str(c.get("source_platform") or "").lower() != dominant_source,
            )
        if not third:
            third = pick_first(relaxed_pool, lambda _c: True)
        if third:
            register(third)

    # Safety fill to 3 if constraints are too strict.
    if len(selected) < 3:
        for cand in relaxed_pool:
            if len(selected) >= 3:
                break
            if not can_add(cand, require_new_topic=False):
                continue
            register(cand)

    out: list[dict[str, Any]] = []
    for idx, item in enumerate(selected, start=1):
        title = item.get("title", "")
        summary = item.get("summary") or title
        content_type = str(item.get("content_type") or "analysis")
        topic_key = str(item.get("topic_key") or "market")
        novelty = float(item.get("novelty_score") or 0.0)
        info_density = float(item.get("information_density_score") or 0.0)
        source_q = float(item.get("source_quality_score") or 0.0)
        market_rel = float(item.get("market_relevance_score") or 0.0)
        if novelty >= 0.8 and market_rel >= 0.7:
            selection_reason = "High market relevance + fresh topic with low redundancy"
        elif info_density >= 0.7:
            selection_reason = "High information density with concrete market signal"
        elif source_q >= 0.82:
            selection_reason = "Higher source quality and clear market usefulness"
        elif content_type == "news":
            selection_reason = "Timely market development with strong signal"
        elif content_type == "opinion":
            selection_reason = "Opinion selected after quality and diversity constraints"
        else:
            selection_reason = "Balanced score after filtering and diversity constraints"
        out.append(
            {
                "id": f"market-{today_et()}-{idx:02d}",
                "date": today_et(),
                "generated_at_utc": iso_utc_now(),
                "source_platform": item.get("source_platform", "reddit"),
                "source_url": item.get("source_url", "https://x.com/"),
                "title": title,
                "title_zh": translator.to_zh(title),
                "summary": summary,
                "summary_zh": translator.to_zh(summary),
                "tags": item.get("tags") or ["market"],
                "engagement": int(item.get("engagement") or 0),
                "content_type": content_type,
                "quality_flags": item.get("quality_flags") or [],
                "topic_key": topic_key,
                "assets": item.get("assets") or [],
                "selection_reason": selection_reason,
                "engagement_score": float(item.get("engagement_score") or 0.0),
                "novelty_score": float(item.get("novelty_score") or 0.0),
                "information_density_score": float(item.get("information_density_score") or 0.0),
                "source_quality_score": float(item.get("source_quality_score") or 0.0),
                "market_relevance_score": float(item.get("market_relevance_score") or 0.0),
                "final_score": float(item.get("final_score") or 0.0),
            }
        )

    if not out:
        existing = ensure_list(MARKET_DAILY_PATH)
        if existing:
            existing = [it for it in existing if title_allowed(it)]
            return existing[:3], {
                "x_candidates": len(x_pool),
                "reddit_candidates": len(reddit_pool),
                "output_count": len(existing[:3]),
                "x_enabled": bool(x_token),
                "x_diagnostic": f"{x_error} | market fallback: keep existing file",
            }

    return out, {
        "x_candidates": len(x_pool),
        "reddit_candidates": len(reddit_pool),
        "output_count": len(out),
        "fill_from_recent_3d_5d": history_fill_count,
        "news_fallback_count": news_fallback_count,
        "news_source_counts": news_source_counts,
        "prev_day_block_count": len(prev_day_items),
        "selected_topic_count": len({str(it.get("topic_key") or "") for it in out}),
        "selected_source_count": len({str(it.get("source_platform") or "") for it in out}),
        "selected_has_high_info_item": any(float(it.get("information_density_score") or 0.0) >= 0.6 for it in out),
        "x_enabled": bool(x_token),
        "x_diagnostic": x_error,
    }


def apply_override(
    ai_item: dict[str, Any],
    market_items: list[dict[str, Any]],
    mode: str = "all",
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    override = load_override_for_today()
    if not override:
        return ai_item, market_items, False

    changed = False

    ai_override = override.get("ai")
    if mode in ("all", "ai") and isinstance(ai_override, dict) and ai_override:
        merged = dict(ai_item)
        merged.update(ai_override)
        ai_item = merged
        changed = True

    market_override = override.get("market")
    if mode in ("all", "market") and isinstance(market_override, list) and market_override:
        replaced: list[dict[str, Any]] = []
        for idx, entry in enumerate(market_override[:3], start=1):
            if not isinstance(entry, dict):
                continue
            base = market_items[idx - 1] if idx - 1 < len(market_items) else {
                "id": f"market-{today_et()}-{idx:02d}",
                "date": today_et(),
                "generated_at_utc": iso_utc_now(),
                "source_platform": "reddit",
                "source_url": "https://www.reddit.com",
                "title": "",
                "title_zh": "",
                "summary": "",
                "summary_zh": "",
                "tags": ["market"],
                "engagement": 0,
            }
            merged = dict(base)
            merged.update(entry)
            replaced.append(merged)
        if replaced:
            market_items = replaced + market_items[len(replaced) :]
            market_items = market_items[:3]
            changed = True

    return ai_item, market_items, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate daily AI + Market data for CryptoSherry site")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["all", "ai", "market"],
        default="all",
        help="Generate both daily datasets (all) or only one side (ai/market).",
    )
    args = parser.parse_args()

    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    x_token = os.getenv("X_BEARER_TOKEN")
    translator = Translator()

    collector = GitHubCollector(gh_token)

    ai_meta: dict[str, Any] = {"source": "existing"}
    market_meta: dict[str, Any] = {"source": "existing"}

    if args.mode in ("all", "ai"):
        ai_item, ai_history, ai_meta = generate_daily_ai(collector, translator)
    else:
        existing_ai = ensure_list(AI_DAILY_PATH)
        ai_item = dict(existing_ai[0]) if existing_ai else {}
        ai_history = ensure_list(AI_HISTORY_PATH)

    if args.mode in ("all", "market"):
        market_items, market_meta = generate_daily_market(x_token, translator)
    else:
        market_items = ensure_list(MARKET_DAILY_PATH)

    ai_item_final, market_items_final, overridden = apply_override(ai_item, market_items, mode=args.mode)

    if args.dry_run:
        print(json.dumps({
            "ai": ai_item_final,
            "market": market_items_final,
            "meta": {
                "ai": ai_meta,
                "market": market_meta,
                "override_applied": overridden,
            },
        }, ensure_ascii=False, indent=2))
        return 0

    if args.mode in ("all", "ai"):
        write_json(AI_DAILY_PATH, [ai_item_final])
        write_json(AI_HISTORY_PATH, ai_history)
    if args.mode in ("all", "market"):
        write_json(MARKET_DAILY_PATH, market_items_final)
        old_market_history = ensure_list(MARKET_HISTORY_PATH)
        merged_market_history = [*market_items_final, *old_market_history]
        seen_ids: set[str] = set()
        stable_history: list[dict[str, Any]] = []
        for item in merged_market_history:
            key = str(item.get("id") or "")
            if key and key in seen_ids:
                continue
            if key:
                seen_ids.add(key)
            stable_history.append(item)
        write_json(MARKET_HISTORY_PATH, stable_history[:180])

    print("Wrote:")
    if args.mode in ("all", "ai"):
        print(f"- {AI_DAILY_PATH}")
        print(f"- {AI_HISTORY_PATH}")
    if args.mode in ("all", "market"):
        print(f"- {MARKET_DAILY_PATH}")
        print(f"- {MARKET_HISTORY_PATH}")
    print(json.dumps({
        "ai": ai_meta,
        "market": market_meta,
        "override_applied": overridden,
        "generated_at_utc": iso_utc_now(),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
