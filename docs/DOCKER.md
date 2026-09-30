# Запуск Home Network Inventory в Docker

Нужны Docker Engine (либо Docker Desktop с Linux-контейнерами) и Docker Compose v2.

## Первый запуск

В корне проекта скопируйте `.env.example` в `.env`:

```sh
cp .env.example .env
docker run --rm python:3.12-slim-bookworm python -c "import secrets; print(secrets.token_urlsafe(48))"
```

В PowerShell вместо `cp` можно использовать `Copy-Item .env.example .env`.
Вставьте сгенерированную строку после `SESSION_SECRET=` в `.env`, затем:

```sh
docker compose up -d --build
docker compose ps
docker compose logs -f hni
```

Откройте http://localhost:8420. Первый вход: **Admin / Admin**.
Приложение потребует изменить пароль. У существующей базы пароль сохраняется.

По умолчанию порт доступен только на компьютере с Docker. Для доступа из
домашней сети задайте `HNI_BIND_ADDRESS=0.0.0.0` и открывайте
`http://IP-СЕРВЕРА:8420`. `HNI_PORT` меняет внешний порт.

## Данные и обновление

База `/data/home_network.db` хранится в именованном томе `hni_data`.
Фотографии домов также хранятся в базе. Обычный `docker compose down`,
перезапуск и пересоздание контейнера сохраняют том.
**Не выполняйте `docker compose down -v`: этот флаг удаляет данные.**
Сохраняйте имя проекта Compose (имя каталога или параметр `-p`): другое имя
создаст отдельный том и приложение будет выглядеть пустым.

После получения обновлённого исходного кода:

```sh
docker compose up -d --build
```

Перед обновлением сделайте резервную копию. Автоматических миграций существующих
таблиц в исходном приложении нет.

## Резервная копия

Остановите приложение, скопируйте согласованный файл базы и запустите снова:

```sh
docker compose stop hni
docker compose cp hni:/data/home_network.db ./home_network.backup.db
docker compose start hni
```

Храните копию отдельно от Docker-хоста.

## Перенос существующей базы

Остановите старое Python-приложение перед копированием его базы.
Сначала создайте контейнер и том, но не запускайте приложение:

```sh
docker compose build
docker compose create hni
docker compose cp ./home_network.db hni:/data/home_network.db
docker compose run --rm --no-deps --user 0 --cap-add CHOWN hni python -c "import os; os.chown('/data/home_network.db', 10001, 10001)"
docker compose up -d
```

Эти же шаги подходят для восстановления резервной копии: предварительно
остановите контейнер и используйте путь к резервному файлу в команде копирования.
Перед заменой уже существующей базы сохраните её отдельно.

## HTTPS

Для HTTPS через nginx/Caddy/другой reverse proxy задайте
`SESSION_HTTPS_ONLY=true` и пересоздайте контейнер:

```sh
docker compose up -d
```

Для локального HTTP оставьте `false`, иначе браузер не отправит cookie сессии
и вход не сохранится. HTTPS по-прежнему является значением по умолчанию при
запуске Python вне Compose. Сам контейнер принимает HTTP на порту 8420;
сертификат обслуживает reverse proxy.

## Настройки

| Переменная | Назначение |
|---|---|
| `SESSION_SECRET` | Обязательная случайная строка, минимум 32 символа. Не меняйте при обычном перезапуске: изменение завершит старые сессии. |
| `SESSION_HTTPS_ONLY` | Secure cookie: `false` для HTTP, `true` для HTTPS. |
| `SESSION_TIMEOUT_SECONDS` | Тайм-аут неактивной сессии, по умолчанию 7200 секунд. |
| `HNI_BIND_ADDRESS` | Адрес публикации порта Docker, по умолчанию 127.0.0.1. |
| `HNI_PORT` | Внешний порт, по умолчанию 8420. |
| `DATABASE_URL` | В Compose зафиксирован путь `sqlite:////data/home_network.db`. Для другого пути меняйте одновременно том и настройку. |

Вне Docker `SESSION_SECRET` также необходимо передавать через окружение.
Один лишь файл `.env` обычный `python run.py` не читает.
Контейнер запускается с UID/GID 10001, без root, с одним процессом Uvicorn
и без автоматической перезагрузки кода. Если вместо именованного тома используется
папка хоста, дайте UID 10001 права на запись в неё.

## Проверка

```sh
pip install -r requirements.txt httpx==0.28.1
python -m unittest discover -s tests -v
```

Тесты проверяют HTTP/HTTPS cookie, вход, смену пароля и сохранность базы между
процессами. Workflow `.github/workflows/docker.yml` дополнительно собирает образ,
проверяет healthcheck, пользователя и сохранение тома после пересоздания.
