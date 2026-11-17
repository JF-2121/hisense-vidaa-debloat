#!/usr/bin/env python3
"""Fernsteuerung + Kontrolle.

  python scripts/tvctl.py state                  # statetype (remote_launcher, app, input, …)
  python scripts/tvctl.py keys KEY_HOME KEY_RIGHT …   # Tasten senden (0,7 s Abstand)
  python scripts/tvctl.py apps                   # aktuelle App-Liste inkl. isFav (= auf Homescreen)
  python scripts/tvctl.py diff                   # was fehlt gegenüber dem Backup?
  python scripts/tvctl.py launch <appId>         # App per Original-Eintrag aus dem Backup starten
Hinweis: fake_sleep in gettvinfo ist auf manchen Modellen unzuverlässig – statetype nutzen.
"""
import json, sys, time
from pathlib import Path
from common import ROOT, connect, log


def latest_backup_apps():
    b = sorted(ROOT.glob("backup_*/applist_original.json"))
    return json.loads(b[-1].read_text()) if b else []


def main(a):
    cmd = a[0] if a else "state"
    tv = connect()
    if cmd == "state":
        s = tv.get_state(timeout=5); print(json.dumps(s, ensure_ascii=False)); log(cmd=cmd, state=s)
    elif cmd == "keys":
        for k in a[1:]:
            tv.send_key(k); time.sleep(0.7)
        time.sleep(0.8); s = tv.get_state(timeout=3)
        print("gesendet:", " ".join(a[1:]), "| state:", json.dumps(s, ensure_ascii=False)); log(cmd=cmd, keys=a[1:], state=s)
    elif cmd == "apps":
        now = tv.get_apps(timeout=10) or []
        for x in now:
            print(f"{x['appId']:>5}  {x['name']:<35} isFav={x.get('isFav')} uninstallable={x.get('isunInstalled')}")
        print(len(now), "Apps")
    elif cmd == "diff":
        ids = {str(x["appId"]) for x in (tv.get_apps(timeout=10) or [])}
        miss = [x["name"] for x in latest_backup_apps() if str(x["appId"]) not in ids]
        print(f"{len(ids)} installiert · {len(miss)} entfernt: {miss}"); log(cmd=cmd, ids=sorted(ids))
    elif cmd == "launch":
        app = next((x for x in latest_backup_apps() if str(x["appId"]) == a[1]), None)
        app = app and {k: app[k] for k in ("appId", "name", "url")}
        tv.launch_app(app or a[1]); time.sleep(5); print(tv.get_state(timeout=4))
    tv.disconnect()


if __name__ == "__main__":
    main(sys.argv[1:])
