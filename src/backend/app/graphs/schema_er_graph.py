from langgraph.constants import START, END
from langgraph.graph import StateGraph

from graphs.nodes.er_node import generate_er_node
from graphs.nodes.schema_node import generate_schema_node
from graphs.state import ProjectState

def route_after_schema(state: ProjectState) -> str:
    """Schema 生成后的条件路由"""
    if state.get("error_message"):
        return "failed"
    return "success"

builder = StateGraph(ProjectState)

builder.add_node("generate_schema", generate_schema_node)
builder.add_node("generate_er", generate_er_node)

builder.add_edge(START, "generate_schema")

builder.add_conditional_edges(
    "generate_schema",
    route_after_schema,
    {
        "success": "generate_er",
        "failed": END,
    }
)

builder.add_edge("generate_er", END)

schema_er_graph = builder.compile()