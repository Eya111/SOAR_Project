from django.urls import path
from .views import event_list
from .views import dashboard_home, run_demo
from . import views
from .views import export_logs_csv

urlpatterns = [
    path('events/', event_list, name='event_list'),
    path('logs/', views.execution_logs, name='execution_logs'),
    path("", dashboard_home, name="dashboard_home"),
    path("run-demo/", run_demo, name="run_demo"),
    path("export-logs/", export_logs_csv, name="export_logs"),
]
