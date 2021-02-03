from shared.infrastructure.django_logs import DSystemLog


def add_system_log(log_type: str, text):
    DSystemLog.objects.create(log_type=log_type, text=text)
