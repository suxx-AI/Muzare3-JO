from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.i18n import i18n_patterns
from dashboard.views import health, serve_asset

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # Local assets with DEBUG=False: localhost-only demo server, no CDN required.
    re_path(r"^static/(?P<path>.*)$", serve_asset),
]
urlpatterns += i18n_patterns(path("", include("dashboard.urls")))
handler400 = "dashboard.views.error_page"
handler403 = "dashboard.views.error_page"
handler404 = "dashboard.views.not_found"
handler500 = "dashboard.views.server_error"
