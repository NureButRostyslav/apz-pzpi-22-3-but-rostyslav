from django.contrib import admin
from .models import UserProfile, Resource, Expense, Budget, ActionLog
from django.contrib.auth.models import User

class UserProfileAdmin(admin.ModelAdmin):
    # Зміна: логування дій створення та видалення профілів
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            ActionLog.objects.create(
                admin=request.user,
                action=f"Created user profile {obj.user.username} via admin panel"
            )
    
    def delete_model(self, request, obj):
        ActionLog.objects.create(
            admin=request.user,
            action=f"Deleted user profile {obj.user.username} via admin panel"
        )
        super().delete_model(request, obj)

# Реєстрація моделей для адмін-панелі
admin.site.register(UserProfile, UserProfileAdmin)  # Зміна: використання кастомного адмін-класу
admin.site.register(Resource)
admin.site.register(Expense)
admin.site.register(Budget)
admin.site.register(ActionLog)