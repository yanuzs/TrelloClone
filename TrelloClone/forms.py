from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Project, ProjectComment, Task


class CustomUserCreationForm(UserCreationForm):
    is_superuser = forms.BooleanField(
        required=False,
        label='Superuser',
        help_text='Czy ten użytkownik ma mieć uprawnienia superusera?'
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'is_superuser')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nazwa użytkownika'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Hasło'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Potwierdź hasło'
        })
        self.fields['is_superuser'].widget.attrs.update({
            'class': 'form-check-input'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['is_superuser']:
            user.is_superuser = True
            user.is_staff = True
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nazwa użytkownika'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hasło'
        })
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa projektu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Opis projektu (opcjonalnie)',
                'rows': 4
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class ProjectEditForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'visibility', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa projektu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Opis projektu (opcjonalnie)',
                'rows': 4
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class JoinProjectForm(forms.Form):
    access_code = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wprowadź kod dostępu',
            'style': 'text-transform: uppercase;'
        }),
        label='Kod dostępu do projektu'
    )
    
    def clean_access_code(self):
        code = self.cleaned_data['access_code'].upper()
        try:
            project = Project.objects.get(access_code=code)
            if project.visibility != 'private':
                raise forms.ValidationError('Ten kod nie jest prawidłowy.')
        except Project.DoesNotExist:
            raise forms.ValidationError('Projekt o takim kodzie nie istnieje.')
        return code


class ProjectCommentForm(forms.ModelForm):
    class Meta:
        model = ProjectComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Napisz komentarz...',
                'rows': 3
            })
        }
        labels = {
            'content': 'Komentarz'
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tytuł zadania'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Opis zadania (opcjonalnie)',
                'rows': 3
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
    
    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if project:
            project_members = [project.owner]
            project_members.extend(project.members.all())
            
            self.fields['assigned_to'].queryset = User.objects.filter(
                id__in=[user.id for user in project_members]
            )
            self.fields['assigned_to'].empty_label = "Nie przypisane"


class TaskMoveForm(forms.Form):
    column_id = forms.IntegerField(widget=forms.HiddenInput())
    task_id = forms.IntegerField(widget=forms.HiddenInput())
    position = forms.IntegerField(widget=forms.HiddenInput(), required=False)

# Formularze administracyjne
class AdminUserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Potwierdzenie hasła",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Hasła się nie zgadzają")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdminProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'visibility', 'status', 'owner']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
        }
