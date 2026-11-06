from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import feedparser
import httpx
import asyncio
from typing import Optional
import time
import re
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Sports News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

FEEDS = {
    "football": [
        {"name": "BBC Sport Football", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml"},
        {"name": "ESPN Soccer", "url": "https://www.espn.com/espn/rss/soccer/news"},
        {"name": "NOS Voetbal", "url": "https://feeds.nos.nl/nossportvoetbal"},
        {"name": "Goal.com", "url": "https://www.goal.com/feeds/en/news"},
    ],
    "f1": [
        {"name": "BBC Sport F1", "url": "https://feeds.bbci.co.uk/sport/formula1/rss.xml"},
        {"name": "The Race", "url": "https://the-race.com/category/formula-1/feed/"},
        {"name": "RaceFans", "url": "https://www.racefans.net/feed/"},
        {"name": "Autosport", "url": "https://www.autosport.com/rss/f1/news/"},
        {"name": "Motorsport.com", "url": "https://www.motorsport.com/rss/f1/news/"},
    ],
    "nfl": [
        {"name": "ESPN NFL", "url": "https://www.espn.com/espn/rss/nfl/news"},
        {"name": "Pro Football Talk", "url": "https://profootballtalk.nbcsports.com/feed/"},
        {"name": "NFL.com", "url": "https://www.nfl.com/rss/rsslanding?contentType=news"},
    ],
    "nba": [
        {"name": "ESPN NBA", "url": "https://www.espn.com/espn/rss/nba/news"},
        {"name": "Hoops Rumors", "url": "https://www.hoopsrumors.com/feed"},
        {"name": "Basketball Reference", "url": "https://www.basketball-reference.com/friv/rss.fcgi"},
    ],
    "tennis": [
        {"name": "BBC Sport Tennis", "url": "https://feeds.bbci.co.uk/sport/tennis/rss.xml"},
        {"name": "Tennis World USA", "url": "https://www.tennisworldusa.org/rss/news.xml"},
        {"name": "Tennis.com", "url": "https://www.tennis.com/feed/"},
    ],
    "cycling": [
        {"name": "CyclingNews", "url": "https://www.cyclingnews.com/news/feed/"},
        {"name": "VeloNews", "url": "https://velonews.com/feed/"},
        {"name": "Wielerflits", "url": "https://www.wielerflits.nl/feed/"},
        {"name": "Cycling Weekly", "url": "https://www.cyclingweekly.com/feed"},
    ],
    "skating": [
        {"name": "NOS Sport", "url": "https://feeds.nos.nl/nossport"},
        {"name": "SpeedSkatingNews", "url": "https://speedskatingnews.info/feed/"},
        {"name": "ISU", "url": "https://www.isu.org/rss-news"},
    ],
    "mlb": [
        {"name": "ESPN MLB", "url": "https://www.espn.com/espn/rss/mlb/news"},
        {"name": "MLB Trade Rumors", "url": "https://www.mlbtraderumors.com/feed"},
        {"name": "Baseball America", "url": "https://www.baseballamerica.com/feed/"},
    ],
    "darts": [
        {"name": "Darts1", "url": "https://www.darts1.de/en/rss.xml"},
        {"name": "Dartsnews", "url": "https://dartsnews.com/feed/"},
        {"name": "PDC", "url": "https://www.pdc.tv/news/rss"},
    ],
    "mma": [
        {"name": "MMA Junkie", "url": "https://mmajunkie.usatoday.com/feed"},
        {"name": "MMA Fighting", "url": "https://www.mmafighting.com/rss/current"},
        {"name": "Bloody Elbow", "url": "https://www.bloodyelbow.com/rss/current"},
    ],
    "nhl": [
        {"name": "ESPN NHL", "url": "https://www.espn.com/espn/rss/nhl/news"},
        {"name": "The Hockey News", "url": "https://thehockeynews.com/feed/"},
        {"name": "NHL.com", "url": "https://www.nhl.com/rss/news.xml"},
    ],
    "dutch": [
        {"name": "NOS Sport", "url": "https://feeds.nos.nl/nossport"},
        {"name": "Nu.nl Sport", "url": "https://www.nu.nl/rss/Sport"},
        {"name": "AD Sport", "url": "https://www.ad.nl/sport/rss.xml"},
    ],
    "olympics": [
        {"name": "BBC Sport Olympics", "url": "https://feeds.bbci.co.uk/sport/olympics/rss.xml"},
        {"name": "Around the Rings", "url": "https://aroundtherings.com/feed/"},
        {"name": "Inside the Games", "url": "https://www.insidethegames.biz/rss"},
    ],
}

CACHE: dict = {}
CACHE_TTL = 900  # 15 minutes

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SportsAggregator/1.0; +https://github.com/sports-aggregator)"
}


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


async def fetch_feed(client: httpx.AsyncClient, source: dict, sport: str) -> list:
    try:
        r = await client.get(source["url"], timeout=8.0, follow_redirects=True)
        feed = feedparser.parse(r.text)
        articles = []
        for entry in feed.entries[:8]:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            articles.append({
                "title": strip_html(entry.get("title", "")).strip(),
                "link": entry.get("link", ""),
                "summary": strip_html(entry.get("summary", ""))[:220].strip(),
                "published": time.mktime(pub) if pub else 0,
                "source": source["name"],
                "sport": sport,
            })
        return articles
    except Exception:
        return []


async def get_news(sport_filter: Optional[str]) -> list:
    key = sport_filter or "all"
    now = time.time()

    if key in CACHE and now - CACHE[key]["ts"] < CACHE_TTL:
        return CACHE[key]["data"]

    to_fetch = (
        {sport_filter: FEEDS[sport_filter]}
        if sport_filter and sport_filter in FEEDS
        else FEEDS
    )

    async with httpx.AsyncClient(headers=HEADERS) as client:
        tasks = [
            fetch_feed(client, src, sport)
            for sport, srcs in to_fetch.items()
            for src in srcs
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    articles = [a for r in results if isinstance(r, list) for a in r]
    articles.sort(key=lambda x: x["published"], reverse=True)

    CACHE[key] = {"ts": now, "data": articles}
    return articles


@app.get("/")
async def root():
    with open(os.path.join(BASE, "index.html")) as f:
        return Response(content=f.read(), media_type="text/html")

@app.get("/style.css")
async def css():
    with open(os.path.join(BASE, "style.css")) as f:
        return Response(content=f.read(), media_type="text/css")

@app.get("/app.js")
async def js():
    with open(os.path.join(BASE, "app.js")) as f:
        return Response(content=f.read(), media_type="application/javascript")

@app.get("/api/news")
@app.get("/api/index")
async def news(sport: Optional[str] = Query(None)):
    articles = await get_news(sport)
    resp = JSONResponse({
        "articles": articles,
        "count": len(articles),
        "fetched_at": CACHE.get(sport or "all", {}).get("ts", time.time()),
        "sports": list(FEEDS.keys()),
    })
    resp.headers["Cache-Control"] = "public, s-maxage=900, stale-while-revalidate=1800"
    return resp


