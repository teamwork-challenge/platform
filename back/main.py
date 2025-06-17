from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# создаём приложение FastAPI
app = FastAPI()

# демо мини база данных
challenges = [
    {
        "id": 1,
        "title": "Teamwork Programming Challenge 2025",
    }
]
tasks = [
    {"id": 1, "title": "First task", "status": "PENDING"},
    {"id": 2, "title": "Second task", "status": "ACCEPTED"},
]
# корневой эндпоинт (тестовый)
@app.get("/")
def root():
    return {"message": "Test(root)"}

# эндпоинт для получения всех челленджей
@app.get(
    "/challenges",
    tags=["Admin"]
)
def get_challenges():
    # возвращаем все челленджи
    return challenges

# эндпоинт для получения задачи по ID (например, /tasks/1)
@app.get(
    "/challenges/{challenge_id}",
    tags=["Admin"]
)
def get_challenge(challenge_id: int):
    for challenge in challenges:
        # ищем челлендж по айди
        if challenge["id"] == challenge_id:
            return challenge
    #если не нашли - возвращ ошибку 404
    raise HTTPException(status_code=404, detail="Challenge not found")

@app.get("/tasks/{task_id}", tags=["Player"])
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

# класс для описания, как должна выглядеть задача
# BaseModel делает автоматическую проверку данных (валидацию)
# и помогает преобразовать их в формат JSON (сериализация)
class Task(BaseModel):
    title: str
    status: str = "PENDING"

# эндпоинт для создания новой задачи (принимает данные от юзера)
@app.post("/tasks", tags=["Player"])
def create_task(new_task: Task):
    task_obj = {
        "id": len(tasks) + 1,
        "title": new_task.title,
        "status": new_task.status
    }
    tasks.append(task_obj)
    # возвращаем созданную задачу
    return task_obj
