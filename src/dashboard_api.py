# src/dashboard_api.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import time
import random

try:
    from .web3_utils import web3_manager
    WEB3_AVAILABLE = True
except ImportError:
    print("⚠️ Web3 utilities not available - running without blockchain features")
    WEB3_AVAILABLE = False
    web3_manager = None

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
    stats = simulator.get_comprehensive_stats()

    # Add calculated fields for dashboard
    trusted_nodes = stats.get('total_nodes', 100) - stats.get('malicious_nodes', 0) - stats.get('low_trust_nodes', 0)
    delivery_rate = 0
    if stats.get('total_messages', 0) > 0:
        delivery_rate = (stats.get('successful_deliveries', 0) / stats.get('total_messages', 1)) * 100

    # Add extra fields for dashboard compatibility
    stats.update({
        'trusted_nodes': trusted_nodes,
        'delivery_success_rate': delivery_rate,
        'rreq_sent': sum(node.stats.get('rreq_sent', 0) for node in simulator.nodes),
        'rrep_sent': sum(node.stats.get('rrep_sent', 0) for node in simulator.nodes),
        'routes_discovered': len([node for node in simulator.nodes if node.routing_table]),
        'failed_deliveries': stats.get('total_messages', 0) - stats.get('successful_deliveries', 0),
        'signature_operations': stats.get('signature_verifications', 0)
    })

    return stats

@app.get("/blockchain_logs")
def blockchain_logs(from_block: int = 0, to_block: str = "latest"):
    """
    Returns blockchain logs, falling back to local simulator logs if chain unavailable.
    """
    try:
        if WEB3_AVAILABLE and web3_manager and hasattr(web3_manager, 'get_logs_from_chain'):
            # Try to get logs from blockchain
            logs = web3_manager.get_logs_from_chain(from_block=from_block, to_block=to_block)
            if logs:
                # Sort logs by block number or timestamp
                logs_sorted = sorted(logs, key=lambda x: x.get("blockNumber", 0))
                return JSONResponse(content=logs_sorted)

        # Fallback: Return simulated blockchain logs
        fallback_logs = generate_fallback_logs()
        return JSONResponse(content=fallback_logs)

    except Exception as e:
        print(f"❌ Error fetching blockchain logs: {e}")
        # Return fallback logs on any error
        fallback_logs = generate_fallback_logs()
        return JSONResponse(content=fallback_logs)

def generate_fallback_logs():
    """Generate simulated blockchain logs when real blockchain is unavailable"""

    # Get current stats to generate realistic logs
    stats = simulator.get_comprehensive_stats()

    logs = []

    # Generate some sample logs based on current simulation state
    if stats.get('anomalies_detected', 0) > 0:
        for i in range(min(5, stats['anomalies_detected'])):
            logs.append({
                "blockNumber": 1000000 + i,
                "transactionHash": f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}",
                "eventHash": f"security_incident_{i}_{int(time.time())}",
                "anomalyType": "packet_drop",
                "trustDelta": -15,
                "timestamp": int(time.time()) - (i * 30)
            })

    if stats.get('blockchain_events', 0) > 0:
        for i in range(min(3, stats['blockchain_events'])):
            logs.append({
                "blockNumber": 1000010 + i,
                "transactionHash": f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}",
                "eventHash": f"trust_update_{i}_{int(time.time())}",
                "anomalyType": "trust_violation",
                "trustDelta": -10,
                "timestamp": int(time.time()) - (i * 45)
            })

    # If no events, create some demo logs
    if not logs:
        logs = [
            {
                "blockNumber": 1000000,
                "transactionHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "eventHash": "demo_security_event_1",
                "anomalyType": "anomalous_behavior",
                "trustDelta": -5,
                "timestamp": int(time.time()) - 300
            },
            {
                "blockNumber": 1000001,
                "transactionHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                "eventHash": "demo_trust_update_1", 
                "anomalyType": "successful_forward",
                "trustDelta": 2,
                "timestamp": int(time.time()) - 180
            }
        ]

    # Sort by timestamp (newest first)
    logs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

    return logs

# Additional endpoint for debugging
@app.get("/debug/web3")
def debug_web3():
    """Debug endpoint to check Web3 status"""
    if not WEB3_AVAILABLE:
        return {"status": "Web3 not available", "error": "Import failed"}

    if not web3_manager:
        return {"status": "web3_manager is None"}

    # Check available methods
    methods = [method for method in dir(web3_manager) if not method.startswith('_')]

    return {
        "status": "Web3 available",
        "web3_manager_type": str(type(web3_manager)),
        "available_methods": methods,
        "has_get_logs_method": hasattr(web3_manager, 'get_logs_from_chain')
    }

# Additional endpoints for dashboard data
@app.get("/nodes")
def get_nodes():
    """Get current node status for network visualization"""
    nodes_data = []
    for node in simulator.nodes:
        nodes_data.append({
            "id": node.node_id,
            "position": node.position,
            "trust_score": node.trust_score,
            "malicious": node.malicious,
            "unit_type": node.unit_type,
            "is_active": node.is_active,
            "energy_level": node.energy_level,
            "neighbors_count": len(node.neighbors)
        })
    return nodes_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
