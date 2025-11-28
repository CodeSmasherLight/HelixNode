from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pydantic import BaseModel, Field
import asyncpg
import os

# i am forcing the connection via unix socket because it is 10x more stable 
# on android/termux than using localhost TCP ports
DB_USER = "root" 
DB_NAME = "telemetry_db"
SOCKET_DIR = "/data/data/com.termux/files/usr/tmp"
DATABASE_URL = f"postgresql://{DB_USER}@/{DB_NAME}?host={SOCKET_DIR}"

app = FastAPI(title="HelixNode LIMS")

# allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# global db pool
class GlobalState:
    pool = None

state = GlobalState()

# schema for incoming DNA sample
class DNASample(BaseModel):
    sequence: str = Field(..., description="Raw DNA Sequence")

# logic
def calculate_gc_content(sequence: str) -> float:
    seq_upper = sequence.upper().strip()
    if not seq_upper:
        return 0.0
        
    g_count = seq_upper.count('G')
    c_count = seq_upper.count('C')
    return ((g_count + c_count) / len(seq_upper)) * 100

# frontend serving
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')


# lifecycle events
@app.on_event("startup")
async def startup():
    print(f"Connecting to database via socket: {SOCKET_DIR}")
    try:
        state.pool = await asyncpg.create_pool(DATABASE_URL)
        
        async with state.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS samples (
                    id SERIAL PRIMARY KEY,
                    sequence TEXT,
                    gc_content FLOAT,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );
            ''')
        print("HelixNode Online: database connected & table ready")
    except Exception as e:
        print(f"DATABASE ERROR: {e}")

@app.on_event("shutdown")
async def shutdown():
    if state.pool:
        await state.pool.close()
    print("database connection closed")


# endpoints
@app.post("/analyze")
async def analyze_sequence(data: DNASample):
    # 1. edge processing (cpu work)
    clean_seq = data.sequence.strip().upper()
    gc_val = calculate_gc_content(clean_seq)
    
    # 2. store in db and get autogen id
    async with state.pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO samples (sequence, gc_content) VALUES ($1, $2) RETURNING id",
            clean_seq, gc_val
        )
        new_id = row['id']
        
    return {
        "status": "success",
        "formatted_id": f"SEQ-{new_id}", # eg. SEQ-5
        "gc_content": round(gc_val, 2),
        "node": "Realme 2 Pro (ARM64)"
    }

@app.get("/stats")
async def get_stats():
    async with state.pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM samples")

        rows = await conn.fetch("SELECT id, gc_content FROM samples ORDER BY id DESC")
        return {
            "total_samples": count, 
            "recent_logs": [
                {"id": f"SEQ-{r['id']}", "gc": r['gc_content']} 
                for r in rows
            ]
        }
