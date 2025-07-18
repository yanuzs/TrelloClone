from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from .forms import CustomUserCreationForm, LoginForm, ProjectForm, JoinProjectForm, ProjectEditForm, ProjectCommentForm, TaskForm, TaskMoveForm
from .models import Project, ProjectMembership, ProjectComment, Board, Column, Task


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Witaj {username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')
    else:
        form = LoginForm()
    
    return render(request, 'trello/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            is_superuser = form.cleaned_data.get('is_superuser')
            
            if is_superuser:
                messages.success(request, f'Konto superusera {username} zostało utworzone!')
            else:
                messages.success(request, f'Konto użytkownika {username} zostało utworzone!')
            
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'trello/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Zostałeś wylogowany.')
    return redirect('login')


@login_required
def dashboard_view(request):
    join_form = JoinProjectForm()
    
    if request.method == 'POST' and 'join_project' in request.POST:
        join_form = JoinProjectForm(request.POST)
        if join_form.is_valid():
            access_code = join_form.cleaned_data['access_code']
            try:
                project = Project.objects.get(access_code=access_code)
                if not project.is_accessible_by_user(request.user):
                    ProjectMembership.objects.get_or_create(
                        user=request.user, 
                        project=project
                    )
                    messages.success(request, f'Dołączyłeś do projektu "{project.title}"!')
                else:
                    messages.info(request, f'Już masz dostęp do projektu "{project.title}".')
            except Project.DoesNotExist:
                messages.error(request, 'Nieprawidłowy kod dostępu.')
            return redirect('dashboard')
    
    if request.user.is_superuser:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(
            Q(owner=request.user) | 
            Q(visibility='public') | 
            Q(members=request.user)
        ).distinct()
    
    context = {
        'user': request.user,
        'projects': projects,
        'join_form': join_form,
    }
    return render(request, 'trello/dashboard.html', context)


@login_required
def create_project_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            
            messages.success(
                request, 
                f'Projekt "{project.title}" został utworzony! '
                f'Kod dostępu: {project.access_code}'
            )
            return redirect('dashboard')
    else:
        form = ProjectForm()
    
    return render(request, 'trello/create_project.html', {'form': form})


@login_required
def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if not project.is_accessible_by_user(request.user):
        messages.error(request, 'Nie masz dostępu do tego projektu.')
        return redirect('dashboard')
    
    is_member = (project.owner == request.user or 
                project.members.filter(id=request.user.id).exists())
    
    board, created = Board.objects.get_or_create(project=project)
    if created:
        project.create_default_board()
        board.refresh_from_db()
    
    columns = board.columns.prefetch_related('tasks__assigned_to', 'tasks__created_by').all()
    
    comment_form = ProjectCommentForm()
    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_form = ProjectCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.project = project
            comment.author = request.user
            comment.save()
            messages.success(request, 'Komentarz został dodany!')
            return redirect('project_detail', project_id=project_id)
    
    comments = project.comments.all().order_by('created_at')
    
    context = {
        'project': project,
        'board': board,
        'columns': columns,
        'is_member': is_member,
        'is_owner': project.owner == request.user,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'trello/project_detail.html', context)


@login_required
def edit_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if project.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Nie masz uprawnień do edycji tego projektu.')
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        form = ProjectEditForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Projekt został zaktualizowany!')
            return redirect('project_detail', project_id=project_id)
    else:
        form = ProjectEditForm(instance=project)
    
    context = {
        'form': form,
        'project': project,
    }
    return render(request, 'trello/edit_project.html', context)


@login_required
def delete_comment_view(request, project_id, comment_id):
    project = get_object_or_404(Project, id=project_id)
    comment = get_object_or_404(ProjectComment, id=comment_id, project=project)
    
    if (comment.author != request.user and 
        project.owner != request.user and 
        not request.user.is_superuser):
        return HttpResponseForbidden('Nie masz uprawnień do usunięcia tego komentarza.')
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Komentarz został usunięty.')
    
    return redirect('project_detail', project_id=project_id)


@login_required
def edit_comment_view(request, project_id, comment_id):
    project = get_object_or_404(Project, id=project_id)
    comment = get_object_or_404(ProjectComment, id=comment_id, project=project)
    
    if comment.author != request.user and not request.user.is_superuser:
        messages.error(request, 'Nie masz uprawnień do edycji tego komentarza.')
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        form = ProjectCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Komentarz został zaktualizowany!')
            return redirect('project_detail', project_id=project_id)
    else:
        form = ProjectCommentForm(instance=comment)
    
    context = {
        'form': form,
        'project': project,
        'comment': comment,
    }
    return render(request, 'trello/edit_comment.html', context)


@login_required
def add_task_view(request, project_id, column_id):
    project = get_object_or_404(Project, id=project_id)
    column = get_object_or_404(Column, id=column_id, board__project=project)
    
    if not project.is_accessible_by_user(request.user):
        messages.error(request, 'Nie masz dostępu do tego projektu.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TaskForm(project=project, data=request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.column = column
            task.created_by = request.user
            
            max_position = column.tasks.aggregate(Max('position'))['position__max']
            task.position = (max_position or 0) + 1
            
            task.save()
            messages.success(request, 'Zadanie zostało dodane!')
            return redirect('project_detail', project_id=project_id)
    else:
        form = TaskForm(project=project)
    
    context = {
        'form': form,
        'project': project,
        'column': column,
    }
    return render(request, 'trello/add_task.html', context)


@login_required
def edit_task_view(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(Task, id=task_id, column__board__project=project)
    
    if not project.is_accessible_by_user(request.user):
        messages.error(request, 'Nie masz dostępu do tego projektu.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TaskForm(project=project, data=request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zadanie zostało zaktualizowane!')
            return redirect('project_detail', project_id=project_id)
    else:
        form = TaskForm(project=project, instance=task)
    
    context = {
        'form': form,
        'project': project,
        'task': task,
    }
    return render(request, 'trello/edit_task.html', context)


@login_required
@require_POST
def delete_task_view(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(Task, id=task_id, column__board__project=project)
    
    if (task.created_by != request.user and 
        project.owner != request.user and 
        not request.user.is_superuser):
        return HttpResponseForbidden('Nie masz uprawnień do usunięcia tego zadania.')
    
    task.delete()
    messages.success(request, 'Zadanie zostało usunięte.')
    return redirect('project_detail', project_id=project_id)


@login_required
@require_POST
def move_task_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if not project.is_accessible_by_user(request.user):
        return JsonResponse({'success': False, 'error': 'Brak dostępu'})
    
    form = TaskMoveForm(request.POST)
    if form.is_valid():
        task_id = form.cleaned_data['task_id']
        column_id = form.cleaned_data['column_id']
        new_position = form.cleaned_data.get('position', 1)
        
        try:
            task = Task.objects.get(id=task_id, column__board__project=project)
            new_column = Column.objects.get(id=column_id, board__project=project)
            
            task.column = new_column
            task.position = new_position or 1
            task.save()
            
            return JsonResponse({'success': True})
        except (Task.DoesNotExist, Column.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Zadanie lub kolumna nie istnieje'})
    
    return JsonResponse({'success': False, 'error': 'Nieprawidłowe dane'})
