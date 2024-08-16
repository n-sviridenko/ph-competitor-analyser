import os
from ph_competitor_analyser.state import AgentState
from langchain_core.messages import AIMessage
from typing import List
from pyairtable import Table
from urllib.parse import urlparse

def store_in_airtable(relevant_launches: List[dict], airtable_base_url: str) -> None:
    api_key = os.environ.get('AIRTABLE_API_KEY')
    if not api_key:
        raise ValueError("AIRTABLE_API_KEY environment variable is not set")

    parsed_url = urlparse(airtable_base_url)
    path_parts = parsed_url.path.split('/')
    base_id = path_parts[1]
    table_id = path_parts[2]

    table = Table(api_key, base_id, table_id)

    for launch in relevant_launches:
        record = {
            'Link': launch['url'],
            'Name': launch['name'],
            'Description': launch['description'],
            'Classification': launch['classification'],
            'Argumentation': launch['argumentation']
        }
        table.create(record)  # Removed the 'view' parameter

def save_relevant_launches(state: AgentState) -> AgentState:
    relevant_launches = state["relevant_launches"]
    airtable_base_url = state["search_args"].get("airtable_base_url")
    
    if not airtable_base_url:
        raise ValueError("airtable_base_url is not provided in search_args")

    store_in_airtable(relevant_launches, airtable_base_url)
    
    message = AIMessage(content=f"Stored {len(relevant_launches)} competitors in Airtable")
    
    return {"relevant_launches": [], "messages": [message]}  # Clear relevant_launches after processing
