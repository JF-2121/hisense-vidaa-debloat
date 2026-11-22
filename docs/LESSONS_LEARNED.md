# Erfahrungen aus dem ersten Durchlauf

Getestet an einem Hisense **43A53FEVS** (MediaTek MTK9602, Firmware `V0006.09.09F`, `os_t.baseui.2.0`, `transport_protocol=3290`).

## Remote-API (MQTT, Port 36669)

| Beobachtung | Konsequenz |
|---|---|
| Die alten Zugangsdaten `hisenseservice`/`multimqttservice` scheitern mit einem TLS-Handshake-Fehler. | Ab Protokoll 3290 braucht es Client-Zertifikat, dynamische Zugangsdaten und eine PIN. Die Bibliothek `vidaa-control` liefert alles mit. |
| Antwort auf eine PIN `{"result":100,"info":"illegal authNum!!"}` | Die PIN ist falsch oder abgelaufen. Skript neu starten und die **neue** PIN eingeben. |
| Direkt nach dem Pairing bleiben alle Abfragen leer. | Abfragen beantwortet der TV erst nach einer **neuen Verbindung mit dem Token**. `pair.py` macht das automatisch. |
| `fake_sleep` in `gettvinfo` steht auch bei eingeschaltetem TV auf 1. | Unzuverlässig. Stattdessen `statetype` auswerten (`remote_launcher`, `app`, `input`, `remote_setting`). |
| Es gibt **keinen** API-Befehl zum Deinstallieren oder zum Bearbeiten der Leiste. | Das geht nur per Fernbedienung. Ob es geklappt hat, zeigt `applist` (Feld `isFav` = liegt auf dem Homescreen). |
| `KEY_OK_LONG_PRESS` und `KEY_MENU` per API öffnen kein Bearbeiten-Menü. | Siehe nächster Abschnitt. |
| Der TV liefert kein Bild (`screen_capture_supported: 0`). | Tasten nie blind mit OK bestätigen. Ein Foto oder eine Rückmeldung vom Bildschirm ist Pflicht. |
| `launchapp` mit dem Originaleintrag (`appId`, `name`, `url`) startet eine App auch dann, wenn sie nicht mehr in der App-Liste steht. | Damit lassen sich versehentlich ausgeblendete Apps wie Prime Video weiter starten: `tvctl.py launch 2`. |

## DNS-Sperre

- `vidaahub.com` und `hismarttv.com` komplett zu sperren und nur `img.vidaahub.com` freizugeben, funktioniert: **Banner und Feed-Module sind weg, Netflix und YouTube laufen**.
- **Ausnahme `vidaa-base-auth-eu.vidaahub.com`:** Ist sie gesperrt, startet YouTube zunächst noch mit dem zwischengespeicherten Token. Nach etwa einem Tag oder einem Neustart lässt sich YouTube dann nicht mehr öffnen. Im NextDNS-Protokoll ist sie beim YouTube-Start die einzige geblockte Domain. Die Freigabe behebt das, und die Werbe-Module bleiben trotzdem gesperrt.
- **`eligibility-panelresearch.googlevideo.com` NICHT sperren.** Das ist die YouTube-Marktforschung. Gesperrt lief YouTube noch zwei Tage weiter (Cache) und startete dann nicht mehr; die Freigabe hat es sofort behoben. `googlevideo.com` steht deshalb komplett auf der Allowlist.
- **`auth-eu.hismarttv.com` freigeben (Ausfall 3, 22.11.):** YouTube meldete „Netzwerkfehler“, während Netflix lief; die Uhrzeit stimmte. Die Adresse zeigt auf denselben Server wie `vidaa-base-auth-eu.vidaahub.com` und ist offenbar eine zweite Adresse der Geräteanmeldung. Gesperrt war sie doppelt: durch `hismarttv.com` in der Denylist **und** durch die Datenschutz-Liste in NextDNS. Deshalb half es auch nicht, `hismarttv.com` von der Denylist zu nehmen. Erst die Allowlist-Freigabe hat YouTube repariert.
- **Versteckte Sperren:** Datenschutz-Listen in NextDNS sperren auch ohne eigene Einträge. Ob eine Sperre aus deiner Liste kommt, erkennst du am Vergleich mit `dig @1.1.1.1 <domain>`: Liefert Cloudflare eine IP und NextDNS `0.0.0.0`, wird gesperrt; steht die Domain auf keiner eigenen Liste, kommt die Sperre aus einer NextDNS-Liste.
- **Muster aller drei Ausfälle:** Die Sperre wirkt erst, wenn der Cache abläuft (1–2 Tage oder ein Neustart). Ein Test direkt nach einer Änderung reicht nicht. Ablauf für Änderungen: siehe README, Abschnitt „Änderungen am DNS-Filter ohne Ausfall“.
- Nebenwirkung: Bei aktiver Sperre fehlt das **Bearbeiten-Menü der Leiste**. Systemapps lassen sich dann nicht entfernen. Vermutete Ursache: Die Launcher-Cloud (`api-launcher-*.hismarttv.com`) und die Anmeldung (`vidaa-base-auth-eu.vidaahub.com`) sind nicht erreichbar. **Darum zuerst die Leiste aufräumen und erst danach die DNS-Sperre aktivieren.**
- Auch App Store, Firmware-Updates und VIDAA-Konto funktionieren nicht, solange `hismarttv.com` gesperrt ist. Für ein Update vorübergehend entsperren.
- **Keinen ungefilterten zweiten DNS** wie `94.140.14.14` eintragen. Der TV fragt beide Server parallel an, ein Teil der Werbung käme durch.
- NextDNS „Verknüpfte IP“: Ohne **DDNS** (z. B. MyFRITZ!-Adresse) hört die Filterung nach einem Wechsel der öffentlichen IP unbemerkt auf.
- NextDNS-Gratistarif: 300.000 Anfragen pro Monat. Ein TV mit gesperrter Anmeldung wiederholt seine Anfragen oft. Nach einer Woche unter **Analysen** nachrechnen, ob das reicht.

## Leistung

- Bildverbesserungen wie MEMC, dynamischer Kontrast und Rauschreduzierung laufen auf eigener Bild-Hardware. Abschalten macht die Oberfläche **nicht** schneller.
- Spürbar helfen: ACR aus, Sprachassistent aus, weniger Kacheln in der Leiste, gelegentlich ein Neustart per Netzstecker.
- Der größte Gewinn bei einem Einsteiger-Chip ist ein externer Streaming-Stick an HDMI.
