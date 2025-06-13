from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.core.mail import send_mail
from django.contrib.auth.models import User
from tasks.models import Task
from django.conf import settings
from datetime import date

class Command(BaseCommand):
    help = 'Send email reminders for due or overdue tasks'

    def handle(self, *args, **kwargs):
        today = date.today()
        users = User.objects.all()

        for user in users:
            due_today = Task.objects.filter(owner=user, due_date=today, status__in=['PENDING', 'IN_PROGRESS'])
            overdue = Task.objects.filter(owner=user, due_date__lt=today, status__in=['PENDING', 'IN_PROGRESS'])

            if due_today or overdue:
                subject = "🕒 Task Reminder from Task Manager"
                message = f"Hi {user.username},\n\n"

                if due_today.exists():
                    message += f"You have {due_today.count()} task(s) due **today**:\n"
                    for task in due_today:
                        message += f"• {task.title} (Due: {task.due_date})\n"

                if overdue.exists():
                    message += f"\n❗ You also have {overdue.count()} overdue task(s):\n"
                    for task in overdue:
                        message += f"• {task.title} (Due: {task.due_date})\n"

                message += "\nPlease login and complete your tasks.\n\n- Task Manager App"

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

        self.stdout.write("✅ Reminder emails sent.")
