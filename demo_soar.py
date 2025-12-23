import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "soar_project.settings")
django.setup()

from core.tasks import collect_event

print("🛡️ DÉMO SOAR — Lancement automatique...\n")

events = [
    {
        "source": "Firewall",
        "event_type": "BRUTE_FORCE",
        "message": "Multiple failed SSH attempts detected",
        "payload": {"ip": "10.0.0.5"}
    },
    {
        "source": "IDS",
        "event_type": "PORT_SCAN",
        "message": "Suspicious port scanning activity",
        "payload": {"ip": "192.168.1.23"}
    },
    {
        "source": "WebServer",
        "event_type": "LOGIN_SUCCESS",
        "message": "User admin logged in successfully",
        "payload": {"user": "admin"}
    },
]

for event in events:
    print(f"➡️ Envoi événement : {event['event_type']}")
    collect_event.delay(
        source=event["source"],
        event_type=event["event_type"],
        message=event["message"],
        payload=event["payload"]
    )
    time.sleep(2)

print("\n✅ Tous les événements ont été envoyés au SOAR.")
