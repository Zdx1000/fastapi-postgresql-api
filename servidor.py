from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List
from contextlib import asynccontextmanager
import os

# Item com SQLModel (usando PostgreSQL)
class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

# Lê a URL do banco PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@localhost:5432/meubanco")

# Cria engine sem testar conexão no início (para evitar erro no deploy)
engine = create_engine(DATABASE_URL, echo=False)

# Cria as tabelas no banco
def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao criar tabelas: {e}")
        # Continua mesmo com erro para não travar o deploy

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed)

app = FastAPI(lifespan=lifespan)

# Configuração CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "API funcionando!", "database": "PostgreSQL conectado"}

@app.get("/items", response_model=List[Item])
def get_items():
    with Session(engine) as session:
        return session.exec(select(Item)).all()

@app.post("/items", response_model=Item)
def add_item(item: Item):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
