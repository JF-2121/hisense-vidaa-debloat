"""Gemeinsame Konfiguration + MQTT-Verbindung zum VIDAA-TV.

Konfiguration über Umgebungsvariablen:
  VIDAA_TV_IP   (Pflicht)  IP des TVs im LAN, z. B. 192.168.x.y
  VIDAA_KEEP    (optional) appIds, die bleiben sollen, Standard "1,2,3" (Netflix, Prime Video, YouTube)
Private Laufzeitdaten (Token, Client-ID, Inventar, Logs) liegen in ./.state/ (gitignored).
"""
import json, os, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".state"
STATE.mkdir(exist_ok=True)
INVENTORY = STATE / "inventory"
TOKENS = STATE / "tokens.json"
CLIENT_ID_FILE = STATE / "client_device_id.txt"
LOG = STATE / "actions_log.jsonl"
KEEP = set(os.environ.get("VIDAA_KEEP", "1,2,3").split(","))


def tv_ip():
    ip = os.environ.get("VIDAA_TV_IP")
    if not ip:
        sys.exit("Bitte zuerst setzen:  export VIDAA_TV_IP=<IP des TVs>")
    return ip


def client_mac():
    """Feste, lokal administrierte Pseudo-MAC als MQTT-Client-UUID (wird wiederverwendet)."""
    if CLIENT_ID_FILE.exists():
        return CLIENT_ID_FILE.read_text().strip()
    mac = ":".join(f"{x:02X}" for x in [0x02] + [random.randint(0, 255) for _ in range(5)])
    CLIENT_ID_FILE.write_text(mac + "\n")
    return mac


def make_client():
    from vidaa import VidaaTV
    from vidaa.config.storage import get_storage
    tv = VidaaTV(host=tv_ip(), mac_address=client_mac(), use_dynamic_auth=True,
                 storage=get_storage(TOKENS))
    return tv


def connect(require_auth=True):
    tv = make_client()
    if not tv.connect(timeout=15):
        sys.exit("MQTT-Verbindung fehlgeschlagen (TV an? gleiches Netz? Port 36669 offen?)")
    if require_auth and not tv.is_authenticated():
        sys.exit("Nicht gepairt oder Token abgelaufen → python scripts/pair.py")
    return tv


def log(**kw):
    with open(LOG, "a") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}, ensure_ascii=False) + "\n")
