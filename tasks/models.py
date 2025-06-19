from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.crypto import get_random_string

# Task Status Options
STATUS_CHOICES = [
    ('TODO', 'To-Do'),
    ('INPROGRESS', 'In Progress'),
    ('COMPLETED', 'Completed'),
]

# Workspace model
class Workspace(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_workspaces')
    members = models.ManyToManyField(User, through='Membership', related_name='workspaces')

    def __str__(self):
        return self.name

# Membership model (joins users to workspaces)
class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

# Invitation model (to invite users to a workspace via email)
class Invitation(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=get_random_string)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} invited to {self.workspace.name}"

# Task model
class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateField(null=True, blank=True)
    reminder_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey('Workspace', on_delete=models.CASCADE, null=True, blank=True)  # Null = personal task

    def save(self, *args, **kwargs):
        if self.status == 'COMPLETED' and self.completed_at is None:
            self.completed_at = timezone.now().date()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title