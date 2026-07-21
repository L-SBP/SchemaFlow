from langgraph.constants import START, END
from langgraph.graph import StateGraph

from graphs.nodes.ddl_node import generate_ddl_node
from graphs.nodes.er_node import generate_er_node
from graphs.state import ProjectState


def route_after_ddl(state: ProjectState) -> str:
    """DDL 生成后的条件路由"""
    if state.get("error_message"):
        return "failed"
    if state.get("regenerate_er") and state.get("schema_text"):
        return "regenerate_er"
    return "done"


def route_after_er(state: ProjectState) -> str:
    """ER 生成后直接结束（非关键路径）"""
    return "done"

builder = StateGraph(ProjectState)

builder.add_node("generate_ddl", generate_ddl_node)
builder.add_node("regenerate_er", generate_er_node)

builder.add_edge(START, "generate_ddl")

builder.add_conditional_edges(
    "generate_ddl",
    route_after_ddl,
    {
        "done": END,
        "failed": END,
        "regenerate_er": "regenerate_er",
    }
)

builder.add_conditional_edges(
    "regenerate_er",
    route_after_er,
    {"done": END}
)

ddl_er_graph = builder.compile()