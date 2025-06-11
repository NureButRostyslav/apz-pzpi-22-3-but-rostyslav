from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/realtime-expenses/(?P<user_id>\d+)/$', consumers.ExpenseConsumer.as_asgi()),
]