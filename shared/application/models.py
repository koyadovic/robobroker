from django.db import models

from shared.domain.configurations import ServerConfiguration, UserConfiguration


class DServerConfiguration(models.Model):
    key = models.CharField(max_length=200, blank=False, null=False)
    data = models.JSONField(blank=False, null=False, default=dict)

    class Meta:
        verbose_name = 'Server configuration'
        verbose_name_plural = 'Server configurations'

    def __str__(self):
        return f'{self.key}'

    @property
    def core_entity(self):
        return ServerConfiguration(self.key, self.data)


class DUserConfiguration(models.Model):
    user_pk = models.IntegerField()
    key = models.CharField(max_length=200, blank=False, null=False)
    data = models.JSONField(blank=False, null=False, default=dict)

    class Meta:
        verbose_name = 'User configuration'
        verbose_name_plural = 'User configurations'

    def __str__(self):
        return f'{self.key} (user={self.user_pk})'

    @property
    def core_entity(self):
        return UserConfiguration(self.user_pk, self.key, self.data)
