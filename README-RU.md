# Docker-исправление для HomeNetworkInventory

Этот архив добавляет контейнерную обвязку, не изменяя исходные файлы приложения в каталоге `app/`.

## Установка

1. Распакуйте содержимое папки `HomeNetworkInventory-docker-fix` в корень репозитория.
2. Разрешите замену файлов `Dockerfile`, `compose.yaml`, `scripts/package_compose.py` и `tests/test_container_config.py`.
3. Создайте `.env` и задайте секрет длиной не менее 32 символов:

   ```env
   SESSION_SECRET=replace-with-a-random-secret-at-least-32-characters
   SESSION_HTTPS_ONLY=false
   ```

4. Соберите и запустите контейнер:

   ```sh
   docker compose up -d --build
   ```

Проверка тестов:

```sh
python -m unittest discover -s tests -v
```

База SQLite сохраняется в Docker volume и доступна контейнеру через `/data`.
