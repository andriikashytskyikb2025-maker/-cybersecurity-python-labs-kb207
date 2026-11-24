# Лабораторна робота №3 — Реєстр вразливостей вебзастосунку

REST API на базі FastAPI та SQLite для обліку знахідок перевірки вебзастосунку (одиниця вимірювання — `score` від 0 до 10).

## 1. Встановлення залежностей

```bash
pip install fastapi uvicorn pydantic

python -m labs.lab03.seed

uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000

curl -X GET "[http://127.0.0.1:8000/ping](http://127.0.0.1:8000/ping)"

curl -X GET "[http://127.0.0.1:8000/categories](http://127.0.0.1:8000/categories)"

curl -X GET "[http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0](http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0)"

curl -X POST "[http://127.0.0.1:8000/records](http://127.0.0.1:8000/records)" \
  -H "Content-Type: application/json" \
  -d '{"code": "V01-10", "title": "XSS у формі пошуку", "category_id": 1, "value": 7.5, "status": "new"}'