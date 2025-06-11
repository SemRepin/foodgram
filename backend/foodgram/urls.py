from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import RecipeViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("users.urls")),
    path("api/", include("api.urls")),
    path(
        "s/<int:pk>/",
        RecipeViewSet.as_view({"get": "redirect_to_recipe"}),
        name="short_link",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
