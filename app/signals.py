from django.db.models.signals import post_save
from django.dispatch import receiver
from .models.file import FileVersion
from .tasks import scan_file_task

@receiver(post_save, sender=FileVersion)
def start_scan_on_upload(sender, instance, created, **kwargs):
    if created:
        scan_file_task.delay(instance.id)
