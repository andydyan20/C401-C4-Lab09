from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    history: list
    
def node1(state: State):
    state["history"].append("node1")
    return state

def node2(state: State):
    state["history"].append("node2")
    return {"history": state["history"]}

graph = StateGraph(State)
graph.add_node("node1", node1)
graph.add_node("node2", node2)
graph.set_entry_point("node1")
graph.add_edge("node1", "node2")
graph.add_edge("node2", END)

app = graph.compile()
print(app.invoke({"history": []}))
