from django.contrib import admin
from django.db.models import JSONField

from shared.application.forms import PrettyJSONWidget
from shared.application.models import DServerConfiguration, DUserConfiguration, DSystemLog
from django.contrib import messages


class DServerConfigurationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        try:
            obj.core_entity.request_pre_save_validations()
            obj.save()
        except Exception as e:
            messages.error(request, str(e))
            return
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


class DUserConfigurationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        try:
            obj.core_entity.request_pre_save_validations()
            obj.save()
        except Exception as e:
            messages.error(request, str(e))
            return
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


class DSystemLogAdmin(admin.ModelAdmin):
    list_display = ['instant', 'log_type', 'text']
    list_filter = ['log_type']


admin.site.register(DServerConfiguration, DServerConfigurationAdmin)
admin.site.register(DUserConfiguration, DUserConfigurationAdmin)
admin.site.register(DSystemLog, DSystemLogAdmin)
