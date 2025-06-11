from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Avg, Count
import numpy as np
from scipy import stats
from datetime import timedelta
from .models import Expense, Resource, UserProfile, Budget

def analyze_resource_efficiency(start_date, end_date, user=None):
    """
    Аналізує ефективність використання ресурсів за період часу.
    Повертає статистику: середній час використання, загальні витрати, коефіцієнт завантаженості.
    """
    filters = {
        'start_time__gte': start_date,
        'end_time__lte': end_date,
    }
    if user:
        filters['user'] = user

    expenses = Expense.objects.filter(**filters)
    total_expenses = expenses.aggregate(total_cost=Sum('total_cost'))['total_cost'] or 0

    usage_times = [
        (expense.end_time - expense.start_time).total_seconds() / 3600
        for expense in expenses
    ]
    avg_usage_time = np.mean(usage_times) if usage_times else 0

    resource_usage = expenses.values('resource__name').annotate(
        total_hours=Sum(
            (models.F('end_time') - models.F('start_time')) / 3600.0
        ),
        usage_count=Count('id')
    )
    total_available_hours = (end_date - start_date).total_seconds() / 3600
    occupancy_rates = [
        item['total_hours'] / total_available_hours if total_available_hours > 0 else 0
        for item in resource_usage
    ]
    avg_occupancy_rate = np.mean(occupancy_rates) if occupancy_rates else 0

    return {
        'total_cost': round(total_cost, 2),
        'avg_usage_time': round(avg_usage_time, 2),
        'avg_occupancy_rate': round(avg_occupancy_rate, 2),
        'resource_breakdown': [
            {
                'resource': item['resource__name'],
                'total_hours': round(item['total_hours'], 2),
                'usage_count': item['usage_count']
            } for item in resource_usage
        ]
    }

def forecast_resource_demand(resource_id, days=30):
    """
    Прогнозує попит на ресурс на основі історичних даних за допомогою лінійної регресії.
    """
    resource = Resource.objects.get(id=resource_id)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Збір історичних даних про використання ресурсу
    expenses = Expense.objects.filter(
        resource=resource,
        start_time__gte=start_date,
        end_time__lte=end_date
    )

    days_list = [(expense.start_time - start_date).days for expense in expenses]
    usage_hours = [
        (expense.end_time - expense.start_time).total_seconds() / 3600
        for expense in expenses
    ]

    if not days_list or len(days_list) < 2:
        return {'error': 'Недостатньо даних для прогнозування'}

    slope, intercept, r_value, p_value, std_err = stats.linregress(days_list, usage_hours)
    predicted_usage = [slope * (i + days) + intercept for i in range(7)]  # Прогноз на 7 днів

    predicted_usage = [max(0, usage) for usage in predicted_usage]

    return {
        'resource': resource.name,
        'forecasted_hours': [round(usage, 2) for usage in predicted_usage],
        'r_squared': round(r_value ** 2, 2),
        'confidence': round(1 - p_value, 2)
    }