# Готовый пакет Docker Compose

Пакет содержит настройки запуска. Сам образ загружается из GitHub Container
Registry; Python и исходный код на сервере не нужны. Нужны Docker с поддержкой
Linux-контейнеров и Docker Compose v2. Образ собирается для amd64 и arm64.

## Запуск

1. Распакуйте архив в постоянную папку, например `hni`.
2. Скопируйте `.env.example` в `.env`.
3. Создайте секрет командой ниже и вставьте его в `SESSION_SECRET=` в `.env`:

```sh
docker run --rm python:3.12-slim-bookworm python -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose pull
docker compose up -d --wait
```

Откройте http://localhost:8420. Первый вход: **Admin / Admin**, затем смена
пароля обязательна. Для доступа с другого компьютера в локальной сети задайте
в `.env` `HNI_BIND_ADDRESS=0.0.0.0` и открывайте `http://IP-СЕРВЕРА:8420`.
При доступе через HTTPS reverse proxy задайте `SESSION_HTTPS_ONLY=true`.

База и фотографии хранятся в томе `hni_data`. Не удаляйте том и не используйте
`docker compose down -v`. Сохранение данных требует постоянного имени проекта
Compose: используйте ту же папку или одинаковое значение `-p`.

## Обновление

Сделайте резервную копию базы (см. DOCKER.md). Замените `compose.yaml` новым
файлом из следующего пакета, сохранив свою `.env` и имя папки, затем:

```sh
docker compose pull
docker compose up -d --wait
```

Пакет фиксирует образ по digest, поэтому обновление `latest` само по себе его
не меняет. Точный образ указан в `IMAGE.txt`. Это предотвращает незаметное
обновление при перезапуске. Пакет не содержит готовой базы или секретов.

Для переноса существующей базы используйте раздел переноса в `DOCKER.md`,
заменив `docker compose build` на `docker compose pull`: сборка относится
только к варианту запуска из исходного репозитория.

## Доступ к GHCR

Первый опубликованный GHCR-пакет по умолчанию приватный, даже у публичного
репозитория. Для скачивания без авторизации владелец должен открыть пакет
в GitHub → Packages → Package settings → Change visibility → Public.
Либо выполните `docker login ghcr.io -u ВАШ_ЛОГИН`, используя personal access
token (classic) с правом `read:packages` как пароль.

## Как пакет создаётся

Workflow **Docker package** сначала проверяет приложение и контейнер.
На `main`, при ручном запуске на `main` и для тегов `v*` затем публикует образ
в `ghcr.io/<владелец>/<репозиторий-в-нижнем-регистре>` и проверяет запуск
опубликованного образа через Compose на amd64. ARM64 собирается, но отдельный
тест запуска на ARM в этом workflow не выполняется.

Архив находится в Actions → завершённый запуск → Artifacts →
`home-network-inventory-compose`. При теге `v*` архив также прикрепляется
к GitHub Release этого тега. В pull request выполняются проверки без публикации.
Дополнительные секреты в GitHub не нужны: используется `GITHUB_TOKEN` с
`packages: write`; создание Release отдельно получает `contents: write`.

Источники: [Docker Actions](https://docs.docker.com/build/ci/github-actions/push-multi-registries/),
[GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).
