# src/dashboard_api.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from .web3_utils import web3_manager
from .sim_runner import SecureMILBASTER

app = FastAPI()
simulator = SecureMILBASTER()
simulator.initialize_network()

# Mount static files directory
dashboard_path = os.path.join(os.path.dirname(__file__), "..", "dashboard")
app.mount("/static", StaticFiles(directory=dashboard_path), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(dashboard_path, "dashboard.html"))

@app.get("/stats")
def stats():
    return simulator.get_comprehensive_stats()

@app.get("/blockchain_logs")
def blockchain_logs(from_block: int = 0, to_block: str = "latest"):
    """
    Returns blockchain logs, falling back to local simulator logs if chain unavailable.
    """
    logs = web3_manager.get_logs_from_chain(from_block=from_block, to_block=to_block)
    # Sort logs by block number or timestamp
    logs_sorted = sorted(logs, key=lambda x: x.get("blockNumber", 0))
    return JSONResponse(content=logs_sorted)

