from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .models.file import FileAccessLog, FileScan




# Custom Token Generator
class ExpiringTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self, expiration_minutes=60):
        self.expiration_minutes = expiration_minutes
        super().__init__()

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}{user.date_joined}"

    def check_token(self, user, token):
        try:
            if not super().check_token(user, token):
                return False

            # Check if token has expired
            token_timestamp = self._get_timestamp_from_token(token)
            expiration_time = timezone.now() - timedelta(minutes=self.expiration_minutes)
            
            return token_timestamp > expiration_time
        except Exception:
            return False

    def _get_timestamp_from_token(self, token):
        try:
            decoded_data = token.split('-')
            return timezone.datetime.fromtimestamp(int(decoded_data[-1]))
        except Exception:
            return timezone.now()

# Instantiate the generator
expiring_token_generator = ExpiringTokenGenerator()

def activation_link( user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = expiring_token_generator.make_token(user)
    current_site = 'localhost:8000/'
    activation_link = f"http://{current_site}/{uid}/{token}/"
    print(activation_link)
    return activation_link

def send_activation_mail(user, activation_link, subject):
    send_mail(subject=subject, 
              message= f"click on the  link: {activation_link}",
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[user.email],
              fail_silently=False)
    

# Email Configuration (Update with your details)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'youremail@gmail.com'
EMAIL_PASSWORD = 'yourpassword'

def send_otp_via_sms(phone, otp):
    carrier_gateway = '@vtext.com'  # Example for Verizon
    to_email = f"{phone}{carrier_gateway}"

    subject = "Your OTP Code"
    body = f"Your OTP is {otp}. It is valid for 5 minutes."

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return False

class FileAccessLoggingMixin:
    DEBOUNCE_SECONDS = 60 

    def log_file_access(self, request, file, action):
        ip = self.get_client_ip(request)
        user = request.user
        now = timezone.now()

        # Check for a recent similar log
        last_log = FileAccessLog.objects.filter(
            user=user,
            file=file,
            action=action
        ).order_by('-timestamp').first()

        if not last_log or (now - last_log.timestamp).total_seconds() > self.DEBOUNCE_SECONDS:
            FileAccessLog.objects.create(
                user=user,
                file=file,
                action=action,
                ip_address=ip,
                timestamp=now
            )
        # Else: Skip logging as it's within debounce window

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


def is_file_infected(file):
    scan = FileScan.objects.filter(file=file).order_by('-scanned_at').first()
    return scan and scan.scan_status == 'infected'
