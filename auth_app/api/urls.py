from django.urls import path

from .views import EmailCheckView, LoginView, RegisterView

urlpatterns = [
    path("registration/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
]
