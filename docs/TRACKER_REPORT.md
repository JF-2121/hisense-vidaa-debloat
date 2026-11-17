# Tracker-Report – Hisense 43A53FEVS (Beispielgerät)

Stand: 2026-11 · Firmware `V0006.09.09F.P0930` · `os_t.baseui.2.0`

## Methode & Aussagekraft

| Quelle | Status |
|---|---|
| Live-Mitschnitt `tv_capture.pcap` (DNS + TLS-SNI) | **nicht vorhanden** → kein Live-Nachweis |
| `phase1_inventory/applist.json` (45 Apps, 34 Hosts) | ausgewertet – **auf diesem TV belegt** |
| Community-Analysen VIDAA (cleanyour.tv, ipanalytics, Okazakee) | abgeglichen – **für VIDAA dokumentiert, auf diesem TV unbelegt** |

Konfidenz-Spalte: **B** = auf diesem TV belegt · **D** = für VIDAA in ≥1 Quelle dokumentiert · **M** = Muster/Ableitung, ungeprüft.
Live-Bestätigung erfolgt in Phase 3 über das Query-Log des DNS-Filters (zeigt jede Anfrage des TVs).

---

## 1. ACR / Screen-Tracking (Bildinhalts-Erkennung)

| Host / Muster | Zweck | Konf. | Maßnahme |
|---|---|---|---|
| — (kein VIDAA-ACR-Host öffentlich dokumentiert) | Hisense „Erweitertes Sehen / Automatische Inhaltserkennung“ | – | **Primär per Menü abschalten** (Phase 3.2) |
| `*.samba.tv`, `*.alphonso.tv`, `*.tvinteractive.tv` | ACR-Drittanbieter anderer Marken | M | vorsorglich blocken (kein Kollateralschaden) |
| `*acr*.vidaahub.com`, `*acr*.hismarttv.com` | Namensmuster | M | vorsorglich blocken, im DNS-Log prüfen |

`tv_info.json`: `screen_capture_supported: 0`, `audio_capture_supported: 0` – das betrifft nur die Remote-API, **nicht** ACR. Ob ACR auf diesem DE-Modell überhaupt angeboten wird, zeigt das Menü.

## 2. Werbung / Homescreen-Feeds

| Host | Zweck | Konf. | Maßnahme |
|---|---|---|---|
| `tvmodules-vidaa.vidaahub.com` | Hostet **V Home**, **Public value**, **VIDAA Art** (Feed-/Promo-Module) | **B** | **BLOCK** |
| `rsc-ads.vidaahub.com`, `rpt-ads*.vidaahub.com` | Werbeauslieferung / Impression-Reporting | D | **BLOCK** |
| `rpt-mntz-azure.vidaahub.com`, `monetization-*.vidaahub.com` | Monetarisierungs-Reporting | D | **BLOCK** |
| `recommend-ui.vidaahub.com` | Empfehlungs-Reihen (evtl. auch Kachel-Artwork) | D | BLOCK, Icons prüfen |
| `recommend-ui-eu.vidaahub.com`, `detail-ui-eu.vidaahub.com`, `content-recommendation.hismarttv.com`, `api-recommendation.hismarttv.com`, `api-recommendation-eu.hismarttv.com`, `api-recommendation-em.hismarttv.com` | Empfehlungen | D | ⚠️ **NICHT blocken** – laut ipanalytics bricht damit die **Prime-Video-UI** auf VIDAA |
| `vidaa-free` / „Vod On Demand“, „TV Channels▶“ (`vidaa-plus`) | FAST-Kanäle mit Werbeunterbrechungen | B | aus Leiste entfernen |

## 3. Hersteller-Telemetrie

| Host / Muster | Zweck | Konf. | Maßnahme |
|---|---|---|---|
| `ter-jrnl-*.vidaahub.com`, `exc-jrnl-*.vidaahub.com`, `policy-jrnl-*.vidaahub.com` | Telemetrie-Journale je Region | D | **BLOCK** |
| `unified-ter*.vidaahub.com`, `api-logsdk*` | Log-SDK / Ereignis-Upload | D | **BLOCK** |
| `tracking-vss.vidaahub.com` | Tracking | D | **BLOCK** |
| `abtest-tv.vidaahub.com` | A/B-Tests | D | **BLOCK** |
| `api-4know-eu.hismarttv.com` | Suchvorschläge/Voice-Antworten | D | optional (bricht Suche/Voice) |

Hinweis: Der TV puffert geblockte Events und versucht es später erneut → viele geblockte Queries im Log sind normal.

## 4. App-Abhängigkeiten (WHITELIST – nie blocken)

| Zweck | Hosts | Konf. |
|---|---|---|
| Firmware/OTA | `upgrade-eu*`, `ota-tv*` (vidaahub/hismarttv), `api.eu.hismarttv.com`, `api.euro.hismarttv.com` | D |
| Konto/Auth, Launcher, Zeit | `auth-*.hismarttv.com`, `api-launcher-*.hismarttv.com`, `*-launcher.hismarttv.com`, NTP | D |
| App-Icons | `img.vidaahub.com` | **B** |
| Werbe-Opt-out-Einstellungen | `ads-privacy.vidaahub.com`, `rsc-mntz.vidaahub.com` | B/D |
| **Netflix** | `*.netflix.com`, `*.netflix.net`, `*.nflxvideo.net`, `*.nflximg.net`, `*.nflxext.com`, `*.nflxso.net`; lokal Port 9080 (NRDP) | B (Port) |
| **YouTube** | `*.youtube.com`, `*.googlevideo.com`, `*.ytimg.com`, `*.ggpht.com`, `*.googleapis.com`, `accounts.google.com`, `*.gstatic.com` | M |
| **Prime Video** | `*.primevideo.com`, `*.amazonvideo.com`, `*.aiv-cdn.net`, `*.aiv-delivery.net`, `*.media-amazon.com`, `*.ssl-images-amazon.com`, `atv-ps-eu.amazon.com`, `api.amazon.com`, `*.amazon.de` | M |

ARD (`api-portal-v3.netrange.com`) und ZDF (`new-hbbtv.zdf.de`) werden **nicht** gewhitelistet – beide Apps fliegen raus.

## 5. Tracker *innerhalb* der behaltenen Apps

| App | Tracker | Per DNS blockbar? |
|---|---|---|
| YouTube | Pre-/Mid-Roll-Werbung | **Nein** – kommt von denselben Google-Hosts wie das Video. Nur YouTube Premium entfernt sie. |
| Prime Video | Werbung im Stream (seit 2024), `device-metrics-*.amazon.com`, `unagi*.amazon.com` | Werbung nein; Metrik-Hosts ja (geringes Risiko, im Log prüfen) |
| Netflix | `ichnaea*.netflix.com` (Logging) | Technisch ja, aber Wiedergabe-Abbrüche gemeldet → **nicht blocken** |

## 6. Drittanbieter-Tracker in den zu löschenden Apps

Der Großteil fremder Ad-Tech kommt aus den FAST-/Werbe-Apps (Pluto TV, Rakuten TV, Haystack TV, Triller TV, Red Bull TV, Vod On Demand …). Wenn wir die 31 Apps deinstallieren und die 9 Systemapps aus der Leiste entfernen, ist diese Quelle weg – dafür braucht es keine DNS-Regel.

## 7. Rechtliche Einordnung („illegale Tracker“)

Ob ein Tracker unzulässig ist, kann ich technisch nicht feststellen. ACR, personalisierte Werbung und nicht notwendige Telemetrie brauchen in DE eine **Einwilligung** (§ 25 TDDDG, Art. 6/7 DSGVO). Hast du bei der Ersteinrichtung „Alle akzeptieren“ gewählt, gibt es formal eine Einwilligung. Du kannst sie jederzeit widerrufen – genau das tun die Menü-Schalter in Phase 3.2. Einen konkreten Rechtsverstoß belegt dieser Report nicht.

## Fazit

- **Belegt auf diesem TV:** Feed-/Promo-Module über `tvmodules-vidaa.vidaahub.com`, 2 FAST-Werbekanal-Apps, 31 werbefinanzierte Drittanbieter-Apps.
- **Für VIDAA dokumentiert, live noch zu bestätigen:** ~12 Telemetrie-/Werbe-Hosts unter `vidaahub.com`.
- **Die größte Falle:** die 6 Empfehlungs-Hosts nicht blocken, sonst bricht die Prime-Video-UI. Außerdem `vidaahub.com` und `hismarttv.com` **nie** komplett blocken, weil OTA, Icons und Login dort mitlaufen.

Quellen: cleanyour.tv/not-android · github.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist · github.com/Okazakee/tv-dns-blocklist
