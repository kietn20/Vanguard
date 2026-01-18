# FastAPI Gateway Examples

## REST API Examples

### 1. Trigger a Workflow (cURL)
```bash
curl -X POST http://localhost:8000/workflows/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "SENSOR_OVERHEAT",
    "machine_id": "PRESS-001",
    "severity": "CRITICAL",
    "description": "Temperature sensor reading 120°C exceeds threshold",
    "metadata": {
      "temperature_celsius": 120,
      "threshold_celsius": 80,
      "sensor_id": "TEMP-05"
    }
  }'
```

Response:
```json
{
  "job_id": "job-abc123def456",
  "status": "pending",
  "event_id": "evt-1234567890",
  "created_at": "2026-01-17T10:00:00Z",
  "message": "Workflow queued for execution"
}
```

### 2. Check Workflow Status
```bash
curl http://localhost:8000/workflows/job-abc123def456
```

Response:
```json
{
  "job_id": "job-abc123def456",
  "status": "completed",
  "event_id": "evt-1234567890",
  "event_type": "SENSOR_OVERHEAT",
  "machine_id": "PRESS-001",
  "severity": "CRITICAL",
  "analysis": "Critical overheat detected...",
  "final_decision": "All required parts are in stock...",
  "recommended_actions": ["Reorder HYDRAULIC_PUMP_001"],
  "actions_taken": [...],
  "should_escalate": true,
  "human_approval_needed": false,
  "created_at": "2026-01-17T10:00:00Z",
  "completed_at": "2026-01-17T10:00:15Z",
  "duration_seconds": 15.3
}
```

### 3. List Recent Workflows
```bash
curl http://localhost:8000/workflows?limit=10
```

### 4. Get System Stats
```bash
curl http://localhost:8000/stats
```

---

## Python Client Example
```python
import requests
import time

API_BASE = "http://localhost:8000"

# 1. Trigger workflow
response = requests.post(f"{API_BASE}/workflows/trigger", json={
    "event_type": "LOW_INVENTORY",
    "machine_id": "INVENTORY-SYSTEM",
    "severity": "MEDIUM",
    "description": "Low stock detected for BEARING_6205",
    "metadata": {
        "part_name": "BEARING_6205",
        "current_stock": 5,
        "minimum_stock": 10
    }
})

job_id = response.json()["job_id"]
print(f"Job created: {job_id}")

# 2. Poll for completion
while True:
    status_response = requests.get(f"{API_BASE}/workflows/{job_id}")
    data = status_response.json()

    print(f"Status: {data['status']}")

    if data["status"] in ["completed", "failed"]:
        print(f"Final decision: {data.get('final_decision')}")
        break

    time.sleep(2)
```

---

## WebSocket Example (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/workflows/stream');

ws.onopen = () => {
    console.log('Connected to workflow stream');

    // Send event data
    ws.send(JSON.stringify({
        event_type: "MACHINE_VIBRATION",
        machine_id: "CNC-M10",
        severity: "HIGH",
        description: "Abnormal vibration detected",
        metadata: {
            vibration_mm_per_sec: 12.5,
            normal_threshold: 3.0
        }
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case 'started':
            console.log(`Workflow started: ${data.job_id}`);
            break;
        case 'update':
            console.log(`Node completed: ${data.data.node_name}`);
            console.log('State updates:', data.data.state_updates);
            break;
        case 'completed':
            console.log('Workflow completed!');
            console.log('Result:', data.result);
            ws.close();
            break;
        case 'error':
            console.error('Error:', data.message);
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

---

## Python WebSocket Example
```python
import asyncio
import websockets
import json

async def stream_workflow():
    uri = "ws://localhost:8000/ws/workflows/stream"

    async with websockets.connect(uri) as websocket:
        # Send event
        event = {
            "event_type": "MAINTENANCE_DUE",
            "machine_id": "PRESS-002",
            "severity": "MEDIUM",
            "description": "Scheduled maintenance approaching",
            "metadata": {
                "hours_until_due": 4,
                "maintenance_type": "PREVENTIVE"
            }
        }

        await websocket.send(json.dumps(event))
        print("Event sent, waiting for updates...")

        # Receive updates
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "started":
                print(f"Workflow started: {data['job_id']}")

            elif data["type"] == "update":
                node = data["data"]["node_name"]
                print(f"Node '{node}' completed")

            elif data["type"] == "completed":
                print("Workflow completed!")
                print(f"Decision: {data['result']['final_decision']}")
                break

            elif data["type"] == "error":
                print(f"Error: {data['message']}")
                break

asyncio.run(stream_workflow())
```
