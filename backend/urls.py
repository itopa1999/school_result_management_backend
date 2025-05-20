from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="School System API",
        default_version="v1",
        description="API description for School System App",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('backdoor/', admin.site.urls),
    path('admins/api/', include('administrator.urls')),
    path('manager/api/', include('manager.urls')),
    path('auth/api/', include('authentication.urls')),
    path(
        "doc/",
        include(
            [
                path(
                    "swagger/",
                    schema_view.with_ui("swagger", cache_timeout=0),
                    name="schema-swagger-ui",
                ),
                path(
                    "swagger.json",
                    schema_view.without_ui(cache_timeout=0),
                    name="schema-json",
                ),
                path(
                    "redoc/",
                    schema_view.with_ui("redoc", cache_timeout=0),
                    name="schema-redoc",
                ),
            ]
        ),
    )
        
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
