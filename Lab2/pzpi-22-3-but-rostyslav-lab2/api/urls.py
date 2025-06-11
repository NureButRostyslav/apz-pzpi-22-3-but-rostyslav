from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserProfileViewSet,
    ResourceViewSet,
    ExpenseViewSet,
    BudgetViewSet,
    ActionLogViewSet,
    NotificationViewSet,
    RFIDTagViewSet,
    login_view,
    analytics_view,
    expense_report_view,
    rfid_validate_view,
    create_user,
    delete_user,
)

router = DefaultRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'action-logs', ActionLogViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'rfid-tags', RFIDTagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', login_view, name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('analytics/', analytics_view, name='analytics'),
    path('reports/expense/', expense_report_view, name='expense_report'),
    path('rfid-tags/validate/', rfid_validate_view, name='rfid_validate'),
    path('admin/users/create/', create_user, name='create_user'),
    path('admin/users/delete/<int:user_id>/', delete_user, name='delete_user'),
]