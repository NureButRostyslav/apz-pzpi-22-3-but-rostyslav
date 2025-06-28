from django.db.models import Sum, Avg
from datetime import datetime, timedelta
from .models import Expense

def calculate_trends(start_date, end_date):
    expenses = Expense.objects.filter(start_time__range=(start_date, end_date))
    total_cost = expenses.aggregate(total=Sum('total_cost'))['total'] or 0
    avg_cost_per_day = expenses.aggregate(avg=Avg('total_cost'))['avg'] or 0
    resource_usage = expenses.values('resource').annotate(total=Sum('total_cost'))
    weekly_trends = []
    current_date = start_date
    while current_date <= end_date:
        week_end = current_date + timedelta(days=6)
        week_expenses = expenses.filter(start_time__range=(current_date, week_end))
        week_total = week_expenses.aggregate(total=Sum('total_cost'))['total'] or 0
        weekly_trends.append({
            'week_start': current_date,
            'total_cost': week_total
        })
        current_date += timedelta(days=7)
    return {
        'total_cost': total_cost,
        'avg_cost_per_day': avg_cost_per_day,
        'resource_usage': list(resource_usage),
        'weekly_trends': weekly_trends
    }

def predict_expenses(start_date, end_date):
    past_expenses = Expense.objects.filter(start_time__lt=start_date)
    avg_daily_cost = past_expenses.aggregate(avg=Avg('total_cost'))['avg'] or 0
    days = (end_date - start_date).days
    predicted_cost = avg_daily_cost * days
    return {'predicted_cost': predicted_cost}
