# Подключение к PostgreSQL

import psycopg2

from config import load_db_config

# Подгрузка значений для выпадающих меню
def load_lookup_values():
    queries = {
        "fam_id": "SELECT f_id, fam FROM public.fams ORDER BY fam, f_id",
        "nam_id": "SELECT n_id, nam FROM public.names ORDER BY nam, n_id",
        "otc_id": "SELECT o_id, otch FROM public.otches ORDER BY otch, o_id",
        "strt_id": "SELECT s_id, street FROM public.streets ORDER BY street, s_id",
    }

    connection = psycopg2.connect(**load_db_config(), connect_timeout=5)
    try:
        with connection.cursor() as cursor:
            values = {}
            for key, query in queries.items():
                cursor.execute(query)
                values[key] = cursor.fetchall()
        return values # Возвращаем словарь, содержащий значения для каждой таблицы 
    finally:
        connection.close()

# Запрос для вывода всех строк при инициализации программы
MAIN_SELECT = """
    SELECT
        m.uid,
        f.fam,
        n.nam,
        o.otch,
        s.street,
        m.bldn,
        m.bldn_k,
        m.apprt,
        m.phone
    FROM public.main AS m
    LEFT JOIN public.fams AS f ON m.fam_id = f.f_id
    LEFT JOIN public.names AS n ON m.nam_id = n.n_id
    LEFT JOIN public.otches AS o ON m.otc_id = o.o_id
    LEFT JOIN public.streets AS s ON m.strt_id = s.s_id
"""

# Перевод для обращения к столбцам ГЛАВНОЙ ТАБЛИЦЫ
FILTER_COLUMNS = {
    "fam_id": "m.fam_id",
    "nam_id": "m.nam_id",
    "otc_id": "m.otc_id",
    "strt_id": "m.strt_id",
    "bldn": "m.bldn",
    "bldn_k": "m.bldn_k",
    "apprt": "m.apprt",
    "phone": "m.phone",
}

# Составление условия WHERE
def build_filter_where(filters):
    conditions = []
    parameters = []
    for key, column in FILTER_COLUMNS.items():
        value = filters.get(key) # Используем get, чтобы не выбрасывать ошибку если Null
        if value is not None and value != "":
            conditions.append(f"{column} = %s")
            parameters.append(value)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, tuple(parameters)

# ---

# Составление SELECT запроса
def build_main_search_query(filters):
    where_clause, parameters = build_filter_where(filters)
    return MAIN_SELECT + where_clause + " ORDER BY m.uid", parameters

# Выполняем запрос поиска, устанавливая параметры в плейсхолдеры
def search_main_rows(filters):
    query, parameters = build_main_search_query(filters)
    connection = psycopg2.connect(**load_db_config(), connect_timeout=5)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            rows = cursor.fetchall()
            executed_query = cursor.query.decode(connection.encoding)
            return rows, executed_query # Возвращаем полученные строки и выполненный запрос
    finally:
        connection.close()

# ---

# Вставить новую строку
def insert_main_row(values):
    if all(value is None for value in values.values()):
        raise ValueError("Нельзя добавить полностью пустую запись")
    columns = tuple(FILTER_COLUMNS)
    parameters = tuple(values[column] for column in columns)
    query = """
        INSERT INTO public.main (
            fam_id, nam_id, otc_id, strt_id, bldn, bldn_k, apprt, phone
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING uid
    """

    connection = psycopg2.connect(**load_db_config(), connect_timeout=5)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            executed_query = cursor.query.decode(connection.encoding)
            uid = cursor.fetchone()[0]
            cursor.execute(MAIN_SELECT + " WHERE m.uid = %s", (uid,))
            added_row = cursor.fetchone()
        connection.commit()
        return added_row, executed_query
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

# ---

# Удалить подтверждённые строки только из main
def delete_main_rows(filters):
    where_clause, parameters = build_filter_where(filters)
    query = "DELETE FROM public.main AS m" + where_clause
    connection = psycopg2.connect(**load_db_config(), connect_timeout=5)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            executed_query = cursor.query.decode(connection.encoding)

        connection.commit()
        return executed_query
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

# ---

# Составление UPDATE запроса
def build_main_update_query(filters, changes):
    assignments = []
    set_parameters = []
    for key in FILTER_COLUMNS:
        value = changes.get(key)
        if value is not None and value != "":
            assignments.append(f"{key} = %s")
            set_parameters.append(value)

    where_clause, where_parameters = build_filter_where(filters)
    query = "UPDATE public.main AS m SET " + ", ".join(assignments) + where_clause + " RETURNING m.uid"
    return query, tuple(set_parameters) + where_parameters

# Прочитать изменённые строки по uid
def fetch_main_rows_by_uids(cursor, uids):
    cursor.execute(MAIN_SELECT + " WHERE m.uid = ANY(%s) ORDER BY m.uid", (uids,))
    return cursor.fetchall()

# Обновить подтверждённые строки
def update_main_rows(filters, changes):
    query, parameters = build_main_update_query(filters, changes)
    connection = psycopg2.connect(**load_db_config(), connect_timeout=5)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            executed_query = cursor.query.decode(connection.encoding)
            updated_uids = [row[0] for row in cursor.fetchall()]
            updated_rows = fetch_main_rows_by_uids(cursor, updated_uids)

        connection.commit()
        return updated_rows, executed_query
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

# ---

# Проверяем значения выбранных параметров на None
def filters_are_empty(filters):
    where_clause, _ = build_filter_where(filters)
    return not where_clause
