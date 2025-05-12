# your_app/tasks.py
from celery import shared_task
from .models.file import FileVersion, FileScan
import clamd

@shared_task
def scan_file_task(file_version_id):
    try:
        version = FileVersion.objects.get(id=file_version_id)
        file_path = version.file_data.path
        cd = clamd.ClamdUnixSocket()
        result = cd.scan(file_path)

        if not result:
            status = 'pending'
            report = 'No result from scan.'
        else:
            status_code, message = result[file_path]
            if status_code == 'OK':
                status = 'clean'
                report = 'No threats found.'
            else:
                status = 'infected'
                report = message

        FileScan.objects.create(
            file=version,
            scan_status=status,
            scan_report=report
        )
    except Exception as e:
        FileScan.objects.create(
            file_id=file_version_id,
            scan_status='pending',
            scan_report=f'Scan failed: {str(e)}'
        )
