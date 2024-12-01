# Backend-приложение для автоматизации закупок

## Описание проекта

Приложение предназначено для автоматизации закупок в розничной сети через **REST API**.

### Пользователи сервиса:

#### Клиент (покупатель):

1. Может авторизироваться, регистрироваться и восстанавливать пароль через электронную почту, указанную во время регистрации;
2. Делает закупки по каталогу, в котором представлены товары от нескольких поставщиков;
3. В одном заказе может указать товары от разных поставщиков;
4. Для доставки может выбрать адреса, которые созданы им;
5. Получает письмо о смене статуса заказа на электронную почту, указанную при регистрации;
6. Помимо товаров, магазинов, категорий, может так же просматривать информацию о себе, о своих адресах и заказах;
7. Может отменить заказ, если он еще не отправлен по адресу;
8. Может очищать корзину или редактировать перед оформлением заказа

#### Поставщик(магазин):

1. Может добавлять товары по одному или воспользоваться загрузкой товаров через файл формата **yaml**;
2. Может открывать один магазин, если загружать товары через импорт, магазин откроется автоматически;
3. Добавлять товарам категории и характеристики с настраиваемыми полями и значениями;
4. Добавлять новые категории и характеристики для своего товара;
5. Изменять информацию о товаре, его категории и характеристики
6. Может включать и отключать приём заказов;
7. Делает закупки по каталогу, в котором представлены товары от нескольких поставщиков;

#### Менеджер(сотрудник склада)

1. Может просматривать список всех заказов и менять статус (*собран, отправлен, отменен и т.д.*)
2. Собирает заказы согласно информации;
3. Получает письмо на электронную почту, указанную во время регистрации, с информацией о всех созданных заказах и если пользователь сам отменил заказ;

#### Дополнительно реализовано:

1. Рассылка писем, импорт товаров выделены в отдельные асинхронные функции;
2. После оформления заказа, количество остатков на складе автоматически уменьшается на нужное количество;
3. Если товара на складе меньше, чем указано в заказе, заказ нельзя будет оформить;
4. Нельзя положить изначально в корзину товара больше, чем его остаток на складе;
5. Магазин может открыть только поставщик;
6. Добавлять в каталог товары может только активный магазин;
7. Если пользователь сам отменил заказ, менеджер не сможет менять статус заказа


## Запуск проекта

Для запуска проекта в корневой директории необходимо создать файл *.env*, пример в файле *env.example*


## Команда для запуска приложения

```
docker compose up --build -d
```

## Дополнительные команды
Если есть необходимость перезапустить определенные контейнеры:
```bash
docker compose up --build  --no-deps -d имя_контейнера
```
Eсли нужно остановить все контейнеры:
```
docker compose down -v
```
Eсли нужно открыть контейнер в консоли
```
docker compose exec имя_контейнера psql -U имя_пользователя имя_бд
```

### Команды для локальной настройки приложения
Для создания виртуального окружения:
```
python -m venv .venv
```
Активация виртуальной среды для OC Linux
```
source .venv/bin/activate
```
Активация виртуальной среды для OC Windows
```
venv\Scripts\activate
```
Установка зависимостей
```
pip install --upgrade pip -r requirements.txt
poetry install
```
Применение миграций
```
cd app/
alembic upgrade head
```
Для локального запуска приложения на http://127.0.0.1:80/docs#/ (swagger)
```
uvicorn app.main:app --reload
```

### Установка pre-commit

```
pre-commit install
```
Для того чтобы прогнать `pre-commit` до выполнения коммита

```bash
pre-commit run --all-files
```

## Запуск тестов

```
pytest
```
