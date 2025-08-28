# Leaderboard

Цель: показать рейтинг команд в выбранном раунде (или текущем активном), с суммарными очками и разбивкой по типам задач.

Что отображает:
- для каждой команды: rank, name , total_score, scores (словарь очков по типам задач: ключ — RoundTaskType.type, значение — сумма очков этого типа).

Параметры:
- round_id (опционально). Если не передан — используется текущий активный раунд команды; если активный раунд не найден — 400 Bad Request.

CLI:
- board leaderboard [-r ROUND_ID]
  - пример: board leaderboard -r 12

API:
- GET /leaderboard?round_id={id?}

Правила подсчёта и сортировки:
1. Берём все задачи выбранного раунда по всем командам челленджа.
2. Очки считаются только за сабмиты со статусом AC; PENDING/WA очков не дают.
3. Разбивка по типам: агрегируем очки AC по типу RoundTaskType.type в словарь scores.
4. total_score = сумма значений в scores.
5. Сортировка:
   - по убыванию total_score;
   - тай-брейк (разрешение ничей): выше команда, достигшая данного total_score раньше (по времени последнего изменения total_score).
6. Включаются только команды, участвующие в челлендже выбранного раунда.

Ошибки:
- 400 — активный раунд не найден (если round_id не указан)
- 401 — нет/неверный API-ключ
- 403 — нет доступа к раунду/челленджу

Пример ответа:
```json
{
  "round_id": 12,
  "teams": [
    {"rank": 1, "name": "Alpha", "total_score": 540, "scores": {"sql": 200, "ml": 240, "misc": 100}},
    {"rank": 2, "name": "Beta",  "total_score": 430, "scores": {"sql": 200, "ml": 130, "misc": 100}}
  ]
}
```
Поле teams — упорядоченный список TeamScore c rank, name, total_score и scores. Поле rank монотонно увеличивается, начиная с 1, без пропусков.

Сценарий:
1. Пользователь вызывает CLI: board leaderboard [-r ROUND_ID].
2. CLI отправляет GET /leaderboard[?round_id=...] с авторизацией игрока.
3. Бэкенд агрегирует данные по правилам выше и возвращает JSON в указанном формате. Ошибки: 401 — нет/неверный API-ключ; 403 — нет доступа к раунду/челленджу; 400 — активный раунд не найден (если round_id не указан).
4. CLI форматирует ответ и выводит в терминал (или JSON при флаге --json).

Реализация (денормализация для производительности):
- Единая таблица board_rows (Board) — общая для Dashboard и Leaderboard
  - Поля общие: round_id, team_id, type (RoundTaskType.type)
  - Поля для дашборда: round_task_type_id, pending, ac, wa, remaining, updated_at.
  - Поля для лидерборда: name, score, last_score_at (для тай‑брейка).
  - Уникальный ключ: (round_id, team_id, round_task_type_id).
- Правила сортировки (описанные выше)

Переходы состояний (влияние на рейтинг):
- Сабмит решения:
  - PENDING → AC: total_score += score; scores_json[type] += score; ac_count += 1; last_score_at = now()
  - PENDING → WA: рейтинг не меняется
  - WA → AC: total_score += score; scores_json[type] += score; ac_count += 1; last_score_at = now()
  - WA → WA: рейтинг не меняется
  - AC → AC: переоценка допустима
