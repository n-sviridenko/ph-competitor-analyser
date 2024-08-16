from langgraph.graph import MessagesState
from typing import TypedDict, Literal, List

class SearchArgs(TypedDict):
    description: str
    competitor_types: List[Literal['direct_competitor', 'indirect_competitor']]
    period_from: str # ISO date string
    period_until: str # ISO date string
    airtable_base_url: str

class AgentState(MessagesState):
    relevant_launches: List[dict]
    page_cursor: str
    search_args: SearchArgs
