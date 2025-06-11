from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Resource, Expense, Budget, ActionLog, Notification, RFIDTag

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'corporate_account_id', 'user_limit']

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'name', 'cost_per_hour']

class ExpenseSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    resource = serializers.PrimaryKeyRelatedField(queryset=Resource.objects.all())

    class Meta:
        model = Expense
        fields = ['id', 'user', 'resource', 'start_time', 'end_time', 'total_cost', 'is_booking']

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'corporate_account_id', 'limit_amount']

class ActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionLog
        fields = ['id', 'admin', 'action', 'timestamp']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'created_at']

class RFIDTagSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = RFIDTag
        fields = ['id', 'user', 'tag_id', 'is_active']