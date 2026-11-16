import os
import tempfile

from fastapi.testclient import TestClient

from app import NewsletterScoutDB, analyze_public_rss_feed, match_sponsor_campaign, web_app


def test_analyze_public_rss_feed():
    rss = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Rust Weekly</title>
        <item><title>Issue 1</title></item>
        <item><title>Issue 2</title></item>
        <item><title>Issue 3</title></item>
        <item><title>Issue 4</title></item>
      </channel>
    </rss>"""
    info = analyze_public_rss_feed(rss)
    assert info["channel_title"] == "Rust Weekly"
    assert info["public_issue_count"] == 4
    assert info["cadence_estimate"] == "Weekly"


def test_match_sponsor_and_api():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = NewsletterScoutDB(db_path=os.path.join(tmpdir, "news.db"))
        matched = match_sponsor_campaign(["ai", "micro-saas"], db=db)
        assert matched[0]["slug"] == "indie-ai-builders"
        assert matched[0]["sponsor_fit_score"] == 100.0

    client = TestClient(web_app)
    resp = client.get("/api/newsletters?tags=devops,cloud")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 3
