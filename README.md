# Foodgram Project

Foodgram - это сервис для публикации рецептов. Учебный проект в рамках Яндекс Практикума.

## Технологии

- Python 3.11
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker
- Nginx
- React

## Установка и запуск проекта

### Запуск в Docker

1. Убедитесь, что у вас установлен Docker и Docker Compose.

2. Склонируйте репозиторий
```bash
git clone https://github.com/Tkazarin/foodgram-st.git
```

3. Создайте файл .env (пример .env.example) в директории backend и отредактируйте docker-compose.yml с имеющимися данными

4. Запустите проект, находясь в корневой директории:
```bash
docker-compose up --build -d
```

5. Для окончания работы:
```bash
docker-compose down -v
```

После запуска сервиса будут доступны ссылки:
- [Frontend](http://localhost)
- [Административная панель](http://localhost/admin/)

Данные тестового администратора:
- admin@example.com
- admin

## Автор
Ткаченко Марья,  ИКБО-02-22\
[Почта для связи](tkachenko.m.s@edu.mirea.ru)
