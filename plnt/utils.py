from django.core.mail import send_mail
from django.conf import settings

def send_reminder_email(reminder):
    send_mail(
        subject="🌱 Plant Reminder Alert",
        message=f"""
Hi,

This is a reminder for your plant care 🌿

Title: {reminder.title}
Time: {reminder.reminder_datetime}

– PlantSnap
""",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[reminder.reg.user.email],
        fail_silently=False
    )
