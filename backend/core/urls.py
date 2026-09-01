from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response


urlpatterns = [
    # Админка (без префикса api, доступ по /admin/)
    path("admin/", admin.site.urls),
    # ВСЕ API эндпоинты теперь внутри префикса /api/
    path(
        "api/",
        include(
            [
                # Маршруты приложения exercises
                # Итоговые пути: /api/exercises/..., /api/admin/exercises/..., /api/recommendations/...
                path("", include("exercises.urls")),
                # Auth endpoints (JWT)
                # Итоговые пути: /api/auth/login/, /api/auth/token/refresh/
                path(
                    "auth/login/",
                    TokenObtainPairView.as_view(),
                    name="token_obtain_pair",
                ),
                path(
                    "auth/token/refresh/",
                    TokenRefreshView.as_view(),
                    name="token_refresh",
                ),
            ]
        ),
    ),
]
