from datetime import timedelta
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from .models import Reminder
from .utils import send_reminder_email

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_reminders, 'interval', minutes=5)
    scheduler.start()

def check_reminders():
    now = timezone.now()

    reminders = Reminder.objects.filter(
        email_sent=False
    )

    for r in reminders:
        alert_time = r.reminder_datetime - timedelta(hours=2)

        # If current time is within 5 minutes window
        if alert_time <= now <= alert_time + timedelta(minutes=5):
            send_reminder_email(r)
            r.email_sent = True
            r.save()

