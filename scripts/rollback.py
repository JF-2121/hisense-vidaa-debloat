#!/usr/bin/env python3
"""Rollback.

  python scripts/rollback.py status            # Ist vs. Backup: fehlende Apps, erledigte Änderungen
  python scripts/rollback.py appstore          # öffnet APP STORE + Liste neu zu installierender Apps
  python scripts/rollback.py launch <appId|all>
  python scripts/rollback.py settings          # geführter Rückbau geänderter Einstellungen
  python scripts/rollback.py factory           # Werksreset-Pfad
Spielt nie blind Tastenfolgen ab; jeder Schritt wird bestätigt.
Achtung: Wenn hismarttv.com per DNS geblockt ist, funktioniert der APP STORE nicht –
vorher im DNS-Filter freigeben.
"""
import json, sys, time
from common import ROOT, connect

BK = sorted(ROOT.glob("backup_*/"))
if not BK:
    sys.exit("Kein backup_*/ gefunden – erst python scripts/backup.py")
B = BK[-1]
STATE = json.loads((B / "rollback_state.json").read_text())
ORIG = json.loads((B / "applist_original.json").read_text())
ask = lambda m: input(f"{m} [j/N] ").strip().lower() in ("j", "ja", "y")


def missing(tv):
    now = {str(a["appId"]) for a in (tv.get_apps(timeout=10) or [])}
    return [a for a in ORIG if str(a["appId"]) not in now]


def main(a):
    cmd = a[0] if a else "status"
    if cmd == "factory":
        print("Einstellungen → Support → Selbstdiagnose → Zurücksetzen (Pfad je nach Firmware). Danach neu pairen."); return
    tv = connect()
    if cmd == "status":
        miss = missing(tv)
        print(f"Backup: {B.name} · Apps im Original: {len(ORIG)} · fehlen: {len(miss)}")
        for x in miss: print("  -", x["name"], f"(appId {x['appId']})")
    elif cmd == "appstore":
        miss = missing(tv)
        tv.launch_app({"appId": "164", "name": "APP STORE", "url": "vidaa-store"})
        print("APP STORE geöffnet – neu installieren:"); [print("  -", x["name"]) for x in miss]
    elif cmd == "launch":
        tg = missing(tv) if a[1] == "all" else [x for x in ORIG if str(x["appId"]) == a[1]]
        for x in tg:
            if ask(f"{x['name']} starten?"):
                tv.launch_app({"appId": x["appId"], "name": x["name"], "url": x["url"]}); time.sleep(4)
    elif cmd == "settings":
        for c in reversed([c for c in STATE["changes"] if c["type"] == "setting" and c["done"]]):
            print(f"\n▶ {c['name']}\n  Menü: {c['menu']}\n  Jetzt: {c['after']} → zurück auf: {c['before']}")
            if ask("  Einstellungsmenü öffnen?"):
                tv.send_key("KEY_HOME"); time.sleep(1); tv.send_key("KEY_MENU")
            input("  Wert zurückstellen, dann Enter …")
    tv.disconnect()


if __name__ == "__main__":
    main(sys.argv[1:])
