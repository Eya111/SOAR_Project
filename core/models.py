from django.db import models

class Playbook(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Action(models.Model):
    ACTION_TYPES = [
        ("block_ip", "Block IP"),
        ("send_alert", "Send Alert"),
        ("log_event", "Log Event"),
    ]

    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name="actions")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    parameters = models.JSONField(blank=True, null=True)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.playbook.name} → {self.action_type}"


class Trigger(models.Model):
    event_type = models.CharField(max_length=100)
    threshold = models.PositiveIntegerField(default=1)
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE)

    def __str__(self):
        return f"Trigger for {self.event_type} (>{self.threshold})"


class ExecutionLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    playbook = models.ForeignKey(Playbook, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.timestamp} – {self.action} – {self.status}"

class EventLog(models.Model):
    source = models.CharField(max_length=255)
    event_type = models.CharField(max_length=255)
    payload = models.JSONField()
    message = models.TextField(blank=True)           # pour analyze_event
    severity = models.CharField(max_length=10, blank=True, null=True)  # LOW / MEDIUM / HIGH
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} – {self.event_type} – {self.severity}"
