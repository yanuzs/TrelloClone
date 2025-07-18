from django.db import models
from django.contrib.auth.models import User
import string
import random


class Project(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Publiczny'),
        ('private', 'Prywatny'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Aktywny'),
        ('completed', 'Zakończony'),
        ('paused', 'Wstrzymany'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Tytuł")
    description = models.TextField(blank=True, verbose_name="Opis")
    visibility = models.CharField(
        max_length=10, 
        choices=VISIBILITY_CHOICES, 
        default='private',
        verbose_name="Widoczność"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Status"
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Data zakończenia")
    access_code = models.CharField(
        max_length=8, 
        unique=True, 
        blank=True,
        verbose_name="Kod dostępu"
    )
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_projects',
        verbose_name="Właściciel"
    )
    members = models.ManyToManyField(
        User, 
        through='ProjectMembership', 
        related_name='projects',
        blank=True,
        verbose_name="Członkowie"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")
    
    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projekty"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.access_code:
            self.access_code = self.generate_access_code()
        if self.status == 'completed' and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        elif self.status != 'completed':
            self.completed_at = None
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.create_default_board()
    
    def generate_access_code(self):
        """Generuje unikalny 8-cyfrowy kod dostępu"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Project.objects.filter(access_code=code).exists():
                return code
    
    def is_accessible_by_user(self, user):
        """Sprawdza czy użytkownik ma dostęp do projektu"""
        if user.is_superuser:
            return True
        if self.visibility == 'public':
            return True
        if self.owner == user:
            return True
        return self.members.filter(id=user.id).exists()
    
    def create_default_board(self):
        """Tworzy domyślną tablicę z 3 kolumnami dla nowego projektu"""
        board = Board.objects.create(project=self)
        
        columns_data = [
            {'name': 'To Do', 'column_type': 'todo', 'position': 1},
            {'name': 'In Progress', 'column_type': 'in_progress', 'position': 2},
            {'name': 'Done', 'column_type': 'done', 'position': 3},
        ]
        
        for col_data in columns_data:
            Column.objects.create(board=board, **col_data)


class ProjectMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'project')
        verbose_name = "Członkostwo w projekcie"
        verbose_name_plural = "Członkostwa w projektach"
    
    def __str__(self):
        return f"{self.user.username} - {self.project.title}"


class ProjectComment(models.Model):
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="Projekt"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Autor"
    )
    content = models.TextField(verbose_name="Treść komentarza")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")
    is_edited = models.BooleanField(default=False, verbose_name="Czy edytowany")
    
    class Meta:
        verbose_name = "Komentarz do projektu"
        verbose_name_plural = "Komentarze do projektów"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Komentarz {self.author.username} - {self.project.title}"
    
    def save(self, *args, **kwargs):
        if self.pk:
            self.is_edited = True
        super().save(*args, **kwargs)


class Board(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='board',
        verbose_name="Projekt"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    
    class Meta:
        verbose_name = "Tablica"
        verbose_name_plural = "Tablice"
    
    def __str__(self):
        return f"Tablica - {self.project.title}"


class Column(models.Model):
    COLUMN_TYPES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name="Tablica"
    )
    name = models.CharField(max_length=100, verbose_name="Nazwa kolumny")
    column_type = models.CharField(
        max_length=20,
        choices=COLUMN_TYPES,
        verbose_name="Typ kolumny"
    )
    position = models.PositiveIntegerField(verbose_name="Pozycja")
    
    class Meta:
        verbose_name = "Kolumna"
        verbose_name_plural = "Kolumny"
        ordering = ['position']
        unique_together = ['board', 'column_type']
    
    def __str__(self):
        return f"{self.name} - {self.board.project.title}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Niska'),
        ('medium', 'Średnia'),
        ('high', 'Wysoka'),
    ]
    
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="Kolumna"
    )
    title = models.CharField(max_length=200, verbose_name="Tytuł zadania")
    description = models.TextField(blank=True, verbose_name="Opis zadania")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Priorytet"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Przypisane do"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name="Utworzone przez"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")
    position = models.PositiveIntegerField(verbose_name="Pozycja w kolumnie")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Termin wykonania")
    
    class Meta:
        verbose_name = "Zadanie"
        verbose_name_plural = "Zadania"
        ordering = ['position']
    
    def __str__(self):
        return self.title
    
    @property
    def project(self):
        return self.column.board.project
