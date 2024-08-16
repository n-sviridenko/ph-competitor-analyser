from typing import Literal
from langgraph.graph import StateGraph, END
from ph_competitor_analyser.state import AgentState
from ph_competitor_analyser.gather_requirements import gather_requirements
from ph_competitor_analyser.find_and_analyze_launches import find_and_analyze_launches
from ph_competitor_analyser.save_relevant_launches import save_relevant_launches
from ph_competitor_analyser.reset_state import reset_state

# Create our graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("reset_state", reset_state)
workflow.add_node("gather_requirements", gather_requirements)
workflow.add_node("find_and_analyze_launches", find_and_analyze_launches)
workflow.add_node("save_relevant_launches", save_relevant_launches)

# Add edges
workflow.set_entry_point("reset_state")
workflow.add_edge("reset_state", "gather_requirements")

def route_gather(state: AgentState) -> Literal["find_and_analyze_launches", END]:
    if state.get('search_args'):
        return "find_and_analyze_launches"
    else:
        return END
workflow.add_conditional_edges("gather_requirements", route_gather)

workflow.add_edge("find_and_analyze_launches", "save_relevant_launches")

def route_analyze(state: AgentState) -> Literal["find_and_analyze_launches", END]:
    # Check if we need to continue analyzing or if we're done
    if state.get("page_cursor"):
        return "find_and_analyze_launches"
    else:
        return END
workflow.add_conditional_edges("save_relevant_launches", route_analyze)

# Compile the graph
graph = workflow.compile()
