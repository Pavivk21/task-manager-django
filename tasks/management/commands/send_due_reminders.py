from django.core.management.base import BaseCommand
from django.utils.timezone import localdate,timedelta
from django.core.mail import send_mail
from tasks.models import Task

class Command(BaseCommand):
    help = 'Send email reminders for tasks due tomorrow'

    def handle(self, *args, **kwargs):
        tomorrow = localdate() + timedelta(days=1)
        tasks = Task.objects.filter(due_date=tomorrow)

        for task in tasks:
            if task.owner.email:
                send_mail(
                    subject=f"Reminder: '{task.title}' is due tomorrow!",
                    message=f"Hi {task.owner.username},\n\nJust a reminder that your task '{task.title}' is due on {task.due_date}.\n\nStay on track!",
                    from_email='noreply@yourdomain.com',
                    recipient_list=[task.owner.email],
                    fail_silently=False,
                )
                self.stdout.write(f"Reminder sent for task: {task.title}")
