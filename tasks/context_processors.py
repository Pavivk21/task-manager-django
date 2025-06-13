from .models import Workspace

def workspace_context(request):
    if request.user.is_authenticated:
        owned = Workspace.objects.filter(owner=request.user)
        joined = Workspace.objects.filter(members=request.user).exclude(owner=request.user)
        return {
            'owned_workspaces': owned,
            'joined_workspaces': joined
        }
    return {}
