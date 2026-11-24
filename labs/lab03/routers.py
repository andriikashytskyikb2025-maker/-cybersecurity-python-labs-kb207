from typing import List, Optional, Literal
from fastapi import APIRouter, HTTPException, Query, Path, status
from shared.student import STUDENT_NAME, GROUP_NAME, VARIANT_NUMBER
from labs.lab03 import repository
from labs.lab03.schemas import (
    CategoryCreate, CategoryRead,
    RecordCreate, RecordReplace, RecordRead
)

router = APIRouter()

@router.get("/ping", summary="Перевірка доступності API")
def ping():
    return {"status": "ok"}

@router.get("/student", summary="Інформація про студента")
def get_student():
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER
    }

@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED,
             summary="Створити категорію")
def create_category(payload: CategoryCreate):
    result = repository.create_category(payload.name)
    if result is None:
        raise HTTPException(status_code=409, detail="Категорія з такою назвою вже існує")
    return result


@router.get("/categories", response_model=List[CategoryRead], summary="Список категорій")
def get_categories():
    return repository.get_categories()

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Видалити порожню категорію")
def delete_category(category_id: int = Path(..., gt=0)):
    res = repository.delete_category(category_id)
    if res == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    if res == "HAS_RECORDS":
        raise HTTPException(status_code=409, detail="Неможливо видалити категорію, що містить записи")
    return None


@router.get("/records", response_model=List[RecordRead], summary="Список записів із фільтрами")
def get_records(
        category_id: Optional[int] = Query(None, gt=0),
        status_param: Optional[Literal['new', 'in_progress', 'done']] = Query(None, alias="status"),
        min_value: Optional[float] = Query(None, ge=0.0, le=10.0),
        q: Optional[str] = Query(None, min_length=1, max_length=120),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0)
):
    return repository.get_records(
        category_id=category_id,
        status=status_param,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset
    )


@router.get("/records/{record_id}", response_model=RecordRead, summary="Один запис")
def get_record(record_id: int = Path(..., gt=0)):
    rec = repository.get_record_by_id(record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    return rec


@router.post("/records", response_model=RecordRead, status_code=status.HTTP_201_CREATED, summary="Створити запис")
def create_record(payload: RecordCreate):
    code_res, rec = repository.create_record(
        payload.code, payload.title, payload.category_id, payload.value, payload.status
    )
    if code_res == "CATEGORY_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Зазначену категорію не знайдено")
    if code_res == "DUPLICATE_CODE":
        raise HTTPException(status_code=409, detail="Запис із таким кодом вже існує")
    return rec


@router.put("/records/{record_id}", response_model=RecordRead, summary="Повна заміна запису")
def update_record(payload: RecordReplace, record_id: int = Path(..., gt=0)):
    code_res, rec = repository.update_record(
        record_id, payload.code, payload.title, payload.category_id, payload.value, payload.status
    )
    if code_res == "RECORD_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    if code_res == "CATEGORY_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Зазначену категорію не знайдено")
    if code_res == "DUPLICATE_CODE":
        raise HTTPException(status_code=409, detail="Запис із таким кодом вже існує")
    return rec


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Видалити запис")
def delete_record(record_id: int = Path(..., gt=0)):
    if not repository.delete_record(record_id):
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    return None


@router.post("/records/bulk", response_model=List[RecordRead], status_code=status.HTTP_201_CREATED,
             summary="Пакетне створення записів")
def create_records_bulk(payload: List[RecordCreate]):
    if not payload or len(payload) > 100:
        raise HTTPException(status_code=422, detail="Пакет повинен містити від 1 до 100 елементів")

    data_list = [item.model_dump() for item in payload]
    code_res, results = repository.create_records_batch(data_list)

    if code_res == "CATEGORY_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Категорію з пакета не знайдено в базі")
    if code_res in ("DUPLICATE_CODE_IN_BATCH", "DUPLICATE_CODE_DB"):
        raise HTTPException(status_code=409, detail="Знайдено дублікат коду")
    if code_res == "TRANSACTION_ERROR":
        raise HTTPException(status_code=422, detail="Помилка збереження пакета")

    return results