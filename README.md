# TrelloClone - System Zarządzania Projektami

Aplikacja webowa do zarządzania projektami, wzorowana na Trello, zbudowana przy użyciu Django i Bootstrap. Umożliwia tworzenie projektów, zarządzanie zadaniami w formie tablic kanban oraz współpracę w zespole.

## Funkcjonalności

- System autentykacji użytkowników (rejestracja, logowanie)
- Zarządzanie projektami (tworzenie, edycja, usuwanie)
- Kontrola dostępu do projektów (publiczne/prywatne)
- Tablice Kanban dla każdego projektu
- Zarządzanie zadaniami (tworzenie, edycja, usuwanie)
- Drag & drop zadań między kolumnami
- System komentarzy do projektów
- Zarządzanie członkami projektu
- Responsywny interfejs użytkownika

## Wymagania

- Python 3.13+
- Django 5.2.4+
- Pozostałe zależności w pliku requirements.txt

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/yanuzs/TrelloClone.git
cd TrelloClone
```

2. Stwórz i aktywuj wirtualne środowisko:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/MacOS
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

4. Wykonaj migracje bazy danych:
```bash
python manage.py migrate
```

5. Stwórz superużytkownika:
```bash
python manage.py createsuperuser
```

6. Uruchom serwer deweloperski:
```bash
python manage.py runserver
```

Aplikacja będzie dostępna pod adresem `http://127.0.0.1:8000/`

## Struktura projektu

```
TrelloClone/
├── TrelloClone/                # Główny katalog aplikacji
│   ├── templates/trello/       # Szablony HTML
│   ├── static/css/            # Pliki statyczne (CSS)
│   ├── models.py              # Modele bazy danych
│   ├── views.py               # Widoki
│   ├── forms.py              # Formularze
│   └── urls.py               # Konfiguracja URL
├── manage.py                  # Skrypt zarządzający Django
└── requirements.txt          # Zależności projektu
```

## Użycie

1. Zarejestruj się lub zaloguj do systemu
2. Utwórz nowy projekt lub dołącz do istniejącego używając kodu dostępu
3. W ramach projektu możesz:
   - Tworzyć i zarządzać zadaniami
   - Przeciągać zadania między kolumnami
   - Dodawać komentarze
   - Zarządzać członkami projektu

## Role użytkowników

- **Administrator**: Pełny dostęp do wszystkich funkcji systemu
- **Właściciel projektu**: Zarządzanie projektem, zadaniami i członkami
- **Członek projektu**: Praca z zadaniami i komentarzami
- **Niezalogowany użytkownik**: Dostęp tylko do strony logowania i rejestracji

