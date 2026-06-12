# Testes da API de Tarefas

## Descrição

Este conjunto de testes cobre os casos solicitados na atividade: autenticação (login), criação, listagem, recuperação por ID e deleção de tarefas (CT-01 a CT-19). Os testes usam o `TestClient` do FastAPI e foram escritos para serem independentes entre si, utilizando uma nova instância do `TestClient` por teste para isolar o armazenamento em memória.

## Como executar

1. Crie um ambiente virtual (recomendado):

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate     # Windows (PowerShell)
```

2. Instale as dependências necessárias (exemplo mínimo):

```bash
pip install pytest fastapi[all]
```

Observação: o projeto principal deve estar disponível e importável como `src.tarefas.app` contendo a variável `app` do FastAPI.

3. Rode os testes a partir da raiz do projeto (`teste_api/`):

```bash
cd teste_api
pytest tests/
```

Alternativa: exporte o `PYTHONPATH` apontando para a raiz do projeto (útil quando você roda os testes de dentro de `tests/`). Exemplos:

Windows (PowerShell, sessão atual):

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest tests/
```

Windows (cmd.exe):

```cmd
set PYTHONPATH=%CD%
pytest tests/
```

Linux/macOS:

```bash
export PYTHONPATH=$(pwd)
pytest tests/
```

## Saída esperada

Quando todos os testes passam, você verá algo parecido com:

```txt
============================= test session starts ==============================
collected 19 items

tests/test_api.py ...................                                      [100%]

============================== 19 passed in 0.xx seconds =======================
```

## Dificuldades encontradas

Ao escrever os testes encontrei duas sutilezas:

- O armazenamento em memória da API faz com que o estado persista apenas enquanto a instância do aplicativo estiver viva. Para garantir independência entre testes, criei um `TestClient` novo por teste (fixture `client`).
- O endpoint de login espera dados via formulário; por isso os testes usam `data=` ao invés de `json=` para o `POST /auth/login`.

Se houver diferenças na estrutura do projeto (por exemplo o app exposto em outro caminho), ajuste o import em `tests/test_api.py` (`from src.tarefas.app import app`) para o local correto.
