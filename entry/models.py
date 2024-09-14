from django.db import models
class KeyManagement(models.Model):
    version = models.IntegerField(unique=True)
    aes_key = models.BinaryField()

    @staticmethod
    def get_current_key():
        return KeyManagement.objects.order_by('-version').first()

    @staticmethod
    def get_key_by_version(version):
        return KeyManagement.objects.get(version=version)