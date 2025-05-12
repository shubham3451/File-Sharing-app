from django.db import models
from .user import User


class Folder(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
   
class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField( max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FileVersion(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    version = models.IntegerField()
    size = models.BigIntegerField()
    type = models.CharField(max_length=50)
    folder = models.ForeignKey(Folder,null=True, on_delete=models.CASCADE)
    is_infected = models.BooleanField()
    file_data = models.FileField(upload_to='media/', max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class Trash(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} trashed by {self.deleted_by.username}"
   

class FileShare(models.Model):
    choices = (
        ('public', 'Public'),
        ('restricted', 'Restricted'),
        )
    file  = models.ForeignKey(FileVersion, on_delete=models.CASCADE, related_name='files_shared_by')
    shared_by = models.ForeignKey(User, on_delete = models.CASCADE, related_name='files_shared_with')
    shared_with = models.ManyToManyField(User,  blank=True)
    share_token = models.CharField(max_length=255, unique=True)
    access_type = models.CharField(max_length=20, choices=choices)
    expiry_date = models.DateTimeField(null=True, blank=True)
    download_limit = models.PositiveIntegerField(null=True, blank=True)
    downloads = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class FileAccessLog(models.Model):
    choices = (
      ('view', 'View'),
      ('download', 'Download'),
      ('share', 'Share'),
    )
    file = models.ForeignKey('File', on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_access_logs')
    action = models.CharField(max_length=20, choices=choices)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.file} at {self.timestamp}"


class FileScan(models.Model):
    choices = (
      ('pending', 'Pending'),
      ('clean', 'Clean'),
      ('infected', 'Infected'),
    )
    file = models.ForeignKey('FileVersion', on_delete=models.CASCADE, related_name='scans')
    scan_status = models.CharField(max_length=20, choices=choices, default='pending')
    scan_report = models.TextField()
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan of {self.file} - {self.scan_status}"
