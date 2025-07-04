from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import TaskForm, RegisterForm, WorkspaceTaskForm
from .models import Task
from datetime import date
from django.contrib import messages
from django.contrib.auth.views import LoginView
from calendar import month_name
from django.db.models import Count, Q
from collections import defaultdict
from datetime import timedelta
from django.core.mail import send_mail
from .models import Workspace, Invitation
from django.conf import settings
from .models import Invitation, Membership
from .forms import InvitationForm
from django.utils.crypto import get_random_string
from .forms import WorkspaceForm
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST,timezone
from django.utils.timezone import localdate




# ======================== Dashboard & Profile ==========================


def dashboard(request):
    tasks = Task.objects.filter(owner=request.user).order_by('-created_at')

    # Task counts
    total = tasks.count()
    completed = tasks.filter(status='COMPLETED').count()
    in_progress = tasks.filter(status='INPROGRESS').count()
    todo = tasks.filter(status='TODO').count()
    pending = todo + in_progress

    # Completion trend data
    completion_by_date = defaultdict(int)
    for item in tasks.filter(status='COMPLETED') \
                     .values('created_at__date') \
                     .annotate(count=Count('id')):
        completion_by_date[item['created_at__date']] += item['count']

    dates = [d.strftime('%Y-%m-%d') for d in completion_by_date]
    completion_counts = [completion_by_date[d] for d in completion_by_date]

    # Overdue trend data
    overdue_by_date = defaultdict(int)
    for item in tasks.filter(Q(due_date__lt=date.today()) & ~Q(status='COMPLETED')) \
                     .values('due_date') \
                     .annotate(count=Count('id')):
        overdue_by_date[item['due_date']] += item['count']

    overdue_labels = [d.strftime('%Y-%m-%d') for d in overdue_by_date]
    overdue_counts = [overdue_by_date[d] for d in overdue_by_date]

    # Status breakdown for pie chart (fixed 3 parts)
    status_order = ['TODO', 'INPROGRESS', 'COMPLETED']
    status_labels = []
    status_counts = []

    for status in status_order:
        count = tasks.filter(status=status).count()
        if count > 0:
            status_labels.append(status)
            status_counts.append(count)

    # Optional: Status color mapping for Chart.js
    status_color_map = {
        'TODO': '#66BB6A',         # green
        'INPROGRESS': '#FFD54F',   # amber
        'COMPLETED': '#42A5F5'     # blue
    }
    status_colors = [status_color_map[status] for status in status_labels]

    context = {
        'tasks': tasks[:5],
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'pending': pending,
        'dates': dates,
        'completion_counts': completion_counts,
        'overdue_labels': overdue_labels,
        'overdue_counts': overdue_counts,
        'status_labels': status_labels,
        'status_counts': status_counts,
        'status_colors': status_colors,  # pass to template
    }

    return render(request, 'tasks/dashboard.html', context)


@login_required
def profile(request):
    user = request.user
    total_tasks = Task.objects.filter(owner=user).count()
    completed_tasks = Task.objects.filter(owner=user, status='COMPLETED').count()
    progress_percent = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    return render(request, 'tasks/profile.html', {
        'user': user,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress_percent': progress_percent,
    })


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'tasks/edit_profile.html')


# ======================== Workspace Related ==========================

@login_required
def workspace_dashboard(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Check if user is allowed in this workspace
    is_member = Membership.objects.filter(user=request.user, workspace=workspace).exists()
    if request.user != workspace.owner and not is_member:
        messages.error(request, "You don't have access to this workspace.")
        return redirect('dashboard')

    # Show only tasks that belong to this workspace (not user-specific)
    task_list = Task.objects.filter(workspace=workspace).order_by('-created_at')
    paginator = Paginator(task_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total_tasks = task_list.count()
    completed_tasks = task_list.filter(status='COMPLETED').count()
    progress_percent = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    return render(request, 'tasks/workspace_dashboard.html', {
        'workspace': workspace,
        'tasks': page_obj,  # ← paginated
        'page_obj': page_obj,  # ← required for pagination controls
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress': progress_percent,
    })

@login_required
def invite_user(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            existing_user = User.objects.filter(email=email).first()
            already_member = existing_user in workspace.members.all() if existing_user else False

            if already_member:
                messages.error(request, f"{email} is already a member of this workspace.")
            else:
                # Create invitation token
                token = get_random_string(length=64)
                invitation = Invitation.objects.create(
                    email=email,
                    token=token,
                    workspace=workspace,
                    invited_by=request.user
                )

                # Construct invitation link
                invite_url = request.build_absolute_uri(
                    reverse('accept_invite', args=[token])
                )

                # Send invitation email
                send_mail(
                    subject=f"You've been invited to join '{workspace.name}' on TaskManager",
                    message=(
                        f"Hi,\n\n"
                        f"You've been invited by {request.user.username} to join the workspace '{workspace.name}'.\n"
                        f"Click the link below to accept the invitation:\n\n{invite_url}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )

                messages.success(request, f"Invitation sent to {email}.")
                return redirect('invite_user', workspace_id=workspace_id)
    else:
        form = InvitationForm()

    return render(request, 'tasks/invite_user.html', {
        'form': form,
        'workspace': workspace
    })

def accept_invite(request, token):
    invitation = get_object_or_404(Invitation, token=token)

    if invitation.accepted:
        messages.info(request, "This invitation has already been accepted.")
        return redirect('login')

    # If user not logged in → store token in session and redirect to login/signup
    if not request.user.is_authenticated:
        request.session['invitation_token'] = token
        messages.info(request, "Please login or register to accept the invitation.")
        return redirect('login')

    # If user is logged in, accept invitation
    workspace = invitation.workspace
    workspace.members.add(request.user)
    invitation.accepted = True
    invitation.save()

    messages.success(request, f"You've joined the workspace '{workspace.name}'.")
    return redirect('invite_user', workspace_id=workspace.id)

@login_required
def create_workspace(request):
    if request.method == 'POST':
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            workspace = form.save(commit=False)
            workspace.owner = request.user
            workspace.save()
            workspace.members.add(request.user)
            messages.success(request, 'Workspace created!')
            return redirect('workspace_dashboard', workspace_id=workspace.id)
    else:
        form = WorkspaceForm()
    return render(request, 'tasks/create_workspace.html', {'form': form})

def create_workspace_task(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if request.method == 'POST':
        form = WorkspaceTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.workspace = workspace
            task.created_by = request.user  # optional field, if you track who created it
            task.owner = request.user       # ✅ FIX: assign required field
            task.save()
            messages.success(request, "Task created successfully!")
            return redirect('workspace_dashboard', workspace_id=workspace.id)
    else:
        form = WorkspaceTaskForm()

    return render(request, 'tasks/create_workspace_task.html', {'form': form, 'workspace': workspace})



@login_required
def post_login_redirect(request):
    token = request.session.pop('invitation_token', None)
    if token:
        return redirect('accept_invite', token=token)
    return redirect('dashboard')  # fallback

@require_POST
@login_required
def update_task_status(request):
    task_id = request.POST.get('task_id')
    new_status = request.POST.get('status')

    task = get_object_or_404(Task, id=task_id)

    if request.user != task.owner and request.user not in task.workspace.members.all():
        messages.error(request, "You do not have permission to update this task.")
        return redirect('workspace_dashboard', workspace_id=task.workspace.id)

    task.status = new_status
    if new_status == 'COMPLETED' and not task.completed_at:
        task.completed_at = timezone.now().date()
    elif new_status != 'COMPLETED':
        task.completed_at = None
    task.save()

    messages.success(request, "Task status updated.")
    return redirect('workspace_dashboard', workspace_id=task.workspace.id)


# tasks/views.py

def reminders_view(request):
    today = localdate()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    user = request.user

    # Only show TODO or INPROGRESS tasks
    active_statuses = ["TODO", "INPROGRESS"]
    REMINDER_LIMIT=5
    reminders = {
        "Today": Task.objects.filter(owner=user, status__in=active_statuses).filter(
            Q(reminder_date=today) | Q(due_date=today)
        ).distinct()[:REMINDER_LIMIT],
        "Tomorrow": Task.objects.filter(owner=user, status__in=active_statuses).filter(
            Q(reminder_date=tomorrow) | Q(due_date=tomorrow)
        ).distinct()[:REMINDER_LIMIT],
        "This Week": Task.objects.filter(owner=user, status__in=active_statuses).filter(
            Q(reminder_date__gt=tomorrow, reminder_date__lte=week_end) |
            Q(due_date__gt=tomorrow, due_date__lte=week_end)
        ).distinct()[:REMINDER_LIMIT],
        "All": Task.objects.filter(owner=user, status__in=active_statuses).filter(
            Q(reminder_date__isnull=False) | Q(due_date__isnull=False)
        ).distinct()[:REMINDER_LIMIT],
    }

    for key, qs in reminders.items():
        print(f"{key}: {qs.count()} reminders")

    return render(request, 'tasks/reminders.html', {
        "reminders": reminders,
        "current_date": today,
    })

@login_required
def quick_add_reminder(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        days_ahead = int(request.POST.get('days_ahead', 0))
        reminder_date = timezone.now().date() + timedelta(days=days_ahead)

        Task.objects.create(
            title=title,
            description="Auto-created test reminder",
            owner=request.user,
            reminder_date=reminder_date
        )
        return redirect('reminders_view')

    return render(request, 'tasks/test_add_reminder.html')

def view_more_reminders(request, category):
    today = localdate()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    user = request.user

    if category == "Today":
        task_qs = Task.objects.filter(owner=user).filter(
            Q(reminder_date=today) | Q(due_date=today)
        ).order_by('due_date')
    elif category == "Tomorrow":
        task_qs = Task.objects.filter(owner=user).filter(
            Q(reminder_date=tomorrow) | Q(due_date=tomorrow)
        ).order_by('due_date')
    elif category == "This Week":
        task_qs = Task.objects.filter(owner=user).filter(
            Q(reminder_date__gt=tomorrow, reminder_date__lte=week_end) |
            Q(due_date__gt=tomorrow, due_date__lte=week_end)
        ).order_by('due_date')
    elif category == "All":
        task_qs = Task.objects.filter(owner=user).filter(
            Q(reminder_date__isnull=False) | Q(due_date__isnull=False)
        ).order_by('reminder_date')
    else:
        task_qs = Task.objects.none()

    # Add pagination
    paginator = Paginator(task_qs, 6)  # Show 5 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tasks/view_more_reminders.html', {
        'tasks': page_obj,
        'category': category,
        'current_date': today,
        'page_obj': page_obj,  # Needed for pagination UI
    })

def edit_reminder_task(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully from reminder.')
            return redirect('reminders')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/edit_reminder_task.html', {'form': form})

def send_reminder_notification(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    send_mail(
        subject=f"Reminder: {task.title}",
        message=f"This is a reminder for your task: {task.title}\nDue on: {task.due_date}\nDescription: {task.description}",
        from_email='noreply@yourdomain.com',
        recipient_list=[request.user.email],
        fail_silently=False,
    )
    messages.success(request, 'Reminder email sent!')
    return redirect('reminders')


@login_required
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request,f'Welcome, {user.username}! Your account has been created.')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'tasks/register.html', {'form': form})

@login_required
def task_list(request):
    selected_month = request.GET.get('month')
    start = request.GET.get('start')
    end = request.GET.get('end')
    filter_val = request.GET.get('filter')

    tasks = Task.objects.filter(owner=request.user).order_by('due_date')

    # Filter by status
    if filter_val == 'completed':
        tasks = tasks.filter(status='COMPLETED')
    elif filter_val == 'pending':
        tasks = tasks.exclude(status='COMPLETED')
    elif filter_val == 'today':
        from datetime import date
        tasks = tasks.filter(due_date=date.today())
    elif filter_val == 'week':
        from datetime import date, timedelta
        today = date.today()
        week_end = today + timedelta(days=7)
        tasks = tasks.filter(due_date__range=(today, week_end))

    # Filter by month
    if selected_month:
        tasks = tasks.filter(due_date__month=int(selected_month))

    # Filter by date range
    if start and end:
        tasks = tasks.filter(due_date__range=[start, end])

    # Prepare months dictionary like {1: 'January', ...}
    months = {i: month_name[i] for i in range(1, 13)}
    selected_month_name = months.get(int(selected_month)) if selected_month else ''

    paginator = Paginator(tasks, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "tasks": page_obj,
        "filter_val": filter_val,
        "selected_month": int(selected_month) if selected_month else '',
        "selected_month_name": selected_month_name,
        "start": start,
        "end": end,
        "months": months,
    }
    return render(request, "tasks/home.html", context)

@login_required
def home(request):
    tasks_queryset = Task.objects.filter(owner=request.user).order_by('due_date')

    # --- Filters ---
    filter_val = request.GET.get('filter')
    selected_month = request.GET.get('month')
    start = request.GET.get('start')
    end = request.GET.get('end')
    today = date.today()
    query = request.GET.get('q', '').strip()

    # Filter by status
    if filter_val == 'completed':
        tasks_queryset = tasks_queryset.filter(status='COMPLETED')
    elif filter_val == 'pending':
        tasks_queryset = tasks_queryset.exclude(status='COMPLETED')
    elif filter_val == 'today':
        tasks_queryset = tasks_queryset.filter(due_date=today)
    elif filter_val == 'week':
        end_date = today + timedelta(days=7)
        tasks_queryset = tasks_queryset.filter(due_date__range=[today, end_date])

    # Filter by selected month
    if selected_month:
        tasks_queryset = tasks_queryset.filter(due_date__month=int(selected_month))

    # Filter by date range
    if start and end:
        tasks_queryset = tasks_queryset.filter(due_date__range=[start, end])
        if selected_month:
            tasks_queryset=tasks_queryset.filter(due_date__month=int(selected_month))
    elif start:
        tasks_queryset = tasks_queryset.filter(due_date__gte=start)
        if selected_month:
            tasks_queryset=tasks_queryset.filter(due_date__month=int(selected_month))
    elif end:
        tasks_queryset = tasks_queryset.filter(due_date__lte=end)
        if selected_month:
            tasks_queryset=tasks_queryset.filter(due_date__month=int(selected_month))

# 🔍 Search by title or description
    
    if query:
        tasks_queryset = tasks_queryset.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Prepare month list
    months = {i: name for i, name in enumerate(month_name) if i != 0}
    month_dict = dict(months)
    selected_month_name = month_dict.get(int(selected_month)) if selected_month else ''

    # Pagination
    paginator = Paginator(tasks_queryset, 6)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)

    return render(request, 'tasks/home.html', {
        'tasks': tasks,
        'months': months,
        'selected_month': int(selected_month) if selected_month else '',
        'selected_month_name': selected_month_name,
        'filter_val': filter_val,
        'start': start,
        'end': end,
        'query': query,
    })

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save() 
            messages.success(request, "Task created successfully!")
            return redirect('home')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        messages.info(request, "Task Updated successfully")
        return redirect('home')
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == 'POST':
        task.delete()
        messages.error(request, "Task deleted.")
        return redirect('home')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  
    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        response=super().form_valid(form)
        token = self.request.session.pop('invitation_token', None)
        if token:
            return redirect('accept_invite', token=token)

        return response
    




