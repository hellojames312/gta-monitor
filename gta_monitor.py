#!/usr/bin/env python3
"""
GTA VI Monitor — GitHub Actions versie
Draait eenmaal per aanroep (geen loop), state wordt opgeslagen in monitor_state.json
"""
import requests
import json
import os
import feedparser
import yfinance as yf
from datetime import datetime
import hashlib
import time

# Credentials uit GitHub Secrets
WHATSAPP_PHONE = os.environ.get("WHATSAPP_PHONE", "")
WHATSAPP_APIKEY = os.environ.get("WHATSAPP_APIKEY", "")

# ─────────────────────────────────────────────
# TIER 1 — Officiële bronnen
# Alert bij élke vermelding van GTA VI
# ─────────────────────────────────────────────
TIER1_FEEDS = [
    ("Rockstar Official", "https://www.rockstargames.com/feeds/news"),
    ("Take-Two IR",       "https://ir.take2games.com/rss/news-releases.xml"),
]

# ─────────────────────────────────────────────
# TIER 2 — Vertrouwde game-journalisten
# Alert bij élke vermelding van GTA VI
# ─────────────────────────────────────────────
TIER2_FEEDS = [
    ("VGC",       "https://www.videogameschronicle.com/feed/"),
    ("Eurogamer", "https://www.eurogamer.net/feed"),
]

# ─────────────────────────────────────────────
# TIER 3 — Grote gaming outlets
# Alert ALLEEN bij GTA VI + high-signal woord
# ─────────────────────────────────────────────
TIER3_FEEDS = [
    ("IGN",      "https://feeds.ign.com/ign/all"),
    ("Kotaku",   "https://kotaku.com/rss"),
    ("Gamespot", "https://www.gamespot.com/feeds/news/"),
    ("Polygon",  "https://www.polygon.com/rss/index.xml"),
]

GTA_KEYWORDS = [
    "gta vi", "gta 6", "grand theft auto vi", "grand theft auto 6",
    "lucia", "jason",
]

HIGH_SIGNAL_KEYWORDS = [
    "release date", "launch date", "launch day", "release window",
    "trailer", "gameplay trailer", "official trailer", "gameplay reveal",
    "delay", "delayed", "postponed", "pushed back",
    "pre-order", "preorder", "pre order", "available to buy",
    "esrb", "pegi", "rated",
    "officially announced", "officially confirmed", "officially revealed",
    "playable demo", "open beta", "closed beta",
    "collector's edition", "standard edition", "$",
]

STOCK_TICKER = "TTWO"
ALERT_THRESHOLDS = [3.0, 5.0, 10.0]
STATE_FILE = "monitor_state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"seen_ids": [], "stock_alerts_sent": [], "last_alert_day": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_whatsapp(message):
    if not WHATSAPP_PHONE or not WHATSAPP_APIKEY:
        log("WhatsApp credentials ontbreken!")
        return
    try:
        r = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={"phone": WHATSAPP_PHONE, "text": message, "apikey": WHATSAPP_APIKEY},
            timeout=10,
        )
        log(f"WhatsApp verzonden: {r.status_code}")
    except Exception as e:
        log(f"WhatsApp fout: {e}")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def article_text(entry):
    title   = getattr(entry, "title",   "") or ""
    summary = getattr(entry, "summary", "") or ""
    return (title + " " + summary).lower()


def has_gta_keyword(text):
    return any(kw in text for kw in GTA_KEYWORDS)


def has_high_signal(text):
    return any(kw in text for kw in HIGH_SIGNAL_KEYWORDS)


def check_feeds(state):
    seen   = set(state.get("seen_ids", []))
    alerts = []

    all_feeds = (
        [(name, url, "TIER1") for name, url in TIER1_FEEDS] +
        [(name, url, "TIER2") for name, url in TIER2_FEEDS] +
        [(name, url, "TIER3") for name, url in TIER3_FEEDS]
    )

    for source, url, tier in all_feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                uid = getattr(entry, "id", None) or getattr(entry, "link", None)
                if not uid:
                    uid = hashlib.md5((getattr(entry, "title", "") + url).encode()).hexdigest()

                if uid in seen:
                    continue
                seen.add(uid)

                text = article_text(entry)

                if not has_gta_keyword(text):
                    continue

                if tier == "TIER3" and not has_high_signal(text):
                    continue

                title_str = getattr(entry, "title", "(geen titel)")
                link      = getattr(entry, "link",  "")
                alerts.append((tier, source, title_str, link))
                log(f"[{tier}] {source}: {title_str[:80]}")

        except Exception as e:
            log(f"Feed fout ({source}): {e}")

    state["seen_ids"] = list(seen)[-2000:]
    return alerts


def check_stock(state):
    today = datetime.now().strftime("%Y-%m-%d")

    if state.get("last_alert_day") != today:
        state["stock_alerts_sent"] = []
        state["last_alert_day"] = today

    try:
        info       = yf.Ticker(STOCK_TICKER).fast_info
        current    = info.last_price
        open_price = info.open

        if not current or not open_price or open_price == 0:
            log("TTWO: geen koersdata beschikbaar")
            return

        pct = ((current - open_price) / open_price) * 100
        log(f"TTWO: ${current:.2f} | open ${open_price:.2f} | {pct:+.2f}%")

        sent = state.get("stock_alerts_sent", [])
        for threshold in ALERT_THRESHOLDS:
            key = f"{today}_{threshold}"
            if pct >= threshold and key not in sent:
                msg = (
                    f"TTWO KOERSALERT {pct:+.1f}%\n\n"
                    f"Koers nu:   ${current:.2f}\n"
                    f"Dagopening: ${open_price:.2f}\n\n"
                    f"Check het nieuws — er is waarschijnlijk iets aan de hand."
                )
                send_whatsapp(msg)
                sent.append(key)
                time.sleep(5)

        state["stock_alerts_sent"] = sent

    except Exception as e:
        log(f"Koers fout: {e}")


def main():
    log("=== GTA VI Monitor — GitHub Actions run ===")
    state = load_state()

    alerts = check_feeds(state)
    for tier, source, title, link in alerts:
        emoji = "🔴" if tier == "TIER1" else "🟡" if tier == "TIER2" else "🟢"
        msg = (
            f"{emoji} GTA VI NIEUWS [{tier}]\n\n"
            f"Bron: {source}\n"
            f"Titel: {title}\n\n"
            f"{link}"
        )
        send_whatsapp(msg)
        time.sleep(5)

    check_stock(state)
    save_state(state)
    log("=== Klaar ===")


if __name__ == "__main__":
    main()
