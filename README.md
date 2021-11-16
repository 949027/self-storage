## Описание

Телеграм-бот на основе python-telegram-bot и Django.

Файл скрипта бота находится в папке: \self-storage\tga\ugc\management\commands 

Создать файл .env в корне каталога с проектом и прописать TG_TOKEN = 'токен бота'

До запуска бота:
python manage.py makemigrations
python manage.py migrate

Для админки:
python manage.py createsuperuser
python manage.py runserver
http://127.0.0.1:8000/admin/

Запустить бота:
python manage.py bot
