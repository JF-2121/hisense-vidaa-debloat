# Hisense VIDAA Debloat: ohne Werbung, auf das Nötigste reduziert, umkehrbar

🇬🇧 [English version](README.en.md)

Mit diesem Repo räumst du einen Hisense-TV mit **VIDAA OS** vom Mac aus auf, ohne Root, ADB oder SSH:

- **Keine Werbung auf dem Homescreen:** Werbebanner, „Empfohlen für dich“ und Feed-Module werden per DNS gesperrt.
- **Hersteller-Telemetrie gesperrt:** Journale, Tracking, A/B-Tests und ACR-Anbieter.
- **Wenige Apps:** Nur die Apps, die du behalten willst (Standard: Netflix, YouTube, Prime Video), plus deine HDMI-Eingänge.
- **Umkehrbar:** Vor jeder Änderung wird der Ausgangszustand gesichert, mit Rollback-Skript.

> Getestet an einem Hisense 43A53FEVS (VIDAA, `transport_protocol=3290`, Stand 2026-11). Menüpfade und Verhalten können je nach Modell und Firmware abweichen. Nutzung auf eigenes Risiko.

## So funktioniert es

| Ebene | Werkzeug |
|---|---|
| Steuerung und Inventar | Lokale **VIDAA-Remote-API** (MQTT über TLS, Port `36669`, PIN-Pairing) mit der Bibliothek [`vidaa-control`](https://github.com/tombabolewski/vidaa-control) |
| Werbung und Tracking | **DNS-Filter** (NextDNS oder AdGuard Home) mit eigener Sperr- und Freigabeliste |
| Apps und Einstellungen | Fernbedienung, anhand der Menüpfade aus dem Backup |

VIDAA ist ein geschlossenes System. Einen eigenen Launcher zu installieren oder Systemapps zu deaktivieren wie bei Android TV ist **nicht** möglich.

---

## Voraussetzungen

- Mac oder Linux mit Python ≥ 3.9 im **gleichen Netz** wie der TV
- Ein DNS-Filter: ein kostenloses [NextDNS](https://nextdns.io)-Konto **oder** ein eigenes AdGuard Home bzw. Pi-hole
- Ein USB-Stick, falls du Antenne oder Kabel nutzt (Export der Senderliste)

## Schritt 0: Installation

```bash
git clone <dieses-repo> && cd <dieses-repo>
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export VIDAA_TV_IP=192.168.x.y        # IP des TVs: FRITZ!Box → Heimnetz → Netzwerk
export VIDAA_KEEP=1,2,3               # appIds, die bleiben (1 Netflix, 2 Prime Video, 3 YouTube)
```

Den TV findest du im Netz mit `nc -z $VIDAA_TV_IP 36669 && echo offen`. Ist Port 36669 geschlossen, unterstützt dein Modell die Remote-API nicht.

## Schritt 1: Pairing und Inventar (ändert nichts)

```bash
.venv/bin/python scripts/pair.py
```

1. Der TV muss eingeschaltet sein. Er zeigt eine **4-stellige PIN**, die du im Terminal eintippst.
2. Meldet das Skript `illegal authNum`, war die PIN abgelaufen. Skript neu starten und die neue PIN nehmen.
3. Danach liegen in `.state/inventory/` die Dateien `tv_info`, `device_info`, `capability`, `sources` und `applist`.

Das Token gilt einige Tage und erneuert sich danach automatisch. Alle privaten Daten liegen in `.state/`, und dieser Ordner wird nie committet.

## Schritt 2: Backup und Rollback-Manifest

```bash
.venv/bin/python scripts/backup.py
```

Erzeugt `backup_<DATUM>/` mit:
- den Original-JSONs
- `rollback_state.json`: jede geplante Änderung mit Menüpfad und Vorher-/Nachher-Wert
- `ROLLBACK.md`: dieselben Änderungen als Tabelle
- `SHA256SUMS`: Prüfsummen aller Dateien

**Antenne oder Kabel?** Vorher die Senderliste auf USB exportieren. Den Pfad findest du unter Einstellungen → Sender; er hängt von Modell und Firmware ab.

## Schritt 3: Apps aufräumen (vor der DNS-Sperre)

> **Wichtig: Diese Reihenfolge einhalten.** Bei aktiver DNS-Sperre bietet VIDAA kein Bearbeiten-Menü für die Leiste an.

Mit der Fernbedienung: **Home → App markieren → OK lang drücken (oder Menü-Taste) →**
- **„Deinstallieren“** für alle Apps, die `rollback_state.json` als `app_uninstall` führt
- **„Entfernen“** für Systemapps (`homebar_remove`), sofern angeboten
- **„Verschieben“** für die Reihenfolge

Danach prüfen:

```bash
.venv/bin/python scripts/tvctl.py diff    # was ist weg
.venv/bin/python scripts/tvctl.py apps    # isFav=True heißt: liegt auf dem Homescreen
```

⚠️ Pass bei den Apps auf, die du behalten willst. Ist eine versehentlich aus der Leiste verschwunden, startest du sie trotzdem mit `tvctl.py launch <appId>`.

## Schritt 4: Einstellungen am TV

Den Vorher-Wert vor jedem Umschalten **ablesen und in `rollback_state.json` eintragen**.

| Was | Menüpfad (VIDAA, deutsch) | Neu |
|---|---|---|
| ACR | Einstellungen → System → Erweiterte Einstellungen → Einstellungen für erweitertes Sehen → Automatische Inhaltserkennung | Aus |
| Personalisierte Werbung | Einstellungen → System → Erweiterte Einstellungen → Personalisierte Werbung | Aus |
| Datenfreigaben | Einstellungen → Support → Haftungsausschluss und Datenschutz | optionale Häkchen aus |
| Sprachassistent | Einstellungen → System → Sprachdienst → VIDAA Voice / Alexa | Aus |
| HbbTV | Einstellungen → Sender → HbbTV-Einstellungen | Aus |
| App-Updates | APP STORE → Einstellungen → Automatische Aktualisierung | Aus |
| HDMI-CEC | Einstellungen → System → HDMI & CEC → CEC-Steuerung | An |

## Schritt 5: DNS-Sperre (NextDNS)

1. Auf nextdns.io ein **Profil anlegen**.
2. Unter **Denylist** jede Zeile aus [`dns/denylist.txt`](dns/denylist.txt) eintragen. Das sperrt auch alle Unterdomains.
3. Unter **Allowlist** jede Zeile aus [`dns/allowlist.txt`](dns/allowlist.txt) eintragen. Freigaben haben Vorrang.
   ⚠️ **`vidaa-base-auth-eu.vidaahub.com` muss frei bleiben.** Ohne diese Geräteanmeldung startet YouTube auf VIDAA nicht mehr, sobald das zwischengespeicherte Token abgelaufen ist (nach etwa einem Tag oder einem Neustart). Netflix ist davon nicht betroffen.
   Hinweis: `googlevideo.com` gehört **nicht** auf die Allowlist, sonst hebt sie die Sperre der YouTube-Marktforschung (`eligibility-panelresearch.googlevideo.com`) auf.
4. Unter **Einrichtung → Verknüpfte IP** auf **„IP verknüpfen“** klicken und darunter einen **DDNS-Hostnamen** eintragen, z. B. deine MyFRITZ!-Adresse.
5. Unter **Einstellungen → Protokolle** das Protokoll einschalten, sonst kannst du nichts prüfen.
6. Am TV unter Einstellungen → Netzwerk → Netzwerkkonfiguration → DNS **Manuell** wählen und beide NextDNS-IPv4-Adressen eintragen. **Keinen** ungefilterten DNS als zweiten Server angeben.
7. TV **per Netzstecker** neu starten.

Prüfen, vom selben Netz aus:

```bash
sh dns/verify_dns.sh <NextDNS-IP-1>
sh dns/verify_dns.sh <NextDNS-IP-2>
```

Erwartet wird `OK` für alle Zeilen. `WARN` steht für einen einzelnen Timeout und ist unkritisch. Zusätzlich sollten im NextDNS-Protokoll **rote** Einträge zu `vidaahub.com` und `hismarttv.com` auftauchen.

- **Prime-Video-Oberfläche hat Lücken?** Die Einträge aus [`dns/allowlist_optional_prime_ui.txt`](dns/allowlist_optional_prime_ui.txt) zusätzlich freigeben. „Empfohlen für dich“ kann damit allerdings zurückkommen.
- **AdGuard Home statt NextDNS:** [`dns/adguardhome_rules.txt`](dns/adguardhome_rules.txt) verwenden und `<TV-MAC>` durch die MAC des TVs ersetzen.

## Rollback

```bash
.venv/bin/python scripts/rollback.py status     # was fehlt gegenüber dem Backup
.venv/bin/python scripts/rollback.py appstore   # App Store öffnen + Liste zum Neuinstallieren
.venv/bin/python scripts/rollback.py settings   # geführter Rückbau der Einstellungen
.venv/bin/python scripts/rollback.py factory    # Werksreset-Pfad
```

Vor dem Neuinstallieren `hismarttv.com` im DNS-Filter freigeben. Die DNS-Sperre selbst hebst du auf, indem du am TV den DNS wieder auf **Automatisch** stellst.

## Wartung

- **Firmware-Update:** In NextDNS `hismarttv.com` vorübergehend von der Sperrliste nehmen und danach wieder eintragen.
- **NextDNS-Kontingent:** Nach etwa einer Woche unter **Analysen** nachrechnen. Der Gratistarif hat 300.000 Anfragen pro Monat; danach wird zwar weiter aufgelöst, aber nicht mehr gefiltert.
- **Schneller wird der TV durch:** ACR und Sprachassistent aus, weniger Kacheln, gelegentlich ein Neustart per Stecker. Bildeinstellungen bringen dafür nichts.

## Dokumentation

- [`docs/TRACKER_REPORT.md`](docs/TRACKER_REPORT.md): welche Domains wofür da sind, mit Belegstärke
- [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md): Stolperfallen aus dem Praxistest
- [`examples/`](examples/): maskierte Beispielantworten der API

## Quellen

[vidaa-control](https://github.com/tombabolewski/vidaa-control) · [pyvidaa Protokollanalyse](https://github.com/warrenrees/pyvidaa) · [cleanyour.tv](https://cleanyour.tv/not-android) · [ipanalytics VIDAA-Blocklist](https://github.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist) · [Okazakee tv-dns-blocklist](https://github.com/Okazakee/tv-dns-blocklist)

Kein offizielles Hisense- oder VIDAA-Projekt.
