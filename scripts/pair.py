#!/usr/bin/env python3
"""Schritt 1: PIN-Pairing + rein lesendes Inventar. Ändert am TV nichts.

  python scripts/pair.py
Beim ersten Lauf zeigt der TV eine 4-stellige PIN – im Terminal eintippen.
Danach (oder wenn schon gepairt) werden gelesen: gettvinfo, getdeviceinfo, capability,
gettvstate, sourcelist, applist → .state/inventory/*.json
Hinweis: Nach dem Pairing verbindet das Skript neu – Abfragen beantwortet der TV
erst in einer Session, die mit dem ausgestellten Token aufgebaut wurde.
"""
import json, sys, time
from common import INVENTORY, connect, make_client, log

INVENTORY.mkdir(exist_ok=True)


def pair():
    tv = make_client()
    if not tv.connect(timeout=15):
        sys.exit("MQTT-Verbindung fehlgeschlagen")
    if tv.is_authenticated():
        tv.disconnect(); return
    tv.start_pairing()
    pin = input("PIN vom TV-Bildschirm: ").strip()
    if not tv.authenticate(pin, timeout=15):
        sys.exit("PIN abgelehnt („illegal authNum“) – Skript neu starten, neue PIN verwenden.")
    time.sleep(3)  # tokenissuance abwarten
    tv.disconnect()
    log(cmd="pair", ok=True)
    print("Gepairt.")


def inventory():
    tv = connect()
    for name, fn in [("tv_info", tv.get_tv_info), ("device_info", tv.get_device_info),
                     ("capability", tv.get_capability), ("tv_state", tv.get_state),
                     ("sources", tv.get_sources), ("applist", tv.get_apps)]:
        data = fn(timeout=10)
        (INVENTORY / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  {name}.json {'ok' if data else 'LEER'}")
    tv.disconnect()


if __name__ == "__main__":
    pair()
    inventory()
