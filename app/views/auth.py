from app.serializers import *
from app.models.user import OTP
from app.models.membership import Plan
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from app.utils import *
from rest_framework.response import Response
import random
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import  IsAuthenticated
import pyotp
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from rest_framework.views import APIView

# Create your views here.
class SignUpView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SignUpSerializer(request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Account created. Check your email to verify."})
        return Response(serializer.errors, status=400)


class EmailVerificationView(APIView):
    def post(self, request, uidb64, token):
        try:
          uid = urlsafe_base64_decode(uidb64).decode()
          user = get_user_model().objects.get(pk=uid)
          if expiring_token_generator.check_token(user, token):
             user.is_verified = True
             user.save()
             return Response({"message": "Email verified successfully!"})
          else:
              return Response({"error": "Invalid or expired token."}, status=400)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            return Response({"error": "Invalid verification link."}, status=400)
        
class LoginView(APIView):
    def post(self, request):
        try:
            identifier = request.data.get('username', None)
            password = request.data.get('password', None)
            if not identifier or not password:
                return Response({"error":"phone ,email or username required"})
            try:
               user = get_user_model().objects.get(Q(username=identifier)|Q(email=identifier)|Q(phone=identifier))
               if not user:
                   return Response({"error":"invalid credentials"})
               if not user.check_password(password):
                   return Response({"error":"invalid credentials"})
               if user.is_2fa_enabled:
                   return Response({"message": "2FA required", "status_code": 200}, status=status.HTTP_200_OK)
               
               refresh = RefreshToken.for_user(user)
               return Response({"refresh":str(refresh), "access_token":str(refresh.access_token), "status":200})
            except Exception as e:
                return Response({"error": f"Error during login: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendOTPView(APIView, LoginRequiredMixin):
    def post(self, request):
        try:
            phone = request.data.get('phone', None)
            try:
                user = get_user_model().objects.get(phone=phone)
            except get_user_model().DoesNotExist:
                return Response({"error": "Phone number not registered"})
            otp = str(random.randint(100000, 999999))
            print(otp)
            data = {
                'user': user,
                'otp': otp
            }
            serializer = OTPSerializer(data)
            serializer.save()
            send_otp = send_otp_via_sms(phone, otp)
            if send_otp:
                return Response({"success": "otp sent successfully"})
            return Response({"error":"failed to send otp"})
        except Exception as e:
            error_message = f"Error in OTP processing: {str(e)}"
            return Response({"error":error_message, "status_code":500})

class VerifyOTPView(APIView):
    def post(self, request):
        try:
            phone = request.data.get("phone", None)
            otp = request.data.get("otp", None)
            if not otp or not phone:
                return Response({"error":"phone and otp are required"})
            user = get_user_model().objects.get(phone=phone)
            otp_obj = OTP.objects.filter(user=user, otp=otp).first()
            if not otp_obj:
                return Response({"error":"invalid otp"})
            if otp_obj.is_expired():
                return Response({"error":"otp expired please send other otp"})
            otp_obj.is_verified = True
            otp_obj.save()
            user.is_phone_verified = True
            user.save()
            plan = get_object_or_404(Plan, name='free')
            data = {
                'user': user,
                'plan':plan,
                'is_active':True,
                'purchase_date': datetime.today(),
                'expiry_date': datetime.today() + timedelta(days=30)
            }
            serializer = MembershipSerializer(data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "otp verified successfully!"})
            else:
                return Response({"error": "error"})
        except Exception as e:
            error_message = f"Error in OTP processing: {str(e)}"
            return Response({"error":error_message, "status_code":500})

@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordview(APIView, LoginRequiredMixin):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            old_password = request.data.get("old_password",None)
            new_password = request.data.get("new_password", None)
            if not old_password or not new_password:
                return Response({"error":"password required"})
            user = request.user
            if not user.check_password(old_password):
                return Response({"error": "old password is wrong"})
            user.set_password(new_password)
            user.save()
            return Response({"success": "password changed successfully"})
        except Exception as e:
            error_message = f"Error: {str(e)}"
            return Response({"error":error_message, "status_code":500})
        
class ResetPasswordView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email', None)
            print("email", email)
            if not email:
                return Response({"error": "email is required"})
            user = get_user_model().objects.filter(email=email).first()
            print("user", user)
            if not user:
                return Response({"error": "user does not exist"})
            link = activation_link(user)
            subject="Reset Your Password"
            send_activation_mail(user, link, subject)
            return Response({"success": "password reset link sent to your email"})
        except Exception as e:
            error_message = f"Error in sending reset password: {str(e)}"
            return Response({"error":error_message, "status_code":500})
        
class ConfirmResetPasswordView(APIView):
    def post(self, request, uidb64, token):
        try:
          uid = urlsafe_base64_decode(uidb64).decode()
          user = get_user_model().objects.get(pk=uid)
          if not expiring_token_generator.check_token(user, token):
              return Response({"error":"token expired"})
          new_password = request.data.get('new_password')
          if not new_password:
                return Response({"error": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)
          user.set_password(new_password)
          user.save()
          return Response({"success":"password reset confirmed"})
        except Exception as e:
            error_message = f"Error : {str(e)}"
            return Response({"error":error_message, "status_code":500})
        
@method_decorator(csrf_exempt, name='dispatch')
class Enable2FAView(APIView, LoginRequiredMixin):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
          user = request.user
          if user.is_2fa_enabled:
              return Response({"message": "2FA is already enabled."})
          if not user.is_phone_verified:
              return Response({"message": "verify your phone number first"})
          totp = pyotp.TOTP(pyotp.random_base32())
          user.two_fa_secret = totp.secret
          uri = totp.provisioning_uri(user.email, issuer_name="app")
          return Response(
              {"message":"2zfa enabled successfully",
              "secret": totp.secret,
              "qr_code_uri": uri})
        except Exception as e:
            error_message = f"Error : {str(e)}"
            return Response({"error":error_message, "status":500})
        
@method_decorator(csrf_exempt, name='dispatch')
class Verify2FA(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
           token = request.data.get("token")
           user = request.user 
           if not token:
               return Response({"error":"token is required"})
           totp = pyotp.TOTP(user.two_fa_secret)
           if totp.verify(token):
              user.is_2fa_enabled = True
              user.save()
              return Response({"success": "2FA verified successfully!"})
           return Response({"error": "Invalid or expired token."})
        except Exception as e:
            error_message = f"Error : {str(e)}"
            return Response({"error":error_message, "status":500})

@method_decorator(csrf_exempt, name='dispatch')
class Verify2FALogin(APIView):
    def post(self, request):
        try:
            user = request.user
            token = request.data.get("token")
            if not token:
                return Response({"error":"token is required"})
            totp = pyotp.TOTP(user.two_fa_secret)
            if totp.verify(token):
                refresh = RefreshToken.for_user(user)
                return Response({"refresh":str(refresh), "access_token":str(refresh.access_token), "status":200})
            return Response({"error":"invalid token"})
        except Exception as e:
            error_message = f"Error : {str(e)}"
            return Response({"error":error_message, "status":500})