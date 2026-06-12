import pytest

from fastapi.testclient import TestClient

from src.tarefas.app import app


@pytest.fixture()
def client():
    """Cria uma instância nova do TestClient para isolar o estado entre testes."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_token(client):
    """Realiza login com credenciais válidas e retorna o access token."""
    resp = client.post("/auth/login", data={"username": "aluno", "password": "senha123"})
    assert resp.status_code == 200
    body = resp.json()
    return body["access_token"]


def test_ct01_login_valido(client):
    """CT-01: Login com credenciais válidas deve retornar access_token e token_type 'bearer'."""
    resp = client.post("/auth/login", data={"username": "aluno", "password": "senha123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and isinstance(body["access_token"], str) and body["access_token"].strip() != ""
    assert body.get("token_type") == "bearer"


def test_ct02_login_sem_username(client):
    """CT-02: POST /auth/login sem 'username' deve retornar 422."""
    resp = client.post("/auth/login", data={"password": "senha123"})
    assert resp.status_code == 422


def test_ct03_login_sem_password(client):
    """CT-03: POST /auth/login sem 'password' deve retornar 422."""
    resp = client.post("/auth/login", data={"username": "aluno"})
    assert resp.status_code == 422


def test_ct04_criar_tarefa_com_descricao(client):
    """CT-04: Criar tarefa com titulo e descricao válidos retorna 201 e campos corretos."""
    payload = {"titulo": "Estudar pytest", "descricao": "Ler a documentação"}
    resp = client.post("/tarefas", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body.get("id"), int)
    assert body.get("titulo") == payload["titulo"]
    assert body.get("descricao") == payload["descricao"]
    assert body.get("status") == "pendente"


def test_ct05_criar_tarefa_sem_descricao(client):
    """CT-05: Criar tarefa sem 'descricao' é aceito; resposta tem descricao=null."""
    payload = {"titulo": "Tarefa sem descricao"}
    resp = client.post("/tarefas", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body.get("titulo") == payload["titulo"]
    assert body.get("descricao") is None


def test_ct06_criar_tarefa_titulo_vazio(client):
    """CT-06: Criar tarefa com titulo vazio deve retornar 422."""
    resp = client.post("/tarefas", json={"titulo": ""})
    assert resp.status_code == 422


def test_ct07_criar_tarefa_sem_titulo(client):
    """CT-07: Criar tarefa sem o campo 'titulo' deve retornar 422."""
    resp = client.post("/tarefas", json={"descricao": "sem titulo"})
    assert resp.status_code == 422


def test_ct08_criar_tarefa_titulo_acima_limite(client):
    """CT-08: Criar tarefa com titulo de 201 caracteres deve retornar 422."""
    long_title = "A" * 201
    resp = client.post("/tarefas", json={"titulo": long_title})
    assert resp.status_code == 422


def test_ct09_status_inicial_pendente(client):
    """CT-09: O status inicial da tarefa criada deve ser sempre 'pendente'."""
    payload = {"titulo": "Qualquer", "status": "concluida"}
    resp = client.post("/tarefas", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body.get("status") == "pendente"


def test_ct10_listar_tarefas_vazio(client):
    """CT-10: GET /tarefas em repositório vazio retorna lista vazia."""
    resp = client.get("/tarefas")
    assert resp.status_code == 200
    assert resp.json() == []


def test_ct11_listar_apos_criar(client):
    """CT-11: Após criar uma tarefa, GET /tarefas deve retornar lista contendo a tarefa."""
    create = client.post("/tarefas", json={"titulo": "Lista Teste"})
    assert create.status_code == 201
    created = create.json()
    resp = client.get("/tarefas")
    assert resp.status_code == 200
    items = resp.json()
    assert any(item.get("id") == created.get("id") for item in items)


def test_ct12_buscar_tarefa_existente(client):
    """CT-12: Buscar por ID de tarefa existente retorna 200 e dados corretos."""
    create = client.post("/tarefas", json={"titulo": "Buscar Teste", "descricao": "detalhe"})
    assert create.status_code == 201
    created = create.json()
    resp = client.get(f"/tarefas/{created.get('id')}")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("id") == created.get("id")
    assert body.get("titulo") == created.get("titulo")


def test_ct13_buscar_tarefa_id_inexistente(client):
    """CT-13: Buscar ID inexistente retorna 404."""
    resp = client.get("/tarefas/99999")
    assert resp.status_code == 404


def test_ct14_buscar_tarefa_id_nao_numerico(client):
    """CT-14: Buscar com ID não numérico retorna 422."""
    resp = client.get("/tarefas/abc")
    assert resp.status_code == 422


def test_ct15_deletar_sem_token(client):
    """CT-15: DELETE sem Authorization header retorna 401."""
    resp = client.delete("/tarefas/1")
    assert resp.status_code == 401


def test_ct16_deletar_com_token_invalido(client):
    """CT-16: DELETE com token inválido retorna 401."""
    headers = {"Authorization": "Bearer token-invalido"}
    resp = client.delete("/tarefas/1", headers=headers)
    assert resp.status_code == 401


def test_ct17_deletar_existente_com_token_valido(client, auth_token):
    """CT-17: Autenticar, criar tarefa e deletar deve retornar 204 e remover o recurso."""
    create = client.post("/tarefas", json={"titulo": "Deletar Teste"})
    assert create.status_code == 201
    tid = create.json().get("id")
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.delete(f"/tarefas/{tid}", headers=headers)
    assert resp.status_code == 204
    assert resp.content == b""


def test_ct18_deletar_inexistente_com_token_valido(client, auth_token):
    """CT-18: Deletar recurso inexistente com token válido retorna 404."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.delete("/tarefas/99999", headers=headers)
    assert resp.status_code == 404


def test_ct19_tarefa_deletada_nao_encontrada(client, auth_token):
    """CT-19: Depois de deletada, a tarefa não deve ser encontrada (GET -> 404)."""
    create = client.post("/tarefas", json={"titulo": "Deletar e Verificar"})
    assert create.status_code == 201
    tid = create.json().get("id")
    headers = {"Authorization": f"Bearer {auth_token}"}
    del_resp = client.delete(f"/tarefas/{tid}", headers=headers)
    assert del_resp.status_code == 204
    get_resp = client.get(f"/tarefas/{tid}")
    assert get_resp.status_code == 404
