from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.home, name="home"),
    path("index", views.index, name="index"),
    path("crops", views.crops, name="crops"),
    path("ready", views.ready, name="ready"),
    path("start", views.start_farm, name="start"),
    path("api/farm/chat/", views.farm_chat, name="farm-chat"),
    path("api/farm/reset/", views.reset_chat, name="reset-chat"),
]
