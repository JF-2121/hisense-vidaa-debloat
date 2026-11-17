# Hisense VIDAA Debloat – ad-free, minimal, reversible

🇩🇪 [Deutsche Version](README.md)

Clean up a Hisense TV running **VIDAA OS** from a Mac or Linux machine, with no root, ADB or SSH:

- **No ads on the home screen:** the ad banner, "Recommended for you" and the feed modules are blocked by DNS.
- **Manufacturer telemetry blocked:** journals, tracking, A/B tests and ACR providers.
- **Only the apps you want:** by default Netflix, YouTube and Prime Video, plus your HDMI inputs.
- **Reversible:** the starting state is backed up before any change, and there is a rollback script.

> Tested on a Hisense 43A53FEVS (VIDAA, `transport_protocol=3290`, as of 2026-11). Menu paths and behaviour can differ by model and firmware. Use at your own risk.

## How it works

| Layer | Tool |
|---|---|
| Control & inventory | The local **VIDAA remote API** (MQTT over TLS, port `36669`, PIN pairing) via the [`vidaa-control`](https://github.com/tombabolewski/vidaa-control) library |
| Ads & tracking | A **DNS filter** (NextDNS or AdGuard Home) with your own denylist and allowlist |
| Apps & settings | Your remote, following the menu paths stored in the backup |

VIDAA is a closed system. Unlike Android TV, you **cannot** install your own launcher or disable system apps.

---

## Requirements

- A Mac or Linux machine with Python ≥ 3.9 on the **same network** as the TV
- A DNS filter: a free [NextDNS](https://nextdns.io) account **or** your own AdGuard Home / Pi-hole
- A USB stick, if you use antenna or cable TV (to export the channel list)

## Step 0: Install

```bash
git clone <this-repo> && cd <this-repo>
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export VIDAA_TV_IP=192.168.x.y        # your TV's IP: see your router's device list
export VIDAA_KEEP=1,2,3               # appIds to keep (1 Netflix, 2 Prime Video, 3 YouTube)
```

To find the TV on the network, run `nc -z $VIDAA_TV_IP 36669 && echo open`. If port 36669 is closed, your model does not support the remote API.

## Step 1: Pairing and inventory (changes nothing)

```bash
.venv/bin/python scripts/pair.py
```

1. The TV must be switched on. It shows a **4-digit PIN**; type it into the terminal.
2. If the script reports `illegal authNum`, the PIN had expired. Run the script again and use the new PIN.
3. The script then saves `tv_info`, `device_info`, `capability`, `sources` and `applist` to `.state/inventory/`.

The token lasts a few days and then renews itself automatically. All private data lives in `.state/`, which is never committed.

## Step 2: Backup and rollback manifest

```bash
.venv/bin/python scripts/backup.py
```

This creates `backup_<DATE>/` with:
- the original JSON files
- `rollback_state.json`: every planned change with its menu path and before/after value
- `ROLLBACK.md`: the same changes as a table
- `SHA256SUMS`: checksums of all files

**Antenna or cable TV?** Export the channel list to USB first. You'll find it under Settings → Channel; the exact path depends on model and firmware.

## Step 3: Clean up apps (before the DNS block)

> **Important: keep this order.** While the DNS block is active, VIDAA does not offer an edit menu for the app bar.

With your remote: **Home → highlight the app → long-press OK (or the Menu key) →**
- **"Uninstall"** for every app listed as `app_uninstall` in `rollback_state.json`
- **"Remove"** for system apps (`homebar_remove`), if offered
- **"Move"** to set the order

Then check:

```bash
.venv/bin/python scripts/tvctl.py diff    # what is gone
.venv/bin/python scripts/tvctl.py apps    # isFav=True means: on the home screen
```

⚠️ Be careful with the apps you want to keep. If one has accidentally disappeared from the app bar, you can still start it with `tvctl.py launch <appId>`.

## Step 4: TV settings

**Note the current value before you change anything, and record it in `rollback_state.json`.**

| What | Menu path (English UI; German labels in brackets) | New |
|---|---|---|
| ACR | Settings → System → Advanced Settings → Enhanced Viewing Settings → Automatic Content Recognition (*Einstellungen für erweitertes Sehen → Automatische Inhaltserkennung*) | Off |
| Personalised ads | Settings → System → Advanced Settings → Personalised Ads (*Personalisierte Werbung*) | Off |
| Data consents | Settings → Support → Disclaimer and Privacy (*Haftungsausschluss und Datenschutz*) | optional boxes off |
| Voice assistant | Settings → System → Voice Service → VIDAA Voice / Alexa (*Sprachdienst*) | Off |
| HbbTV | Settings → Channel → HbbTV Settings (*Sender → HbbTV-Einstellungen*) | Off |
| App updates | APP STORE → Settings → Auto Update (*Automatische Aktualisierung*) | Off |
| HDMI-CEC | Settings → System → HDMI & CEC → CEC Control (*CEC-Steuerung*) | On |

## Step 5: DNS block (NextDNS)

1. **Create a profile** at nextdns.io.
2. Under **Denylist**, add each line of [`dns/denylist.txt`](dns/denylist.txt). This also blocks all subdomains.
3. Under **Allowlist**, add each line of [`dns/allowlist.txt`](dns/allowlist.txt). The allowlist overrides the denylist.
4. Under **Setup → Linked IP**, click **"Link IP"**, and below it add a **DDNS hostname**, for example your router's dynamic DNS name.
5. Turn on logging under **Settings → Logs**, otherwise you can't check anything.
6. On the TV, go to Settings → Network → Network Configuration → DNS, choose **Manual** and enter both NextDNS IPv4 addresses. **Do not** add an unfiltered DNS as the second server.
7. Restart the TV **by unplugging it**.

Check from the same network:

```bash
sh dns/verify_dns.sh <NextDNS-IP-1>
sh dns/verify_dns.sh <NextDNS-IP-2>
```

Every line should say `OK`. `WARN` means a single timeout and is not a problem. The NextDNS log should also show **red** (blocked) entries for `vidaahub.com` and `hismarttv.com`.

- **Gaps in the Prime Video UI?** Also allow the entries in [`dns/allowlist_optional_prime_ui.txt`](dns/allowlist_optional_prime_ui.txt). "Recommended for you" may come back as a result.
- **AdGuard Home instead of NextDNS:** use [`dns/adguardhome_rules.txt`](dns/adguardhome_rules.txt) and replace `<TV-MAC>` with your TV's MAC address.

> The shell scripts print German status words: `GEBLOCKT` = blocked, `frei` = resolved, `FEHLER` = error.

## Rollback

```bash
.venv/bin/python scripts/rollback.py status     # what is missing compared to the backup
.venv/bin/python scripts/rollback.py appstore   # opens the App Store + list of apps to reinstall
.venv/bin/python scripts/rollback.py settings   # guided reset of changed settings
.venv/bin/python scripts/rollback.py factory    # factory reset path
```

Before reinstalling apps, allow `hismarttv.com` in your DNS filter. To lift the DNS block itself, set the TV's DNS back to **Automatic**.

## Maintenance

- **Firmware update:** remove `hismarttv.com` from the NextDNS denylist for the update, then add it back.
- **NextDNS quota:** check **Analytics** after about a week. The free plan allows 300,000 queries a month; after that, NextDNS keeps resolving but stops filtering.
- **To make the TV feel faster:** turn off ACR and the voice assistant, keep fewer tiles, and unplug it now and then. Picture settings (MEMC, noise reduction) don't help with speed.

## Documentation

- [`docs/TRACKER_REPORT.md`](docs/TRACKER_REPORT.md): which domains do what, with how well each is evidenced (German)
- [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md): pitfalls from real-world testing (German)
- [`examples/`](examples/): masked sample API responses

## Sources

[vidaa-control](https://github.com/tombabolewski/vidaa-control) · [pyvidaa protocol analysis](https://github.com/warrenrees/pyvidaa) · [cleanyour.tv](https://cleanyour.tv/not-android) · [ipanalytics VIDAA blocklist](https://github.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist) · [Okazakee tv-dns-blocklist](https://github.com/Okazakee/tv-dns-blocklist)

Not an official Hisense or VIDAA project.
