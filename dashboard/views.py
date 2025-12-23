import csv
import json

from django.http import HttpResponse
from django.shortcuts import render, redirect
from core.models import EventLog, ExecutionLog
from core.tasks import collect_event

def event_list(request):
    severity_filter = request.GET.get('severity')  # récupère le filtre depuis l'URL
    if severity_filter:
        events = EventLog.objects.filter(severity=severity_filter)
    else:
        events = EventLog.objects.all().order_by('-timestamp')
    return render(request, 'dashboard/event_list.html', {'events': events})

def execution_logs(request):
    logs = ExecutionLog.objects.all().order_by('-timestamp')
    return render(request, 'dashboard/execution_logs.html', {'logs': logs})

def dashboard_home(request):
    total_events = EventLog.objects.count()
    high_events = EventLog.objects.filter(severity="HIGH").count()
    medium_events = EventLog.objects.filter(severity="MEDIUM").count()
    low_events = EventLog.objects.filter(severity="LOW").count()

    triggers_fired = ExecutionLog.objects.filter(status="TRIGGER FIRED").count()
    success_runs = ExecutionLog.objects.filter(status="SUCCESS").count()
    failed_runs = ExecutionLog.objects.filter(status="FAILED").count()

    context = {
        "total_events": total_events,
        "high_events": high_events,
        "medium_events": medium_events,
        "low_events": low_events,
        "triggers_fired": triggers_fired,
        "success_runs": success_runs,
        "failed_runs": failed_runs,

        # GRAPHIQUES
        "severity_data": [high_events, medium_events, low_events],
        "playbook_data": [success_runs, failed_runs],
    }

    return render(request, "dashboard/home.html", context)


def run_demo(request):
    events = [
        {"source": "Firewall", "event_type": "BRUTE_FORCE", "message": "Multiple failed SSH attempts detected", "payload": {"ip": "10.0.0.5"}},
        {"source": "IDS", "event_type": "PORT_SCAN", "message": "Suspicious port scanning activity", "payload": {"ip": "192.168.1.23"}},
        {"source": "WebServer", "event_type": "LOGIN_SUCCESS", "message": "User admin logged in successfully", "payload": {"user": "admin"}},
    ]

    for event in events:
        collect_event.delay(
            source=event["source"],
            event_type=event["event_type"],
            message=event["message"],
            payload=event["payload"]
        )

    return redirect("dashboard_home")  # Retourne au dashboard après envoi


def export_logs_csv(request):
    # Création de la réponse CSV
    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename="soar_logs.csv"'},
    )
    
    # IMPORTANT : delimiter=";" pour Excel FR
    writer = csv.writer(response, delimiter=';')

    # En-têtes du fichier CSV
    writer.writerow(['Timestamp', 'Action', 'Status', 'Détails'])

    # Récupération des logs
    logs = ExecutionLog.objects.all().order_by('-timestamp')
    for log in logs:
        writer.writerow([log.timestamp, log.action, log.status, json.dumps(log.details, ensure_ascii=False)
        ])

    return response
