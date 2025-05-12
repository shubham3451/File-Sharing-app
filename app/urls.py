from django.urls import path, include
from app.views.auth import *
from app.views.file import *
from app.views.membership import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("signUp/", SignUpView.as_view(), name="signUp"),
    path('login/', LoginView.as_view(), name='login'),
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify=otp"),
    path("change-password/", ChangePasswordview.as_view(), name="change-password"),
    path("send-reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path('confirm-reset-password/<uidb64>/<token>/', ConfirmResetPasswordView.as_view(), name='confirm-reset-password'),
    path('activate/<uidb64>/<token>/', EmailVerificationView.as_view(), name='activate'),
    path('auth/social/', include('allauth.socialaccount.urls')),
    path('enable-2fa/', Enable2FAView.as_view(), name='enable-2fa'),
    path('verify-2fa/', Verify2FA.as_view(), name='verify-2fa'),
    path('verify-2fa-login/', Verify2FALogin.as_view(), name='verify-2fa-login'),


    path('files/', Files.as_view(), name='files'),
    path('files/<int:file_id>/', Files.as_view(), name='file-detail'),
    path('files/<int:file_id>/<str:name>/', Files.as_view(), name='file-delete'),
    path('files/update/<int:file_id>/<int:version>/', Files.as_view(), name='file-update'),
    path('files/upload/', Files.as_view(), name='file-create'),
    path('files/download/<int:file_id>/', FileDownloadView.as_view(), name='file-download'),
    path('files/share/<int:file_id>/', FileShareView.as_view(), name='file-share'),
    path('files/share/<str:token>/', FileShareView.as_view(), name='file-share-view'),
    path('files/share/download/<str:token>/', FileShareDownload.as_view(), name='file-share-download'),
    path('folders/', FolderView.as_view(), name='folder-list'),
    path('folders/<int:folder_id>/', FolderView.as_view(), name='folder-detail'),
    path('folders/create/', FolderView.as_view(), name='folder-create'),
    path('folders/<int:folder_id>/update/', FolderView.as_view(), name='folder-update'),
    path('folders/<int:folder_id>/delete/', FolderView.as_view(), name='folder-delete'),
    path('search/', FileSearchView.as_view(), name='file_search'),

    path('plans/', PlanView.as_view(), name='plans'),
    path('membership/<int:plan_id>/', MembershipView.as_view(), name='membership'),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
