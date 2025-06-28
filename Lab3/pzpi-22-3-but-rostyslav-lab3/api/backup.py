import csv
import os
from datetime import datetime
from .models import Expense, Booking

def backup_user_data(user_id, backup_dir='/app/backups'):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{backup_dir}/user_{user_id}_backup_{timestamp}.csv'
    expenses = Expense.objects.filter(user_id=user_id)
    bookings = Booking.objects.filter(user_id=user_id)
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Type', 'Resource', 'Total Cost', 'Start Time', 'End Time'])
        for expense in expenses:
            writer.writerow(['Expense', expense.resource, expense.total_cost, expense.start_time, ''])
        for booking in bookings:
            writer.writerow(['Booking', booking.resource_name, '', booking.start_time, booking.end_time])
    return filename

def restore_user_data(user_id, filename):
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Type'] == 'Expense':
                Expense.objects.create(
                    user_id=user_id,
                    resource=row['Resource'],
                    total_cost=float(row['Total Cost']),
                    start_time=datetime.fromisoformat(row['Start Time'])
                )
            elif row['Type'] == 'Booking':
                Booking.objects.create(
                    user_id=user_id,
                    resource_name=row['Resource'],
                    start_time=datetime.fromisoformat(row['Start Time']),
                    end_time=datetime.fromisoformat(row['End Time'])
                )
