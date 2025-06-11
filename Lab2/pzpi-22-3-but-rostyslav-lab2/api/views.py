from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import models
from django.db.models import Sum
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
import io
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import UserProfile, Resource, Expense, Budget, ActionLog, Notification, RFIDTag
from .serializers import (
    UserProfileSerializer,
    ResourceSerializer,
    ExpenseSerializer,
    BudgetSerializer,
    ActionLogSerializer,
    NotificationSerializer,
    RFIDTagSerializer,
)

# --- Login View ---
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
        },
    ),
    responses={
        200: openapi.Response(
            description='Successful login',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
            )
        ),
        401: openapi.Response(description='Invalid credentials'),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# --- ViewSets ---
class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserProfile.objects.none()
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Create a new user profile (forbidden, use admin endpoint)",
        responses={403: 'User creation forbidden'}
    )
    def create(self, request, *args, **kwargs):
        return Response(
            {'error': 'User creation is only allowed via /api/admin/users/create/'},
            status=status.HTTP_403_FORBIDDEN
        )

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Expense.objects.none()
        if self.request.user.is_staff:
            return Expense.objects.all()
        return Expense.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Create a new expense",
        request_body=ExpenseSerializer,
        responses={201: ExpenseSerializer, 400: 'Invalid data'}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        resource = serializer.validated_data['resource']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        is_booking = serializer.validated_data.get('is_booking', False)

        overlapping_expenses = Expense.objects.filter(
            resource=resource,
            start_time__lte=end_time,
            end_time__gte=start_time
        )
        if overlapping_expenses.exists():
            return Response(
                {"error": "Resource is not available at this time"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = UserProfile.objects.get(user=user)
            budget = Budget.objects.filter(corporate_account_id=profile.corporate_account_id).first()
            total_cost = resource.cost_per_hour * (
                (end_time - start_time).total_seconds() / 3600
            )
            current_expenses = Expense.objects.filter(
                user__userprofile__corporate_account_id=profile.corporate_account_id
            ).aggregate(total=Sum('total_cost'))['total'] or 0
            if profile.user_limit and current_expenses + total_cost > profile.user_limit:
                Notification.objects.create(
                    user=user,
                    message=f"User limit exceeded for {user.username} on {resource.name}"
                )
                return Response(
                    {"error": "User limit exceeded"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if budget and current_expenses + total_cost > budget.limit_amount:
                Notification.objects.create(
                    user=user,
                    message=f"Corporate budget limit exceeded for {user.username} on {resource.name}"
                )
                return Response(
                    {"error": "Corporate budget limit exceeded"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "expense_update",
                "message": serializer.data
            }
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Budget.objects.none()
        if self.request.user.is_staff:
            return Budget.objects.all()
        profile = UserProfile.objects.get(user=self.request.user)
        return Budget.objects.filter(corporate_account_id=profile.corporate_account_id)

class ActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActionLog.objects.all()
    serializer_class = ActionLogSerializer
    permission_classes = [IsAdminUser]

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="List all notifications for the authenticated user or all users (admin only)",
        responses={200: NotificationSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new notification (admin only)",
        request_body=NotificationSerializer,
        responses={201: NotificationSerializer}
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if request.user.is_staff:
            ActionLog.objects.create(
                admin=request.user,
                action=f'Created notification for user {request.data.get("user")} at {timezone.now()}'
            )
        return response

    @swagger_auto_schema(
        operation_description="Update a notification (admin only)",
        request_body=NotificationSerializer,
        responses={200: NotificationSerializer}
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if request.user.is_staff:
            ActionLog.objects.create(
                admin=request.user,
                action=f'Updated notification {kwargs.get("pk")} at {timezone.now()}'
            )
        return response

    @swagger_auto_schema(
        operation_description="Delete a notification (admin only)",
        responses={204: 'Notification deleted'}
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        if request.user.is_staff:
            ActionLog.objects.create(
                admin=request.user,
                action=f'Deleted notification {kwargs.get("pk")} at {timezone.now()}'
            )
        return response

class RFIDTagViewSet(viewsets.ModelViewSet):
    queryset = RFIDTag.objects.all()
    serializer_class = RFIDTagSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_description="List all RFID tags (admin only)",
        responses={200: RFIDTagSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new RFID tag (admin only)",
        request_body=RFIDTagSerializer,
        responses={201: RFIDTagSerializer}
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        ActionLog.objects.create(
            admin=request.user,
            action=f'Created RFID tag {request.data.get("tag_id")} for user {request.data.get("user")} at {timezone.now()}'
        )
        return response

    @swagger_auto_schema(
        operation_description="Update an RFID tag (admin only)",
        request_body=RFIDTagSerializer,
        responses={200: RFIDTagSerializer}
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        ActionLog.objects.create(
            admin=request.user,
            action=f'Updated RFID tag {kwargs.get("pk")} at {timezone.now()}'
        )
        return response

    @swagger_auto_schema(
        operation_description="Delete an RFID tag (admin only)",
        responses={204: 'RFID tag deleted'}
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        ActionLog.objects.create(
            admin=request.user,
            action=f'Deleted RFID tag {kwargs.get("pk")} at {timezone.now()}'
        )
        return response

# --- Analytics View ---
@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='User ID'),
        openapi.Parameter('start_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date', description='Start date (YYYY-MM-DD)'),
        openapi.Parameter('end_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date', description='End date (YYYY-MM-DD)'),
    ],
    responses={
        200: openapi.Response(
            description='Expense and resource usage analytics',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_cost': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'resource_usage': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'resource_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'total_usage_hours': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'total_cost': openapi.Schema(type=openapi.TYPE_NUMBER),
                            }
                        )
                    )
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_view(request):
    expenses = Expense.objects.all() if request.user.is_staff else Expense.objects.filter(user=request.user)
    user_id = request.query_params.get('user_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    if user_id and request.user.is_staff:
        expenses = expenses.filter(user_id=user_id)
    if start_date:
        expenses = expenses.filter(start_time__gte=start_date)
    if end_date:
        expenses = expenses.filter(end_time__lte=end_date)

    total_cost = expenses.aggregate(total=Sum('total_cost'))['total'] or 0
    resource_usage = expenses.values('resource__id', 'resource__name').annotate(
        total_usage_hours=Sum(
            (models.F('end_time') - models.F('start_time')) / 3600.0
        ),
        total_cost=Sum('total_cost')
    )
    return Response({
        'total_cost': total_cost,
        'resource_usage': resource_usage
    }, status=status.HTTP_200_OK)

# --- PDF Report View ---
@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='User ID'),
        openapi.Parameter('start_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date', description='Start date (YYYY-MM-DD)'),
        openapi.Parameter('end_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date', description='End date (YYYY-MM-DD)'),
    ],
    responses={
        200: openapi.Response(description='PDF report generated')
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def expense_report_view(request):
    expenses = Expense.objects.all() if request.user.is_staff else Expense.objects.filter(user=request.user)
    user_id = request.query_params.get('user_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    if user_id and request.user.is_staff:
        expenses = expenses.filter(user_id=user_id)
    if start_date:
        expenses = expenses.filter(start_time__gte=start_date)
    if end_date:
        expenses = expenses.filter(end_time__lte=end_date)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 800, "Expense Report")
    y = 750
    for expense in expenses:
        p.drawString(100, y, f"{expense.user.username} - {expense.resource.name}: {expense.total_cost} ({expense.start_time} to {expense.end_time})")
        y -= 20
    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expense_report.pdf"'
    return response

# --- RFID Validation View ---
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['tag_id'],
        properties={
            'tag_id': openapi.Schema(type=openapi.TYPE_STRING, description='RFID/NFC tag ID'),
        },
    ),
    responses={
        200: openapi.Response(
            description='RFID validation result',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'access_granted': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                }
            )
        ),
        400: openapi.Response(description='Invalid tag or no resources')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def rfid_validate_view(request):
    tag_id = request.data.get('tag_id')
    try:
        rfid_tag = RFIDTag.objects.get(tag_id=tag_id, is_active=True)
        resource = Resource.objects.first()
        if not resource:
            return Response(
                {'error': 'No resources available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Expense.objects.create(
            user=rfid_tag.user,
            resource=resource,
            start_time=timezone.now(),
            end_time=timezone.now(),
            total_cost=0,
            is_booking=False
        )
        return Response(
            {'user_id': rfid_tag.user.id, 'access_granted': True},
            status=status.HTTP_200_OK
        )
    except RFIDTag.DoesNotExist:
        return Response(
            {'error': 'Invalid or inactive tag'},
            status=status.HTTP_400_BAD_REQUEST
        )

# --- Admin Functions ---
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password', 'email', 'corporate_account_id', 'user_limit'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'corporate_account_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'user_limit': openapi.Schema(type=openapi.TYPE_NUMBER),
        }
    ),
    responses={201: 'User created', 400: 'Invalid data'}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    corporate_account_id = request.data.get('corporate_account_id')
    user_limit = request.data.get('user_limit')

    if not all([username, password, email, corporate_account_id, user_limit]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        UserProfile.objects.create(
            user=user,
            corporate_account_id=corporate_account_id,
            user_limit=user_limit
        )
        ActionLog.objects.create(
            admin=request.user,
            action=f'Created user {username} at {timezone.now()}'
        )
        return Response(
            {'message': 'User created'},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@swagger_auto_schema(
    method='delete',
    manual_parameters=[openapi.Parameter('user_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description='User ID')],
    responses={204: 'User deleted', 404: 'User not found'}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        username = user.username
        UserProfile.objects.filter(user=user).delete()
        user.delete()
        ActionLog.objects.create(
            admin=request.user,
            action=f'Deleted user {username} at {timezone.now()}'
        )
        return Response(
            {'message': 'User deleted'},
            status=status.HTTP_204_NO_CONTENT
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )