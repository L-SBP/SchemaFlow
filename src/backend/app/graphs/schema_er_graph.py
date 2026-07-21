"""
Schema → ER 序列图。前端等两个都完成后停止轮询，展示 Schema + ER 图。
"""

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from graphs.nodes.er_node import generate_er_node
from graphs.nodes.schema_node import generate_schema_node
from graphs.state import ProjectState


def route_after_schema(state: ProjectState) -> str:
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