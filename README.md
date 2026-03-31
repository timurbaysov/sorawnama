# NMTU PsychTest

Веб-приложение для психологических опросов студентов с тремя языками интерфейса (UZ / KK / RU), ролями пользователей и аналитикой результатов.

## 1) Что это за проект

Сайт решает 4 основные задачи:

- регистрация и вход студентов;
- создание и редактирование опросов психологом/админом;
- прохождение опросов студентами (одна попытка на вопрос);
- просмотр статистики и выявление группы риска по красным ответам.

## 2) Технологии

- Python 3.12+ (рекомендуется 3.12/3.13)
- Django 5.x
- PostgreSQL
- psycopg3 (`psycopg[binary]`)
- HTML + CSS (шаблоны Django)

Файл зависимостей: [requirements.txt](file:///e:/dart/PythonProject1/requirements.txt)

## 3) Архитектура проекта (где что находится)

Корень проекта: `e:\dart\PythonProject1`

- `manage.py` — точка входа для команд Django.
- `student_psychology/` — конфигурация проекта:
  - [settings.py](file:///e:/dart/PythonProject1/student_psychology/settings.py) — настройки (БД, middleware, языки, static и т.д.).
  - [urls.py](file:///e:/dart/PythonProject1/student_psychology/urls.py) — корневые маршруты.
  - `wsgi.py` / `asgi.py` — запуск приложения сервером.
- `surveys/` — основное приложение:
  - [models.py](file:///e:/dart/PythonProject1/surveys/models.py) — модели БД.
  - [views.py](file:///e:/dart/PythonProject1/surveys/views.py) — бизнес-логика.
  - [urls.py](file:///e:/dart/PythonProject1/surveys/urls.py) — маршруты приложения.
  - [forms.py](file:///e:/dart/PythonProject1/surveys/forms.py) — формы и валидация.
  - [middleware.py](file:///e:/dart/PythonProject1/surveys/middleware.py) — кастомная языковая middleware.
  - `templatetags/` — кастомные теги для шаблонов.
  - [translations.json](file:///e:/dart/PythonProject1/surveys/translations.json) — словарь переводов UI.
  - `migrations/` — миграции схемы БД.
- `templates/` — HTML-шаблоны:
  - [base.html](file:///e:/dart/PythonProject1/templates/base.html) — базовый макет.
  - `templates/surveys/*.html` — страницы опросов, статистики, профиля.
  - `templates/registration/*.html` — страницы входа/регистрации.
- `static/css/styles.css` — основные стили интерфейса.
- `locale/` — файлы локализации Django (`.po/.mo`).

## 4) Маршруты (URL)

Корневые маршруты: [student_psychology/urls.py](file:///e:/dart/PythonProject1/student_psychology/urls.py)

- `/admin/` — Django Admin
- `/accounts/login/` — вход пользователя
- `/accounts/...` — встроенные auth-маршруты Django
- `/` и остальные — маршруты из приложения `surveys`

Маршруты опросов: [surveys/urls.py](file:///e:/dart/PythonProject1/surveys/urls.py)

- `/` — список опросов
- `/profile/` — профиль
- `/register/` — регистрация студента
- `/set-language/` — смена языка сайта
- `/survey/create/` — создание опроса
- `/survey/<id>/edit/` — редактирование
- `/survey/<id>/delete/` — удаление
- `/survey/<id>/` — прохождение опроса
- `/survey/<id>/statistics/` — аналитика

## 5) Роли и права доступа

- **Студент**
  - проходит опросы;
  - видит свой профиль;
  - не может редактировать/создавать опросы.

- **Психолог (`is_staff` или профиль психолога)**
  - создает/редактирует/удаляет опросы;
  - видит статистику и группу риска.

- **Суперадмин**
  - полный доступ;
  - вход через `/admin/`;
  - доступ к admin-tools (создание психологов, список пользователей).

## 6) Блок-схема работы

```text
Психолог/Админ
    │
    ├── Создает опрос (Survey)
    │       └── Добавляет вопросы (Question)
    │               └── Добавляет варианты (Option: RED/YELLOW/GREEN)
    │
Студент
    │
    └── Проходит опрос
            └── По каждому вопросу сохраняется Answer(student, question, option)
                    └── Уникальность: 1 студент = 1 ответ на 1 вопрос

Статистика
    │
    ├── Подсчет RED/YELLOW/GREEN по всем ответам
    ├── Список прошедших студентов
    └── Группа риска (где RED доминирует), сортировка по убыванию RED
```

## 7) База данных (подробно)

См. модели: [models.py](file:///e:/dart/PythonProject1/surveys/models.py)

### 7.1 Таблицы и поля

1. `auth_user` (стандарт Django)
- `id`, `username`, `password`, `email`, `is_active`, `is_staff`, `is_superuser`, ...

2. `surveys_student`
- `id`
- `user_id` (OneToOne -> `auth_user`)
- `group_code` (шифр группы)
- `course` (1..4)

3. `surveys_psychologist`
- `id`
- `user_id` (OneToOne -> `auth_user`)

4. `surveys_survey`
- `id`
- `title_uz`, `title_kk`, `title_ru`
- `created_by_id` (FK -> `surveys_psychologist`, может быть `NULL`)
- `created_at`

5. `surveys_question`
- `id`
- `survey_id` (FK -> `surveys_survey`)
- `text_uz`, `text_kk`, `text_ru`

6. `surveys_option`
- `id`
- `question_id` (FK -> `surveys_question`)
- `text_uz`, `text_kk`, `text_ru`
- `value` (1=RED, 2=YELLOW, 3=GREEN)
- `order` (порядок отображения)

7. `surveys_answer`
- `id`
- `student_id` (FK -> `surveys_student`)
- `question_id` (FK -> `surveys_question`)
- `selected_option_id` (FK -> `surveys_option`)
- `submitted_at`
- ограничение уникальности: `(student_id, question_id)` — один ответ на вопрос

### 7.2 Связи

```text
User 1─1 Student
User 1─1 Psychologist
Psychologist 1─N Survey
Survey 1─N Question
Question 1─N Option
Student N─N Question (через Answer)
```

### 7.3 Как работает многоязычность данных

- Контент опросов хранится сразу в трех полях (`*_uz`, `*_kk`, `*_ru`).
- Методы `localized_title()` и `localized_text()` выбирают нужный язык с fallback.
- Язык интерфейса хранится в сессии (`site_language`) через [middleware.py](file:///e:/dart/PythonProject1/surveys/middleware.py).

## 8) Локальный запуск (с нуля)

### 8.1 Установка

```bash
git clone <ВАШ_РЕПО_URL>
cd PythonProject1
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 8.2 Поднять PostgreSQL

Создайте БД и пользователя (пример):

```sql
CREATE DATABASE student_surveys_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE student_surveys_db TO postgres;
```

### 8.3 Переменные окружения

В PowerShell перед запуском:

```powershell
$env:POSTGRES_DB="student_surveys_db"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="postgres"
$env:POSTGRES_HOST="127.0.0.1"
$env:POSTGRES_PORT="5432"
```

### 8.4 Миграции и запуск

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Сайт: `http://127.0.0.1:8000`  
Админка: `http://127.0.0.1:8000/admin`

## 9) Деплой на сервер с нуля до продакшена (Ubuntu + Gunicorn + Nginx)

Ниже полный минимальный production-сценарий.

### Шаг 1. Подготовить сервер

Подключитесь по SSH и установите пакеты:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx git
```

### Шаг 2. Создать системного пользователя для проекта

```bash
sudo adduser --disabled-password --gecos "" psychapp
sudo usermod -aG www-data psychapp
```

### Шаг 3. Клонировать проект

```bash
sudo -u psychapp -H bash -c '
cd ~
git clone <ВАШ_РЕПО_URL> app
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
'
```

### Шаг 4. Настроить PostgreSQL

```bash
sudo -u postgres psql
```

Внутри `psql`:

```sql
CREATE DATABASE student_surveys_db;
CREATE USER psych_user WITH PASSWORD 'СЛОЖНЫЙ_ПАРОЛЬ';
GRANT ALL PRIVILEGES ON DATABASE student_surveys_db TO psych_user;
\q
```

### Шаг 5. Подготовить `.env`

Создайте файл `~/app/.env`:

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=СЛОЖНЫЙ_СЕКРЕТ
DJANGO_ALLOWED_HOSTS=ваш.домен,IP_СЕРВЕРА
POSTGRES_DB=student_surveys_db
POSTGRES_USER=psych_user
POSTGRES_PASSWORD=СЛОЖНЫЙ_ПАРОЛЬ
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Примечание: в текущем `settings.py` нужно использовать эти переменные для `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`. Сейчас там dev-значения.

### Шаг 6. Применить миграции и собрать static

```bash
sudo -u psychapp -H bash -c '
cd ~/app
source .venv/bin/activate
export POSTGRES_DB=student_surveys_db
export POSTGRES_USER=psych_user
export POSTGRES_PASSWORD=СЛОЖНЫЙ_ПАРОЛЬ
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
'
```

### Шаг 7. Настроить systemd для Gunicorn

Создайте `/etc/systemd/system/psychtest.service`:

```ini
[Unit]
Description=Gunicorn for NMTU PsychTest
After=network.target

[Service]
User=psychapp
Group=www-data
WorkingDirectory=/home/psychapp/app
Environment="POSTGRES_DB=student_surveys_db"
Environment="POSTGRES_USER=psych_user"
Environment="POSTGRES_PASSWORD=СЛОЖНЫЙ_ПАРОЛЬ"
Environment="POSTGRES_HOST=127.0.0.1"
Environment="POSTGRES_PORT=5432"
ExecStart=/home/psychapp/app/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8001 student_psychology.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Примените:

```bash
sudo systemctl daemon-reload
sudo systemctl enable psychtest
sudo systemctl start psychtest
sudo systemctl status psychtest
```

### Шаг 8. Настроить Nginx

Создайте `/etc/nginx/sites-available/psychtest`:

```nginx
server {
    listen 80;
    server_name ваш.домен IP_СЕРВЕРА;

    client_max_body_size 20M;

    location /static/ {
        alias /home/psychapp/app/static/;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8001;
    }
}
```

Активируйте:

```bash
sudo ln -s /etc/nginx/sites-available/psychtest /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Шаг 9. SSL (HTTPS) через Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ваш.домен
```

Проверка автообновления сертификата:

```bash
sudo certbot renew --dry-run
```

## 10) Что обязательно сделать перед production

- вынести `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` в переменные окружения;
- поставить `DEBUG=False`;
- ограничить доступ к БД по сети и использовать сложный пароль;
- включить HTTPS;
- настроить резервные копии БД (pg_dump + cron);
- следить за логами `journalctl -u psychtest -f` и `sudo tail -f /var/log/nginx/error.log`.

## 11) Полезные команды

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py runserver
```

Для сервера:

```bash
sudo systemctl restart psychtest
sudo systemctl restart nginx
sudo systemctl status psychtest
```

