from ph_competitor_analyser.state import AgentState


def reset_state(state: AgentState):
    return {"search_args": None, "relevant_launches": [], "page_cursor": None}
