# LangGraph Integration

## Overview

Vanguard now uses **LangGraph** for declarative, stateful multi-agent workflows.

### Before (Manual Routing)
```python
if state["next_agent"] == "inventory":
    state = inventory_agent.process(state)
```

### After (LangGraph)
```python
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("inventory", inventory_node)
graph.add_conditional_edges("supervisor", route_to_agent)
```

---

## Graph Structure
```
START
  ↓
Supervisor (analyzes event)
  ↓
[conditional routing]
  ↓
Inventory Agent (checks parts) → END
  ↓
[conditional routing]
  ↓
Escalation (human approval) → END
```

---

## Key Benefits

✅ **Declarative** - Graph structure is explicit, not hidden in if/else
✅ **Stateful** - State flows through nodes with automatic merging
✅ **Traceable** - See exactly which nodes executed
✅ **Streamable** - Watch workflow execute step-by-step
✅ **Checkpointable** - Pause and resume workflows
✅ **Testable** - Test nodes and routing independently

---

## Running Tests
```bash
cd brain
poetry run pytest tests/test_langgraph_workflow.py -v
```

---

## Visualizing the Graph
```bash
poetry run python scripts/visualize_graph.py
```

This generates a Mermaid diagram you can paste into https://mermaid.live

---

## Streaming Workflow Execution
```python
workflow = LangGraphWorkflow()

for node_name, state_update in workflow.stream_event(event):
    print(f"Node {node_name} completed")
    print(f"Updated: {state_update.keys()}")
```

---

## Switching Between Workflows
```bash
# Use LangGraph (default)
export USE_LANGGRAPH=true

# Use legacy manual routing
export USE_LANGGRAPH=false
```

---

## Adding New Nodes

1. Create node function in `graph_nodes.py`:
```python
def my_new_node(state: AgentState) -> Dict[str, Any]:
    # Process state
    return {"field": "updated_value"}
```

2. Add to graph in `workflow_langgraph.py`:
```python
graph.add_node("my_node", my_new_node)
graph.add_edge("supervisor", "my_node")
```

3. Test it:
```python
def test_my_new_node():
    result = my_new_node(test_state)
    assert result["field"] == "updated_value"
```
