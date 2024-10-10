from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("user_auth/", include("user_auth.urls")),
    path("backtester/", include("backtester.urls")),
]
