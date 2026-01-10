# Agent Architecture Documentation

## Overview

The Vanguard AI Agent System is a multi-agent architecture that autonomously responds to factory events by analyzing situations, checking inventory, and making decisions.

## Architecture
```
Factory Event (Kafka)
        ↓
   Supervisor Agent
   (Analyzes & Routes)
        ↓
   Inventory Agent
   (Checks Stock & Decides)
        ↓
   Actions & Decisions
```

## Agent Roles

### Supervisor Agent
**Responsibility:** Event analysis and workflow routing

**Logic:**
- Analyzes incoming factory events
- Determines event severity
- Routes to appropriate specialized agent
- Marks critical events for escalation

**Routing Rules:**
- `LOW_INVENTORY` → Inventory Agent
- `SENSOR_OVERHEAT` → Inventory Agent (check repair parts)
- `MACHINE_VIBRATION` → Inventory Agent (check repair parts)
- `MAINTENANCE_DUE` → Inventory Agent (verify maintenance parts)
- `PART_FAILED_QC` → Inventory Agent (check replacement parts)

**Escalation Criteria:**
- Severity = CRITICAL or HIGH
- Part availability issues
- Multiple simultaneous problems

---

### Inventory Agent
**Responsibility:** Stock verification and procurement recommendations

**Capabilities:**
1. **Check Part Availability**
   - Queries Inventory Service REST API
   - Verifies required parts are in stock
   - Reports quantity levels

2. **Low Stock Analysis**
   - Identifies parts below minimum quantity
   - Calculates reorder recommendations
   - Prioritizes critical parts

3. **Decision Making**
   - ✅ Approve if all parts available
   - ⚠️ Recommend reorder if low stock
   - ❌ Escalate if parts missing

**Tools Used:**
- `get_part_by_number()`: Get part details
- `check_availability()`: Verify stock level
- `get_low_stock_parts()`: Find reorder candidates
- `remove_stock()`: Reserve parts
- `add_stock()`: Record received shipments

---

## State Management

The agent system uses a shared state object that flows through the workflow:
```python
AgentState = {
    # Input
    "event_id": str,
    "event_type": EventType,
    "machine_id": str,
    "severity": Severity,

    # Workflow
    "next_agent": Optional[str],
    "should_escalate": bool,

    # Analysis
    "analysis": str,
    "recommended_actions": List[str],
    "required_parts": List[str],
    "parts_available": Dict[str, bool],

    # Results
    "actions_taken": List[Dict],
    "final_decision": str,
    "human_approval_needed": bool
}
```

---

## Decision Flows

### Flow 1: Low Inventory Event
```
1. Supervisor: Detect LOW_INVENTORY event
2. Supervisor: Route to Inventory Agent
3. Inventory Agent: Query low stock parts
4. Inventory Agent: Calculate reorder quantities
5. Inventory Agent: Generate recommendations
6. Output: Reorder suggestions for each part
```

### Flow 2: Machine Failure Event
```
1. Supervisor: Detect SENSOR_OVERHEAT on PRESS-001
2. Supervisor: Identify required parts (hydraulic pump, pressure sensor)
3. Supervisor: Mark as CRITICAL (escalate)
4. Inventory Agent: Check availability of each part
5. Inventory Agent:
   - All parts available → Approve repair
   - Some parts missing → Escalate + urgent reorder
6. Output: Go/no-go decision with justification
```

### Flow 3: Scheduled Maintenance
```
1. Supervisor: Detect MAINTENANCE_DUE
2. Supervisor: Identify maintenance parts needed
3. Inventory Agent: Verify all parts in stock
4. Inventory Agent: Check for low stock warnings
5. Output:
   - Maintenance approved
   - Parts to reorder (proactive)
```

---

## Integration Points

### Kafka Consumer
- **Topic:** `factory_events`
- **Group ID:** `ai-agent-group`
- **Processing:** Asynchronous event consumption

### REST API (Inventory Service)
- **Base URL:** `http://localhost:8082/api/inventory`
- **Endpoints Used:**
  - `GET /parts/{partNumber}`
  - `GET /parts/low-stock`
  - `GET /parts/{partNumber}/check-availability`
  - `POST /parts/{partNumber}/remove`

---

## Testing Strategy

### Unit Tests
- Supervisor routing logic
- Inventory agent decision rules
- State transformations

### Integration Tests
- End-to-end event processing
- REST API interactions
- Error handling

### Test Coverage
- ✅ Event routing
- ✅ Part availability checks
- ✅ Escalation logic
- ✅ Low stock detection
- ✅ Missing part handling

---

## Future Enhancements

1. **LLM-Based Supervisor**
   - Replace rule-based routing with LLM reasoning
   - Natural language explanations
   - Adaptive decision-making

2. **Learning & Optimization**
   - Learn part usage patterns
   - Predict maintenance needs
   - Optimize reorder quantities

3. **Human-in-the-Loop**
   - Approval workflows for critical decisions
   - Feedback mechanism for agent learning
   - Override capabilities

4. **Additional Agents**
   - Maintenance Scheduling Agent
   - Procurement Agent (auto-ordering)
   - Quality Control Agent

---

## Performance Metrics

Current system processes:
- **Event throughput:** 1 event every 10 seconds (simulator rate)
- **Processing time:** < 500ms per event
- **API calls:** 2-5 per event (depending on complexity)
- **Decision latency:** Real-time (< 1 second)

---

## Monitoring & Observability

**Logs:**
- Event reception
- Agent routing decisions
- Tool executions
- Final decisions

**Metrics to Add:**
- Events processed per minute
- Average decision time
- Escalation rate
- Part availability hit rate
