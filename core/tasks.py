from celery import shared_task
from django.utils import timezone
from core.models import EventLog
from django.db import models
from core.models import EventLog, ExecutionLog, Trigger, Playbook
from celery import shared_task

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

    # Log automatique
    ExecutionLog.objects.create(
        event=event,
        action="Événement collecté",
        status="SUCCESS",
        details=f"Event {event.id} créé avec payload {payload}"
    )

    

    # Analyse automatique
    analyze_event.delay(event.id)

    # Vérification des triggers après analyse
    check_triggers.delay(event.id)

    return event.id


# ---------------------------
# 2) Analyser l'événement
# ---------------------------
@shared_task
def analyze_event(event_id):
    event = EventLog.objects.get(id=event_id)
    event_count = event.payload.get("count", 0)

    # Analyse automatique basée sur le message
    msg = event.message.lower()
    if "failed" in msg:
        severity = "HIGH"
    elif "error" in msg:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Vérification avec triggers
    triggers = Trigger.objects.filter(event_type=event.event_type)
    for trig in triggers:
        if event_count >= trig.threshold:
            severity = "HIGH"  # Si count dépasse le seuil, on force HIGH
            break

    event.severity = severity
    event.save()

    # Log automatique
    ExecutionLog.objects.create(
        playbook=None,
        event=event,
        action="Analyse effectuée",
        status="SUCCESS",
        details=f"Événement {event.id} analysé avec sévérité {severity}"
    )


    return severity


# ---------------------------
# 3) Playbook SOAR
# ---------------------------
@shared_task
def run_playbook(event_id):
    event = EventLog.objects.get(id=event_id)
    triggers = Trigger.objects.filter(event_type=event.event_type)

    playbook = None
    action = ""
    status = "INFO"
    message = ""

    trigger_fired = None

    for trig in triggers:
        event_count = event.payload.get("count", 0)
        if event_count >= trig.threshold:
            playbook = trig.playbook
            trigger_fired = trig
            if event.severity == "HIGH":
                action = f"Alerte CRITIQUE envoyée pour l’événement {event.id}"
                status = "SUCCESS"
            elif event.severity == "MEDIUM":
                action = f"Notification envoyée pour l’événement {event.id}"
                status = "SUCCESS"
            else:
                action = f"Aucune action requise pour l’événement {event.id}"
                status = "INFO"
            message = action
            break
    else:
        action = f"Aucun playbook activé pour l’événement {event.id}"
        message = action

    # Enregistrement automatique dans ExecutionLog
    ExecutionLog.objects.create(
        playbook=playbook,
        event=event,
        action="Vérification triggers",
        status="TRIGGER FIRED" if trigger_fired else "NO MATCH",
        details=message
    )

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

    activated_trigger = None

    for trig in triggers:
        event_count = event.payload.get("count", 0)

        if event_count >= trig.threshold:
            activated_trigger = trig
            break  # On garde le premier trigger qui correspond

    if activated_trigger:
        message = f"Trigger activé → playbook {activated_trigger.playbook.name}"
        
        # Exécuter playbook
        run_playbook.delay(event_id)

        # LOG automatiquement
        ExecutionLog.objects.create(
            playbook=activated_trigger.playbook,
            event=event,
            action="Vérification triggers",
            status="TRIGGER FIRED",
            details=message
        )

        return message

    else:
        message = "Aucun trigger activé"

        # LOG même si aucun trigger n'est activé
        ExecutionLog.objects.create(
            playbook=None,
            event=event,
            action="Vérification triggers",
            status="NO MATCH",
            details=message
        )

        return message
