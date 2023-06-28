from django.urls import path
from . import views

urlpatterns = (
    path('dcim/devices/<int:pk>/atelier/', views.AtelierView.as_view(), name='atelier'),
)
