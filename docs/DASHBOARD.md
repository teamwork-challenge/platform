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
- из Submission — статус (AC/WA/PENDING) и task_id;
- по task_id получаем Task, из Task — round_task_type_id, round_id, team_id, challenge_id;
- по round_task_type_id известны ограничения (max_tasks_per_team), используемые для вычисления remaining.

Параметры:
- round_id (опционально) — если не передан, берется текущий активный раунд команды.

CLI:
- dashboard [-r ROUND_ID] 
  - пример: dashboard -r 12


API:
- GET /dashboard?round_id={id?}

Алгоритм агрегации:
1. Для выбранного раунда отобрать все задачи команды и сгруппировать по типам (RoundTaskType.type).
2. Для каждой задачи определить текущий статус как статус последнего сабмита: взять Submission с максимальным submitted_at по task_id.
3. Подсчитать по типу: ac, wa, pending. total = ac + wa + pending.
4. remaining = max(0, max_tasks_per_team - total). Если max_tasks_per_team отсутствует, remaining определяется бизнес-правилом бэкенда (кол-во доступных для выдачи задач).
Примечание: для производительности допустимо поддерживать денормализованную таблицу «последний статус задачи», обновляемую при каждом сабмите.

Формат ответа (соответствует api_models.models.Dashboard и TypeStats):
```json
{
  "round_id": 12,
  "stats": {
    "type1": { "total": 6, "pending": 2, "ac": 1, "wa": 3, "remaining": 4 },
    "type2": { "total": 7, "pending": 2, "ac": 4, "wa": 1, "remaining": 3 },
    "total": { "total": 13, "pending": 4, "ac": 5, "wa": 4, "remaining": 7 }
  }
}
```

Сценарий:
1. Пользователь вызывает CLI: challenge board dashboard [-r ROUND_ID].
2. CLI отправляет GET /dashboard[?round_id=...] с авторизацией игрока.
3. Бэкенд агрегирует данные по алгоритму выше и возвращает JSON в указанном формате.
4. CLI форматирует ответ и выводит в терминал (или в JSON при флаге --json).