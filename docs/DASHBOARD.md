# Dashboard

Цель: показать команде сводную статистику по задачам выбранного раунда, сгруппированную по типам задач раунда (RoundTaskType).

Что отображает:
- для каждого типа задач: ac (решено), wa (неверно), pending (ожидает/на проверке), remaining (еще можно взять);

Основные сущности:
- Challenge
  - Team
  - Round
    - RoundTaskType
      - Task
        - Submission

Нужные поля и связи:
- из Submission — статус последнего сабмита (AC/WA) и task_id;
- по task_id получаем Task, из Task — round_task_type_id, round_id, team_id, challenge_id, текущий Task.status;
- по round_task_type_id известны ограничения (max_tasks_per_team), используемые для вычисления remaining.

Параметры:
- round_id (опционально) — если не передан, берется текущий активный раунд команды; если отсутствует — 400 Bad Request.

CLI:
- board dashboard [-r ROUND_ID]
  - пример: board dashboard -r 12

API:
- GET /dashboard?round_id={id?}

Правила агрегации:
1. Берем все задачи команды выбранного раунда и группируем по типам (RoundTaskType.type).
2. Статус задачи — по последнему сабмиту/текущему Task.status. Каждая задача учитывается ровно в одном счетчике: pending, ac или wa.
3. Для каждого типа считаем: total = ac + wa + pending; далее считаем remaining.
4. Формула remaining: remaining = max(0, max_tasks_per_team - total). Если max_tasks_per_team отсутствует — remaining считаем 0.
5. Порядок типов в ответе — по дате добавления типа (например, по возрастанию round_task_type_id).

Пример ответа:
```json
{
  "round_id": 12,
  "stats": {
    "sql": { "ac": 1, "wa": 3, "pending": 2, "remaining": 4 },
    "ml":  { "ac": 4, "wa": 1, "pending": 2, "remaining": 3 }
  }
}
```
Здесь ключи словаря stats — это значение RoundTaskType.type (например, "sql", "ml"). Агрегат по всем типам (total) в ответе не возвращается — он используется только внутренне для вычисления remaining.

Сценарий:
1. Пользователь вызывает CLI: board dashboard [-r ROUND_ID].
2. CLI отправляет GET /dashboard[?round_id=...] с авторизацией игрока.
3. Бэкенд агрегирует данные по правилам выше и возвращает JSON в указанном формате. Ошибки: 401 — нет/неверный API-ключ; 403 — нет доступа к команде/раунду; 400 — активный раунд не найден (если round_id не указан).
4. CLI форматирует ответ и выводит в терминал (или JSON при флаге --json).

Реализация (денормализация для производительности):
- Единая таблица board_rows (Board) — общая для Dashboard и Leaderboard
  - Поля общие: round_id, team_id, type (RoundTaskType.type)
  - Поля для дашборда: round_task_type_id, pending, ac, wa, remaining, updated_at.
  - Поля для лидерборда: name, score, last_score_at (для тай‑брейка).
  - Уникальный ключ: (round_id, team_id, round_task_type_id).
- Строка создаётся, когда команда берёт новую задачу данного типа в раунде.
- Обновления счетчиков не допускают отрицательных значений; если remaining = 0, задача не выдается.

Переходы состояний:
- Генерация задачи команде: remaining → pending (pending += 1; remaining = max(0, remaining - 1)).
- Сабмит решения:
  - pending → AC: pending -= 1; ac += 1
  - pending → WA: pending -= 1; wa += 1
  - WA → AC: wa -= 1; ac += 1
  - WA → WA: счетчики не меняются
  - AC -> AC:  переоценка допустима
