from django.urls import path, include
from .views import *

urlpatterns = [
    path(
        "user/",
        include(
            [
                path("create/", RegisterUser.as_view()),
                path("verify/", UserVerificationView.as_view()),
                path("resend/verification/token/", ResendVerificationTokenView.as_view()),
                path("login/", LoginView.as_view()),
                path("forget/password/", ForgetPasswordView.as_view()),
                path("forget/password/verify/", ForgetPasswordVerificationView.as_view()),
                path("change/password/", ChangePasswordView.as_view()),
                path('verify/email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify-email'),                
                
            ]
        )
    ),
]