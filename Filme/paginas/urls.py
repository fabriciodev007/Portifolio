from django.urls import path
from .views import IndexView, assistir_trailer

urlpatterns = [
    path("", IndexView.as_view(), name="inicio"),
    path("filme/<int:movie_id>/trailer/", assistir_trailer, name="trailer"),
]