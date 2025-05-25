from django.contrib import admin
from django.urls import include, path

from api.views import handle_shortlink

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/s/<slug:short_link>/", handle_shortlink, name="short_url"),
]