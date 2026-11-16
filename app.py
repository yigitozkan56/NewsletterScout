"""
NewsletterScout - Opt-In Newsletter Directory, Public RSS Cadence Analyzer & Sponsor Fit Matcher.
Exclusively processes public RSS feeds and creator-submitted opt-in metadata. Never accesses paywalled content.
"""

import os
from contextlib import closing
import sqlite3
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import typer
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app_cli = typer.Typer(help="NewsletterScout CLI - Match sponsors with opt-in newsletters via public RSS feeds.")
web_app = FastAPI(
    title="NewsletterScout API & Web UI",
    description="Matches sponsors and creators using public RSS feeds and voluntary opt-in newsletter profiles.",
    version="1.0.0",
)

OPT_IN_NEWSLETTERS = [
    {
        "slug": "pragmatic-devops-weekly",
        "title": "Pragmatic DevOps & Cloud Native Weekly",
        "rss_url": "https://example.org/devops/feed.xml",
        "niche_tags": "devops,kubernetes,cloud,sre,ci-cd",
        "cadence": "Weekly",
        "subscribers_opt_in": 18500,
        "opt_in_verified": True,
    },
    {
        "slug": "indie-ai-builders",
        "title": "Indie AI & Micro-SaaS Builders Digest",
        "rss_url": "https://example.org/indie-ai/rss.xml",
        "niche_tags": "ai,llm,micro-saas,python,indiehacker",
        "cadence": "Bi-Weekly",
        "subscribers_opt_in": 12400,
        "opt_in_verified": True,
    },
    {
        "slug": "modern-frontend-bytes",
        "title": "Modern TypeScript & UI Engineering Bytes",
        "rss_url": "https://example.org/ts-bytes/feed.xml",
        "niche_tags": "typescript,react,frontend,webdev,design-systems",
        "cadence": "Weekly",
        "subscribers_opt_in": 24000,
        "opt_in_verified": True,
    },
]


class OptInNewsletterRegistration(BaseModel):
    slug: str
    title: str
    rss_url: str
    niche_tags: str
    cadence: str = "Weekly"
    subscribers_opt_in: int = 1000


def analyze_public_rss_feed(xml_text: str) -> Dict[str, Any]:
    """Extracts public issue count and topic keywords from an open RSS feed without touching paywalled bodies."""
    root = ET.fromstring(xml_text.strip())
    channel_title = (root.findtext(".//channel/title") or "Public Newsletter").strip()
    items = root.findall(".//item")
    titles = [(i.findtext("title") or "").strip() for i in items]
    cadence_estimate = "Weekly" if len(items) >= 4 else ("Bi-Weekly" if len(items) >= 2 else "Monthly")
    return {
        "channel_title": channel_title,
        "public_issue_count": len(items),
        "cadence_estimate": cadence_estimate,
        "recent_titles": titles[:5],
    }


class NewsletterScoutDB:
    """SQLite local registry for opt-in newsletters and public RSS metadata."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("NEWSLETTERSCOUT_DB_PATH", "newsletterscout_cache.db")
        self._init_db()

    def _init_db(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS newsletters (
                    slug TEXT PRIMARY KEY,
                    title TEXT,
                    rss_url TEXT,
                    niche_tags TEXT,
                    cadence TEXT,
                    subscribers_opt_in INTEGER,
                    opt_in_verified INTEGER,
                    registered_at INTEGER
                )
                """
            )
            conn.commit()
        if not self.list_newsletters():
            for n in OPT_IN_NEWSLETTERS:
                self.register_newsletter(n)

    def register_newsletter(self, data: Dict[str, Any]) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO newsletters (
                    slug, title, rss_url, niche_tags, cadence,
                    subscribers_opt_in, opt_in_verified, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["slug"],
                    data["title"],
                    data["rss_url"],
                    data["niche_tags"],
                    data.get("cadence", "Weekly"),
                    int(data.get("subscribers_opt_in", 1000)),
                    1,
                    int(time.time()),
                ),
            )
            conn.commit()

    def list_newsletters(self) -> List[Dict[str, Any]]:
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM newsletters ORDER BY subscribers_opt_in DESC").fetchall()
            return [dict(r) for r in rows]


def match_sponsor_campaign(target_tags: List[str], db: Optional[NewsletterScoutDB] = None) -> List[Dict[str, Any]]:
    db = db or NewsletterScoutDB()
    items = db.list_newsletters()
    norm_targets = [t.strip().lower() for t in target_tags if t.strip()]
    results = []
    for item in items:
        haystack = f"{item['title']} {item['niche_tags']}".lower()
        hits = sum(1 for t in norm_targets if t in haystack)
        fit_score = round((hits / max(len(norm_targets), 1)) * 100.0, 1) if norm_targets else 100.0
        entry = dict(item)
        entry["sponsor_fit_score"] = fit_score
        results.append(entry)
    results.sort(key=lambda x: (x["sponsor_fit_score"], x["subscribers_opt_in"]), reverse=True)
    return results


@web_app.get("/api/newsletters")
def api_match_newsletters(
    tags: str = Query("ai,python,micro-saas", description="Comma-separated sponsor campaign tags"),
) -> Dict[str, Any]:
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    matched = match_sponsor_campaign(tag_list)
    return {"count": len(matched), "source": "Public RSS & Creator Opt-In Directory", "items": matched}


@web_app.post("/api/opt-in")
def api_opt_in_register(reg: OptInNewsletterRegistration) -> Dict[str, Any]:
    db = NewsletterScoutDB()
    data = reg.model_dump()
    db.register_newsletter(data)
    return {"status": "registered", "opt_in": True, "newsletter": data}


@web_app.get("/", response_class=HTMLResponse)
def web_dashboard(tags: str = "ai,devops,cloud") -> str:
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    matched = match_sponsor_campaign(tag_list)
    rows_html = "".join(
        f"<tr><td><strong>{n['title']}</strong><br><small>{n['rss_url']}</small></td>"
        f"<td><code>{n['niche_tags']}</code></td><td>{n['cadence']}</td>"
        f"<td>{n['subscribers_opt_in']:,}</td><td><strong>{n['sponsor_fit_score']}%</strong></td></tr>"
        for n in matched
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NewsletterScout - Opt-In Newsletter & Sponsor Matcher</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; background: #0f172a; color: #f8fafc; }}
        h1 {{ color: #38bdf8; }}
        .badge {{ background: #0284c7; padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.85rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #0f172a; color: #94a3b8; }}
    </style>
</head>
<body>
    <h1>ğŸ“¬ NewsletterScout <span class="badge">Public RSS & Voluntary Creator Opt-In</span></h1>
    <p>Matches developer product sponsors with opt-in newsletters for campaign tags: <code>{tags}</code></p>
    <table>
        <thead>
            <tr><th>Newsletter & RSS</th><th>Niche Tags</th><th>Cadence</th><th>Opt-In Reach</th><th>Sponsor Fit</th></tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
</body>
</html>"""


@app_cli.command("match")
def cli_match(
    tags: str = typer.Option("ai,python,micro-saas", "--tags", "-t", help="Sponsor target niche tags"),
) -> None:
    """Match sponsor campaign tags against opt-in public RSS newsletters."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    matched = match_sponsor_campaign(tag_list)
    typer.echo(f"{'Newsletter':<36} | {'Cadence':<10} | {'Subscribers':<12} | {'Sponsor Fit'}")
    typer.echo("-" * 78)
    for n in matched:
        typer.echo(
            f"{n['title'][:36]:<36} | {n['cadence']:<10} | {n['subscribers_opt_in']:<12,} | {n['sponsor_fit_score']}%"
        )


@app_cli.command("serve")
def cli_serve(port: int = typer.Option(8008, "--port", "-p")) -> None:
    """Start the NewsletterScout FastAPI web server."""
    import uvicorn

    uvicorn.run(web_app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    app_cli()
