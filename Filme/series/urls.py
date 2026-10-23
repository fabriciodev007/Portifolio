from django.urls import path
from .views import SeriesView

urlpatterns = [
    path('series/', SeriesView.as_view(), name='series'),
]