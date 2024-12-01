# Backend-приложение для автоматизации закупок

## Настройка проекта

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -r requirements.txt
poetry install
```

### Установка pre-commit hooks

Установка хуков

```bash
pre-commit install
```

Для того чтобы прогнать `pre-commit` до выполнения коммита

```bash
pre-commit run --all-files
```


### Запуск проекта

Для запуска docker compose пректа нужно создать файл .env, пример в файле *env.example*


### Команды для docker compose

```bash
docker compose up --build -d
docker compose up --build  --no-deps -d имена контейнеров которые надо перезапустить через пробел
docker compose down -v
docker compose exec имя_контейнера psql -U имя_пользователя имя_бд
```

### Запуск тестов

```bash
pytest
```
