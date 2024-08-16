from langchain_openai import ChatOpenAI


def _get_model():
    return ChatOpenAI(temperature=0, model_name="gpt-4o-2024-08-06")
