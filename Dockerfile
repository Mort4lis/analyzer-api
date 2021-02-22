############### Образ для сборки виртуального окружения ################
# Основа — «тяжелый» (~1 ГБ, в сжатом виде ~500 ГБ) образ со всеми необходимыми
# библиотеками для сборки модулей
FROM snakepacker/python:all as builder

# Обновляем pip и создаем виртуальное окружение
RUN python3.8 -m pip install --upgrade pip \
    && python3.8 -m venv /usr/local/app/venv

# Создаем папку и делаем ее рабочей директорией
WORKDIR /usr/local/app/

# Копируем зависимости в рабочую директорую и устанавливаем (необходимо для кэширования).
# При следующей сборке Docker пропустит этот шаг если requirements.txt не изменялся
COPY requirements.txt .
RUN venv/bin/pip install -r requirements.txt

# Копируем собранный артефакт (source distribution) и устанавливаем его
COPY dist/ dist/
RUN venv/bin/pip install ./dist/*

########################### Финальный образ ############################
# За основу берем «легкий» (~100 МБ, в сжатом виде ~50 МБ) образ с Python
FROM snakepacker/python:3.8 as api

# Копируем в него готовое виртуальное окружение из builder
COPY --from=builder /usr/local/app/venv /usr/local/app/venv

RUN ln -s /usr/local/app/venv/bin/analyzer-* /usr/local/bin/

CMD ["analyzer-api"]