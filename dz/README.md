# Домашнее задание

## Вариант №14

Разработать инструмент командной строки для учебного конфигурационного языка, синтаксис которого приведен далее \
Этот инструмент преобразует текст из входного формата в выходной. Синтаксические ошибки выявляются с выдачей сообщений

Входной текст на учебном конфигурационном языке принимается из стандартного ввода. Выходной текст на языке json попадает в файл, путь к которому задан ключом командной строки

Числа: `[+-]?\d+`

Словари:
```
begin
имя := значение;
имя := значение;
имя := значение;
...
end
```

Имена: `[A-Z]+`

Значения:
- Числа
- Строки
- Словари

Строки: `q(Это строка)`

Объявление константы на этапе трансляции: `имя is значение`

Вычисление константного выражения на этапе трансляции (инфиксная форма), пример: `|имя + 1|`

Результатом вычисления константного выражения является значение \
Для константных вычислений определены операции и функции:
1. Сложение
2. Вычитание
3. Умножение
4. ord()

Все конструкции учебного конфигурационного языка (с учетом их возможной вложенности) должны быть покрыты тестами

Необходимо показать 3 примера описания конфигураций из разных предметных областей

## Использование

Для запуска парсера, передайте текст на вход через стандартный ввод и укажите выходной файл с помощью флага `--output`

## Примеры

### Игровой уровень

```commandline
cat ./input/game_level.txt | python main.py --output ./output/game_level.json
```

[Ввод:](./input/game_level.txt)
```text
LEVEL_NAME is q(RTU MIREA)
DIFFICULTY is 3

begin
    NAME := LEVEL_NAME;
    TIME_LIMIT := 5400;
    STUDENTS_COUNT := |DIFFICULTY * 1500|;
    HAZARDS := begin
        DOORS := 10;
        TEACHERS := 52;
    end;
    SECRET_ITEMS := 3;
end
```

[Вывод:](./output/game_level.json)
```json
{
    "NAME": "RTU MIREA",
    "TIME_LIMIT": 5400,
    "STUDENTS_COUNT": 4500,
    "HAZARDS": {
        "DOORS": 10,
        "TEACHERS": 52
    },
    "SECRET_ITEMS": 3
}
```

### Конфигурация сервера

```bash
cat ./input/server_config.txt | python main.py --output ./output/server_config.json
```

[Ввод:](./input/server_config.txt)
```text
HOST is q(web.telegram.org)
PORT is 443

begin
    APP_NAME := q(WebTgClient);
    DEBUG_MODE := q(false);
    DATABASE_URL := q(postgres://user:password@host:5432/dbname);
    RESOURCES := begin
        CPU_LIMIT := q(500m);
        MEM_LIMIT := q(1G);
    end;
    API_PORT := PORT;
end
```

[Вывод:](./output/server_config.json)
```json
{
    "APP_NAME": "WebTgClient",
    "DEBUG_MODE": "false",
    "DATABASE_URL": "postgres://user:password@host:5432/dbname",
    "RESOURCES": {
        "CPU_LIMIT": "500m",
        "MEM_LIMIT": "1G"
    },
    "API_PORT": 443
}
```

### Профиль пользователя

```commandline
cat ./input/user_profile.txt | python main.py --output ./output/user_profile.json
```

[Ввод:](./input/user_profile.txt)
```text
USER_ID is 1
USERNAME is q(K1rLes)

begin
    DISPLAY_NAME := USERNAME;
    AVATAR_URL := q(https://k1rles.ru/static/images/profile.jpg);
    LEVEL := 19;
    XP := 6935;
    SETTINGS := begin
        SHOW_ONLINE_STATUS := q(true);
        THEME := q(dark-blue);
    end;
end
```

[Вывод:](./output/user_profile.json)
```json
{
    "DISPLAY_NAME": "K1rLes",
    "AVATAR_URL": "https://k1rles.ru/static/images/profile.jpg",
    "LEVEL": 19,
    "XP": 6935,
    "SETTINGS": {
        "SHOW_ONLINE_STATUS": "true",
        "THEME": "dark-blue"
    }
}
```
