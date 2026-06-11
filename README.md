# GTA VI Monitor 🎮📈

Automatische nieuwsmonitor die GTA VI-aankondigingen bijhoudt en WhatsApp-alerts stuurt — zodat je TTWO-aandelen kunt handelen vóórdat de markt reageert.

Draait gratis via GitHub Actions, elke 5 minuten, 24/7.

---

## Hoe het werkt

Het script controleert RSS-feeds van gaming-nieuwssites op GTA VI-gerelateerde artikelen. Bij een treffer krijg je direct een WhatsApp-bericht via de CallMeBot API. Daarnaast wordt de TTWO-koers bewaakt en ontvang je een alert zodra de koers +3%, +5% of +10% boven de dagopening uitkomt.

Om ruis te vermijden werkt het systeem met drie tiers:

- **Tier 1** (Rockstar Official, Take-Two IR) — alert bij élke vermelding van GTA VI
- **Tier 2** (VGC, Eurogamer) — alert bij élke vermelding van GTA VI
- **Tier 3** (IGN, Kotaku, Gamespot, Polygon) — alert alleen bij GTA VI + een high-signal woord (releasedatum, trailer, delay, pre-order, etc.)

---

## Setup

### 1. Secrets instellen

Ga naar **Settings → Secrets and variables → Actions** en voeg toe:

| Secret | Waarde |
|---|---|
| `WHATSAPP_PHONE` | Jouw telefoonnummer (zonder +, bijv. `31612345678`) |
| `WHATSAPP_APIKEY` | Jouw CallMeBot API key |

Nog geen CallMeBot API key? Stuur `I allow callmebot to send me messages` als WhatsApp-bericht naar **+34 623 78 64 49** en je ontvangt automatisch een key.

### 2. Actions inschakelen

Ga naar **Actions** en klik op **Enable workflows** als dat nog niet het geval is.

### 3. Eerste test

Ga naar **Actions → GTA VI Monitor → Run workflow** om hem handmatig te starten. Controleer of je een WhatsApp-bericht ontvangt.

Daarna draait hij automatisch elke 5 minuten.

---

## Bestanden

| Bestand | Omschrijving |
|---|---|
| `gta_monitor.py` | Hoofdscript — controleert feeds en koers |
| `.github/workflows/monitor.yml` | GitHub Actions workflow |
| `requirements.txt` | Python dependencies |
| `monitor_state.json` | State (al geziene artikelen, verstuurde alerts) — wordt automatisch bijgewerkt |

---

## Koersalerts TTWO

| Alert | Trigger |
|---|---|
| 🟡 +3% | Koers is 3% boven dagopening |
| 🟠 +5% | Koers is 5% boven dagopening |
| 🔴 +10% | Koers is 10% boven dagopening |

Elke drempelwaarde wordt maximaal één keer per dag gemeld.
