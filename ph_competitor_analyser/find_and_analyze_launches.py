import os
import requests
from typing import TypedDict, Literal, List, Dict
from ph_competitor_analyser.state import AgentState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ph_competitor_analyser.model import _get_model
import concurrent.futures

class CompetitorAnalysis(TypedDict):
    name: str
    classification: Literal['direct_competitor', 'indirect_competitor', 'not_competitors']
    argumentation: str

def find_new_launches(state: AgentState) -> list:
    period_from = state["search_args"]["period_from"]
    period_until = state["search_args"]["period_until"]

    url = f"https://api.producthunt.com/v2/api/graphql"
    query = """
    {
      posts(order: NEWEST, first: 20, after: "%s", postedAfter: "%s", postedBefore: "%s") {
        edges {
          node {
            url
            name
            description
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
    """ % (state.get("page_cursor", ""), period_from, period_until)

    headers = {
        "Authorization": f"Bearer {os.getenv('PRODUCT_HUNT_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={"query": query}, headers=headers)
    data = response.json()
    
    new_launches = [{
        "name": edge["node"]["name"],
        "description": edge["node"]["description"],
        "url": edge["node"]["url"]
    } for edge in data["data"]["posts"]["edges"]]
    page_info = data["data"]["posts"]["pageInfo"]
    
    print(f"Found {len(new_launches)} launches")
    return new_launches, page_info["endCursor"] if page_info["hasNextPage"] else None

def analyze_launch_batch(launches: List[dict], state: AgentState) -> List[dict]:
    prompt_products = "\n\n".join([f"Name: {launch['name']}"+"\n"+f"Description: {launch['description']}" for launch in launches])
    prompt = f"""
Analyze the following product descriptions and determine if they are direct or indirect competitors to our product or not, and explain why for each.

Return solely a JSON object with the following structure, strictly following this format:
{{
  "analyses": [
    {{
      "name": "Product Name",
      "classification": "direct_competitor" | "indirect_competitor" | "not_competitors",
      "argumentation": "Explanation"
    }},
    ...
  ]
}}

Our Product Description:
'''
{state["search_args"]["description"]}
'''

Products to Analyze:
{prompt_products}

Result:
"""
    messages = [
        SystemMessage(content="You are a product analyst tasked with identifying competitors."),
        HumanMessage(content=prompt)
    ]
    analyses = _get_model().with_structured_output(Dict[str, List[CompetitorAnalysis]], method="json_mode").invoke(messages)
    
    results = []
    analysis_dict = {analysis["name"]: analysis for analysis in analyses["analyses"]}
    
    for launch in launches:
        analysis = analysis_dict.get(launch["name"])
        if analysis and analysis["classification"] in state["search_args"]["competitor_types"]:
            results.append({
                "url": launch["url"],
                "name": launch["name"],
                "description": launch["description"],
                "classification": analysis["classification"],
                "argumentation": analysis["argumentation"]
            })
    
    return results

def analyze_launches(launches: List[dict], state: AgentState) -> List[dict]:
    print(f"Analyzing {len(launches)} launches")
    batch_size = 5  # Analyze 5 products in each OpenAI request
    openai_batch_size = 4  # Batch 4 OpenAI requests at a time
    
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=openai_batch_size) as executor:
        for i in range(0, len(launches), batch_size * openai_batch_size):
            batch = launches[i:i + batch_size * openai_batch_size]
            futures = []
            for j in range(0, len(batch), batch_size):
                sub_batch = batch[j:j + batch_size]
                futures.append(executor.submit(analyze_launch_batch, sub_batch, state))
            
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
    
    return all_results

def find_and_analyze_launches(state: AgentState) -> AgentState:
    new_launches, page_cursor = find_new_launches(state)
    state["page_cursor"] = page_cursor
    
    relevant = state['relevant_launches'] + []
    
    results = analyze_launches(new_launches, state)
    relevant.extend(results)
    
    message = AIMessage(content=f"Found {len(relevant)} relevant from {len(new_launches)} launches")

    return {"relevant_launches": relevant, "page_cursor": state["page_cursor"], "messages": [message]}