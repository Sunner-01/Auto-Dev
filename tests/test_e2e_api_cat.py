from fastapi.testclient import TestClient
from app.main import app
from app import crud
import time
import json
import pytest

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(crud, "DB_FILE", str(tmp_path / "db.json"))


def test_e2e_full_category_lifecycle():
    """
    Simula un flujo completo del usuario (End-to-End):
    1. Revisa si existe.
    2. Crea el recurso.
    3. Revisa la lista para confirmar la creación.
    """
    cat_name = f"E2E Cat {int(time.time())}" # Nombre único
    # 1. Paso de usuario: Intenta obtener todas las categorías
    response_get_initial = client.get("/categorias")
    initial_list = response_get_initial.json()
    initial_count = len(initial_list)
    print("\n--- E2E: LISTA INICIAL DE CATEGORÍAS (Antes de crear) ---")
    print(json.dumps(initial_list, indent=4))
    print(f"Número inicial de categorías: {initial_count}")
    print("----------------------------------------------------------")
    # 2. Paso de usuario: Crea una nueva categoría
    response_post = client.post("/categorias", params={"nombre": cat_name})
    assert response_post.status_code == 200
    categoria_creada = response_post.json()
    print(f"\n--- E2E: CATEGORÍA CREADA ---")
    print(json.dumps(categoria_creada, indent=4))
    print("------------------------------")
    # 3. Paso de usuario: Verifica la lista final
    response_get_final = client.get("/categorias")
    final_list = response_get_final.json()
    print("\n--- E2E: LISTA FINAL DE CATEGORÍAS (Tras crear) ---")
    print(json.dumps(final_list, indent=4))
    print("--------------------------------------------------")
    # E2E Assertions:
    assert len(final_list) == initial_count + 1
    assert any(c['nombre'] == cat_name for c in final_list)


def test_e2e_create_category_then_product():
    categoria = client.post("/categorias", params={"nombre": "Oficina"})
    assert categoria.status_code == 200

    producto = client.post("/productos", params={
        "nombre": "Cuaderno", "categoria_id": categoria.json()["id"]
    })
    assert producto.status_code == 200
    assert producto.json()["nombre"] == "Cuaderno"
    assert producto.json()["categoria_id"] == categoria.json()["id"]
    assert categoria.json() in client.get("/categorias").json()


def test_e2e_recover_from_invalid_product_category():
    rejected = client.post("/productos", params={"nombre": "Lápiz", "categoria_id": 999})
    assert rejected.status_code == 404

    categoria = client.post("/categorias", params={"nombre": "Papelería"})
    assert categoria.status_code == 200
    accepted = client.post("/productos", params={
        "nombre": "Lápiz", "categoria_id": categoria.json()["id"]
    })

    assert accepted.status_code == 200
    assert accepted.json()["categoria_id"] == categoria.json()["id"]
    assert len(client.get("/categorias").json()) == 1
