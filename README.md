# Тестовое задание компании Облачные Технологии

## Настройка приложения

### Клонирование репозитория
Для клонирования репозитория в локальную директорию ввести команду: 
```
git clone https://github.com/murekswork/stripchat_solution
cd stripchat_solution
```

Для создания виртуального окружения ввести команды:
```
Для linux / mac:
python3 -m venv venv

Для windows:
python -m venv venv
```

### Зависимости
а) Для установки зависимостей в директории с файлом Makefile ввести команды (!нужно чтобы пк мог работать с Make файлами)Ж
```
make deps
make setup-playwright
```
б) Либо открыть Makefile и вручую повторить все команды написанных скриптов в терминале:

### .env файл
Также НЕОБХОДИМО создать .env файл в директории config/ с указанием токена для Twocaptcha вида:
```
#./config/.env

2CAPTCHA_KEY=вашкод

```

## Запуск приложения

### Запуск сервера / миграции
Для проведения миграций запуска сервера в директории config и c активированным venv ввести команду:
```
python manage.py migrate && python manage.py runserver
```
Приложение будет доступно по адресу:
http://localhost:8000/

### Использование приложения
Для входа на сайт сначала нужно создать аккаунт для входа в админке джанго, для входа в которую сначала создать superuser:
```
python manage.py createsuperuser
```
http://localhost:8000/admin

Затем перейти на главная страницу приложения и можно пробовать :)

