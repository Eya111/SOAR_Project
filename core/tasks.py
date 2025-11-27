from celery import shared_task
from django.utils import timezone
from core.models import EventLog
from django.db import models
from core.models import Trigger, Playbook
# ---------------------------
# 1) Collecter un événement
# ---------------------------
@shared_task
def collect_event(source, event_type, payload, message=""):
    event = EventLog.objects.create(
        source=source,
        event_type=event_type,
        payload=payload,
        message=message
    )


    # Analyse automatique
    analyze_event.delay(event.id)

    # Vérification des triggers après analyse
    #check_triggers.delay(event.id)

    return event.id


# ---------------------------
# 2) Analyser l'événement
# ---------------------------
@shared_task
def analyze_event(event_id):
    event = EventLog.objects.get(id=event_id)

    # Analyse automatique basée sur le message
    msg = event.message.lower()
    if "failed" in msg:
        severity = "HIGH"
    elif "error" in msg:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    event.severity = severity
    event.save()

    return severity


# ---------------------------
# 3) Playbook SOAR
# ---------------------------
@shared_task
def run_playbook(event_id):
    event = EventLog.objects.get(id=event_id)

    if event.severity == "HIGH":
        action = f"Alerte CRITIQUE envoyée pour l’événement {event.id}"
    elif event.severity == "MEDIUM":
        action = f"Notification envoyée pour l’événement {event.id}"
    else:
        action = f"Aucune action requise pour l’événement {event.id}"

    return action


@shared_task
def log_event(source, event_type, payload):
    """Créer un nouvel EventLog"""
    event = EventLog.objects.create(
        source=source,
        event_type=event_type,
        payload=payload
    )
    return event.id


@shared_task
def update_event(event_id, severity=None, payload_update=None):
    """Met à jour un EventLog existant"""
    event = EventLog.objects.get(id=event_id)
    if severity:
        event.severity = severity
    if payload_update:
        event.payload.update(payload_update)
    event.save()
    return event.id


@shared_task
def get_recent_events(limit=10):
    """Retourne les derniers événements enregistrés"""
    return list(EventLog.objects.order_by('-created_at')[:limit].values())


@shared_task
def check_triggers(event_id):
    event = EventLog.objects.get(id=event_id)

    # Chercher triggers du même event_type
    triggers = Trigger.objects.filter(event_type=event.event_type)

    for trig in triggers:
        # Exemple de condition simple
        event_count = event.payload.get("count", 0)

        if event_count >= trig.threshold:
            # On lance le playbook automatiquement
            run_playbook.delay(event_id)
            return f"Trigger activé → playbook {trig.playbook.name}"

    return "Aucun trigger activé"
