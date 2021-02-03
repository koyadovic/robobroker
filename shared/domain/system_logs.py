
def add_system_log(log_type: str, text):
    # TODO enhance this
    from shared.application.models import DSystemLog
    DSystemLog.objects.create(log_type=log_type, text=text)
