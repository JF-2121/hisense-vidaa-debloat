#!/usr/bin/env python3
"""Schritt 2: Backup des Ist-Zustands + Rollback-Manifest. Ändert am TV nichts.

  python scripts/backup.py
Erzeugt backup_<DATUM>/ mit: Original-JSONs, rollback_state.json (jede geplante Änderung
Vorher → Nachher mit deutschem Menüpfad), ROLLBACK.md und SHA256SUMS.
Behalten werden die appIds aus VIDAA_KEEP (Standard 1,2,3 = Netflix, Prime Video, YouTube).
"""
import hashlib, json, shutil, time
from common import INVENTORY, KEEP, ROOT, tv_ip

SETTINGS = [
    ("acr", "Einstellungen → System → Erweiterte Einstellungen → Einstellungen für erweitertes Sehen → Automatische Inhaltserkennung", "Aus"),
    ("ads-personal", "Einstellungen → System → Erweiterte Einstellungen → Personalisierte Werbung", "Aus"),
    ("privacy-consents", "Einstellungen → Support → Haftungsausschluss und Datenschutz → Datenfreigabe, Datenschutz und EULA", "optionale Häkchen aus"),
    ("voice", "Einstellungen → System → Sprachdienst → VIDAA Voice / Amazon Alexa (inkl. Freihändig)", "Aus"),
    ("hbbtv", "Einstellungen → Sender → HbbTV-Einstellungen → HbbTV", "Aus"),
    ("app-autoupdate", "APP STORE → Einstellungen → Automatische Aktualisierung", "Aus"),
    ("cec", "Einstellungen → System → HDMI & CEC → CEC-Steuerung", "An"),
    ("dns", "Einstellungen → Netzwerk → Netzwerkkonfiguration → WLAN → Erweiterte Einstellungen → DNS", "Manuell: <DNS-Filter-IPs>"),
]


def main():
    if not (INVENTORY / "applist.json").exists():
        raise SystemExit("Erst python scripts/pair.py ausführen.")
    B = ROOT / f"backup_{time.strftime('%Y-%m-%d')}"
    (B / "raw").mkdir(parents=True, exist_ok=True)
    m = {"applist.json": "applist_original.json", "sources.json": "sources_original.json"}
    for f in INVENTORY.glob("*.json"):
        shutil.copy2(f, B / m.get(f.name, f.name))
    apps = json.loads((B / "applist_original.json").read_text())
    rem = lambda a: str(a.get("isunInstalled")).lower() == "true"
    ch = []
    for a in apps:
        if str(a["appId"]) in KEEP:
            continue
        if rem(a):
            ch.append({"id": f"app-{a['appId']}", "type": "app_uninstall", "name": a["name"], "appId": a["appId"], "url": a["url"],
                       "menu": "Home → App markieren → OK lang drücken → Deinstallieren", "before": "installiert", "after": "deinstalliert",
                       "rollback": "APP STORE → Suche → Installieren", "done": False})
        else:
            ch.append({"id": f"bar-{a['appId']}", "type": "homebar_remove", "name": a["name"], "appId": a["appId"], "url": a["url"],
                       "menu": "Home → App markieren → OK lang → Entfernen (falls angeboten)", "before": "in Leiste", "after": "nicht in Leiste",
                       "rollback": "Apps → Zur Startseite hinzufügen", "done": False})
    for sid, menu, after in SETTINGS:
        ch.append({"id": f"set-{sid}", "type": "setting", "name": sid, "menu": menu, "before": None, "after": after,
                   "rollback": "Vorher-Wert im selben Menü wiederherstellen", "key_macro": None, "done": False})
    (B / "rollback_state.json").write_text(json.dumps({"tv": tv_ip(), "created": time.strftime("%Y-%m-%d"), "changes": ch}, indent=2, ensure_ascii=False))
    L = [f"# ROLLBACK – Backup {B.name}", "", "Vorher-Werte der Einstellungen sind leer: die API kann Menüwerte nicht lesen – vor dem Umschalten am TV ablesen und eintragen.", "",
         "| Typ | Name | Menüpfad | Vorher | Nachher |", "|---|---|---|---|---|"]
    L += [f"| {c['type']} | {c['name']} | {c['menu']} | {c['before'] or '_ablesen_'} | {c['after']} |" for c in ch]
    L += ["", "Werksreset (letzter Notanker): Einstellungen → Support → Selbstdiagnose → Zurücksetzen (Pfad je nach Firmware)."]
    (B / "ROLLBACK.md").write_text("\n".join(L) + "\n")
    sums = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(B)}" for p in sorted(B.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"]
    (B / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    print(f"{B.name}: {sum(c['type']=='app_uninstall' for c in ch)} Deinstallationen, "
          f"{sum(c['type']=='homebar_remove' for c in ch)} Systemapps, {len(SETTINGS)} Einstellungen geplant.")


if __name__ == "__main__":
    main()
