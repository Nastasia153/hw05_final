# Социальная сеть YaTube.


### Установка
Клонировать репозиторий и перейти в него в командной строке:

```
git clone 
```

```
cd yacut
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

* Если у вас Linux/macOS

    ```
    source venv/bin/activate
    ```

* Если у вас windows

    ```
    source venv/scripts/activate
    ```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

### Использование

Создаём базу данных
```
python manage.py migrate
```

Запускаем сервер
```
python manage.py runserver
```

### Технологии

- [Django 2.2](https://www.djangoproject.com/download/)
