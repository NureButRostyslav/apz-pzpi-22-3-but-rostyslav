from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    corporate_account_id = models.IntegerField()  # Removed unique=True
    user_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # MF8

    def __str__(self):
        return f"{self.user.username} (Account {self.corporate_account_id})"

class Resource(models.Model):
    name = models.CharField(max_length=100)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_booking = models.BooleanField(default=False)  # MF3

    def check_availability(self):
        conflicts = Expense.objects.filter(
            resource=self.resource,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)
        return not conflicts.exists()

    def check_budget(self):
        profile = UserProfile.objects.get(user=self.user)
        budget = Budget.objects.filter(corporate_account_id=profile.corporate_account_id).first()
        total_expenses = Expense.objects.filter(
            user__userprofile__corporate_account_id=profile.corporate_account_id
        ).exclude(id=self.id).aggregate(models.Sum('total_cost'))['total_cost__sum'] or 0

        if profile.user_limit and total_expenses + self.total_cost > profile.user_limit:
            return False
        if budget and total_expenses + self.total_cost > budget.limit_amount:
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.check_availability():
            raise ValueError("Resource is not available at this time")
        if not self.check_budget():
            Notification.objects.create(
                user=self.user,
                message=f"Budget limit exceeded for {self.user.username} on {self.resource.name}"
            )
            send_mail(
                subject="Budget Limit Exceeded",
                message=f"User {self.user.username} has exceeded their budget limit on {self.resource.name}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=True,
            )
            raise ValueError("Expense exceeds budget limit")
        if self.start_time and self.end_time:
            time_diff = (self.end_time - self.start_time).total_seconds() / 3600
            self.total_cost = time_diff * self.resource.cost_per_hour
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.resource.name}"

class Budget(models.Model):
    corporate_account_id = models.IntegerField()
    limit_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Budget {self.id} for account {self.corporate_account_id}"

class ActionLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.action} at {self.timestamp}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

class RFIDTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag_id = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"RFID Tag {self.tag_id} for {self.user.username}"