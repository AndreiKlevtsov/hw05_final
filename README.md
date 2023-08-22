# hw05_final - Проект спринта: подписки на авторов.


### Настройка и запуск на ПК

Клонируем проект:

```bash
git clone git@github.com:AndreiKlevtsov/hw05_final.git
```
```
cd hw05_final
```

Устанавливаем виртуальное окружение:

```bash
python -m venv venv
```

Активируем виртуальное окружение:

```bash
source venv/Scripts/activate
```

Устанавливаем зависимости:

```bash
python -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```

Применяем миграции:

```bash
python yatube/manage.py makemigrations
python yatube/manage.py migrate
```

Создаем супер пользователя:

```bash
python yatube/manage.py createsuperuser
```

Собираем статику:
```bash
python yatube/manage.py collectstatic
```

Создать в корневой директории .env и заполнить:

```
SECRET_KEY='Ваш секретный ключ'
ALLOWED_HOSTS='127.0.0.1, localhost'
DEBUG=True
```

Для запуска тестов:

```bash
pytest
```
Запускаем проект:

```bash
python yatube/manage.py runserver
```

После чего проект будет доступен по адресу разработки.
