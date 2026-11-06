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
import random

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
        {"name": "BBC Sport",             "url": "https://feeds.bbci.co.uk/sport/football/rss.xml"},
        {"name": "NOS Sport",             "url": "https://feeds.nos.nl/nossportvoetbal"},
        {"name": "NU.nl",                 "url": "https://www.nu.nl/rss/Voetbal"},
        {"name": "AD Sport",              "url": "https://www.ad.nl/voetbal/rss.xml"},
        {"name": "Voetbal International", "url": "https://www.vi.nl/rss"},
        {"name": "The Athletic",          "url": "https://news.google.com/rss/search?q=site:nytimes.com/athletic+football&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Flashscore",            "url": "https://news.google.com/rss/search?q=site:flashscore.com+football&hl=en-US&gl=US&ceid=US:en"},
    ],
    "f1": [
        {"name": "BBC Sport F1",   "url": "https://feeds.bbci.co.uk/sport/formula1/rss.xml"},
        {"name": "Autosport",      "url": "https://www.autosport.com/rss/f1/news/"},
        {"name": "Motorsport.com", "url": "https://www.motorsport.com/rss/f1/news/"},
        {"name": "AD Sport",       "url": "https://www.ad.nl/formule-1/rss.xml"},
        {"name": "NU.nl",          "url": "https://www.nu.nl/rss/Formule+1"},
        {"name": "Formula 1",      "url": "https://www.formula1.com/content/fom-website/en/latest/all.xml"},
        {"name": "The Athletic",   "url": "https://news.google.com/rss/search?q=site:nytimes.com/athletic+formula+1&hl=en-US&gl=US&ceid=US:en"},
    ],
    "nfl": [
        {"name": "ESPN NFL",          "url": "https://www.espn.com/espn/rss/nfl/news"},
        {"name": "Pro Football Talk", "url": "https://profootballtalk.nbcsports.com/feed/"},
        {"name": "NFL.com",           "url": "https://www.nfl.com/rss/rsslanding?contentType=news"},
        {"name": "The Athletic",      "url": "https://news.google.com/rss/search?q=site:nytimes.com/athletic+nfl&hl=en-US&gl=US&ceid=US:en"},
    ],
    "nba": [
        {"name": "ESPN NBA",           "url": "https://www.espn.com/espn/rss/nba/news"},
        {"name": "Basketball Reference","url": "https://www.basketball-reference.com/friv/rss.fcgi"},
        {"name": "NBA.com",            "url": "https://www.nba.com/news/rss"},
        {"name": "The Athletic",       "url": "https://news.google.com/rss/search?q=site:nytimes.com/athletic+nba&hl=en-US&gl=US&ceid=US:en"},
    ],
    "tennis": [
        {"name": "BBC Sport",    "url": "https://feeds.bbci.co.uk/sport/tennis/rss.xml"},
        {"name": "Tennis World", "url": "https://www.tennisworldusa.org/rss/news.xml"},
        {"name": "Tennis.com",   "url": "https://www.tennis.com/feed/"},
        {"name": "ATP Tour",     "url": "https://www.atptour.com/en/news/rss"},
        {"name": "WTA Tennis",   "url": "https://www.wtatennis.com/news/feed"},
        {"name": "NOS Sport",    "url": "https://feeds.nos.nl/nossporttennis"},
        {"name": "NU.nl",        "url": "https://www.nu.nl/rss/Tennis"},
        {"name": "The Athletic", "url": "https://news.google.com/rss/search?q=site:nytimes.com/athletic+tennis&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Flashscore",   "url": "https://news.google.com/rss/search?q=site:flashscore.com+tennis&hl=en-US&gl=US&ceid=US:en"},
    ],
    "cycling": [
        {"name": "CyclingNews",   "url": "https://www.cyclingnews.com/news/feed/"},
        {"name": "VeloNews",      "url": "https://velonews.com/feed/"},
        {"name": "Wielerflits",   "url": "https://www.wielerflits.nl/feed/"},
        {"name": "Cycling Weekly","url": "https://www.cyclingweekly.com/feed"},
        {"name": "NOS Sport",     "url": "https://feeds.nos.nl/nossportwielrennen"},
        {"name": "NU.nl",         "url": "https://www.nu.nl/rss/Wielrennen"},
    ],
    "skating": [
        {"name": "NOS Sport",       "url": "https://feeds.nos.nl/nossportschaatsen"},
        {"name": "SpeedSkatingNews","url": "https://speedskatingnews.info/feed/"},
        {"name": "ISU",             "url": "https://www.isu.org/rss-news"},
        {"name": "NU.nl",           "url": "https://www.nu.nl/rss/Schaatsen"},
        {"name": "Schaatsen.nl",    "url": "https://www.schaatsen.nl/nieuws/feed/"},
    ],
    "mlb": [
        {"name": "ESPN MLB",       "url": "https://www.espn.com/espn/rss/mlb/news"},
        {"name": "MLB Trade Rumors","url": "https://www.mlbtraderumors.com/feed"},
        {"name": "Baseball America","url": "https://www.baseballamerica.com/feed/"},
        {"name": "MLB.com",        "url": "https://www.mlb.com/feeds/news/rss.xml"},
        {"name": "The Athletic",   "url": "https://news.google.com/rss/search?q=site:nytimes.com/athletic+mlb&hl=en-US&gl=US&ceid=US:en"},
    ],
    "darts": [
        {"name": "Darts1",   "url": "https://www.darts1.de/en/rss.xml"},
        {"name": "Dartsnews","url": "https://dartsnews.com/feed/"},
        {"name": "PDC",      "url": "https://www.pdc.tv/news/rss"},
        {"name": "NOS Sport","url": "https://feeds.nos.nl/nossportdarts"},
        {"name": "NU.nl",    "url": "https://www.nu.nl/rss/Darts"},
        {"name": "Flashscore","url": "https://news.google.com/rss/search?q=site:flashscore.com+darts&hl=en-US&gl=US&ceid=US:en"},
    ],
    "mma": [
        {"name": "MMA Junkie",    "url": "https://mmajunkie.usatoday.com/feed"},
        {"name": "MMA Junkie EU", "url": "https://mmajunkie-eu.usatoday.com/feed"},
        {"name": "MMA Fighting",  "url": "https://www.mmafighting.com/rss/current"},
        {"name": "Bloody Elbow",  "url": "https://www.bloodyelbow.com/rss/current"},
    ],
    "nhl": [
        {"name": "ESPN NHL",      "url": "https://www.espn.com/espn/rss/nhl/news"},
        {"name": "The Hockey News","url": "https://thehockeynews.com/feed/"},
        {"name": "NHL.com",       "url": "https://www.nhl.com/rss/news.xml"},
        {"name": "The Athletic",  "url": "https://news.google.com/rss/search?q=site:nytimes.com/athletic+nhl&hl=en-US&gl=US&ceid=US:en"},
    ],
    "dutch": [
        {"name": "NOS Sport", "url": "https://feeds.nos.nl/nossport"},
        {"name": "NU.nl",     "url": "https://www.nu.nl/rss/Sport"},
        {"name": "Volkskrant","url": "https://www.volkskrant.nl/sport/rss.xml"},
    ],
    "olympics": [
        {"name": "BBC Sport",       "url": "https://feeds.bbci.co.uk/sport/olympics/rss.xml"},
        {"name": "Around the Rings","url": "https://aroundtherings.com/feed/"},
        {"name": "Inside the Games","url": "https://www.insidethegames.biz/rss"},
        {"name": "NOS Sport",       "url": "https://feeds.nos.nl/nossportatletiek"},
    ],
    "hockey": [
        {"name": "NOS Sport", "url": "https://feeds.nos.nl/nossporthockey"},
        {"name": "Hockey.nl", "url": "https://www.hockey.nl/nieuws/rss"},
    ],
}

CACHE: dict = {}
CACHE_TTL = 900

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SportsAggregator/1.0; +https://github.com/sports-aggregator)"
}

# Stop words for both English and Dutch — used for cross-language topic deduplication
_STOP = {
    "the","a","an","in","on","at","to","for","of","and","or","is","was","are",
    "were","has","have","had","be","been","will","would","could","should","may",
    "might","it","this","that","with","from","by","as","into","about","after",
    "before","over","under","than","but","so","not","no","up","out","do","did",
    "does","its","their","his","her","our","your","my","we","he","she","they",
    # Dutch
    "de","het","een","van","en","of","is","was","zijn","hebben","had","met",
    "uit","bij","na","als","maar","dat","dit","die","hij","ze","we","om","naar",
    "over","dan","nog","al","wel","niet","zo","ook","nu","er","zich","wat","wie",
    "hoe","waar","door","tijdens","voor","hun","onze","uw","mijn","ik","jij","u",
}


def _tokens(title: str) -> set:
    return {w for w in re.findall(r'\b\w+\b', title.lower()) if w not in _STOP and len(w) > 2}


def _duplicate(t1: str, t2: str, threshold: float = 0.55) -> bool:
    tok1, tok2 = _tokens(t1), _tokens(t2)
    if not tok1 or not tok2:
        return False
    return len(tok1 & tok2) / max(len(tok1), len(tok2)) >= threshold


def diversify(articles: list) -> list:
    """Round-robin interleave by source so no outlet dominates the feed."""
    groups: dict = {}
    for a in articles:
        groups.setdefault(a["source"], []).append(a)
    queues = list(groups.values())
    random.shuffle(queues)
    result = []
    while queues:
        for q in queues:
            if q:
                result.append(q.pop(0))
        queues = [q for q in queues if q]
    return result


def deduplicate(articles: list) -> list:
    kept = []
    for article in articles:
        if not any(_duplicate(article["title"], k["title"]) for k in kept):
            kept.append(article)
    return kept


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
    articles = deduplicate(articles)
    articles = diversify(articles)

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

@app.get("/manifest.json")
async def manifest():
    with open(os.path.join(BASE, "manifest.json")) as f:
        return Response(content=f.read(), media_type="application/manifest+json")

@app.get("/icon.svg")
async def icon():
    with open(os.path.join(BASE, "icon.svg")) as f:
        return Response(content=f.read(), media_type="image/svg+xml")

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
