from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header, status, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
import uuid


class TarefaIn(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    descricao: Optional[str] = None


class TarefaOut(BaseModel):
    id: int
    titulo: str
    descricao: Optional[str]
    status: str


app = FastAPI()


@app.on_event("startup")
def startup_event():
    app.state.tarefas = []  # type: ignore
    app.state.next_id = 1  # type: ignore
    app.state.tokens = set()  # type: ignore


from fastapi import Request, Form


@app.post("/auth/login", status_code=200)
async def auth_login(username: str = Form(...), password: str = Form(...)):
    if username != "aluno" or password != "senha123":
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = str(uuid.uuid4())
    app.state.tokens.add(token)  # type: ignore
    return {"access_token": token, "token_type": "bearer"}


def _get_tarefas_storage() -> List[dict]:
    return app.state.tarefas  # type: ignore


@app.get("/tarefas", response_model=List[TarefaOut])
def listar_tarefas():
    return _get_tarefas_storage()


@app.post("/tarefas", response_model=TarefaOut, status_code=status.HTTP_201_CREATED)
def criar_tarefa(t: TarefaIn):
    tarefa = {
        "id": app.state.next_id,  # type: ignore
        "titulo": t.titulo,
        "descricao": t.descricao,
        "status": "pendente",
    }
    app.state.next_id += 1  # type: ignore
    app.state.tarefas.append(tarefa)  # type: ignore
    return JSONResponse(status_code=201, content=tarefa)


@app.get("/tarefas/{tarefa_id}", response_model=TarefaOut)
def buscar_tarefa(tarefa_id: int):
    for t in _get_tarefas_storage():
        if t["id"] == tarefa_id:
            return t
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")


def _require_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="missing authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="invalid authorization header")
    token = parts[1]
    if token not in app.state.tokens:  # type: ignore
        raise HTTPException(status_code=401, detail="invalid token")
    return token


@app.delete("/tarefas/{tarefa_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tarefa(tarefa_id: int, token: str = Depends(_require_token)):
    tarefas = _get_tarefas_storage()
    for i, t in enumerate(tarefas):
        if t["id"] == tarefa_id:
            tarefas.pop(i)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")
