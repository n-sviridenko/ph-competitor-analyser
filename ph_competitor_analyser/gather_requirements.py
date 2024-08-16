from ph_competitor_analyser.model import _get_model
from ph_competitor_analyser.state import AgentState, SearchArgs
from typing import TypedDict, Literal, List
import dateparser

class SearchArgsRaw(TypedDict):
    description: str
    competitor_types: List[Literal['direct_competitor', 'indirect_competitor']]
    period_from: str
    period_until: str
    airtable_base_url: str

gather_prompt = """
You are tasked with helping collecting information about a product to find its competitors.

You need to collect:
- Product description
- Should you check for direct competitors, indirect competitors, or both?
- How far back in time should you check the competitors? For example, '7 days ago,' '2 weeks ago,' or a specific date range (e.g., 'from August 1st to today').
- Airtable base URL to store the results

You are conversing with a user. Ask as many follow up questions as necessary - but only ask ONE question at a time.

Once all information is collected, call the `SearchArgsRaw` tool with a detailed description.

Do not ask unnecessary questions! Do not ask them to confirm your understanding!
"""


def gather_requirements(state: AgentState, config):
    messages = [
       {"role": "system", "content": gather_prompt}
   ] + state['messages']
    model = _get_model().bind_tools([SearchArgsRaw])
    response = model.invoke(messages)
    if len(response.tool_calls) == 0:
        return {"messages": [response]}
    else:
        search_args_raw = response.tool_calls[0]['args']
        search_args: SearchArgs = {
            'description': search_args_raw['description'],
            'competitor_types': search_args_raw['competitor_types'],
            'airtable_base_url': search_args_raw['airtable_base_url'],
            'period_from': dateparser.parse(search_args_raw['period_from']).isoformat(),
            'period_until': dateparser.parse(search_args_raw['period_until']).isoformat()
        }
        return {"search_args": search_args}
