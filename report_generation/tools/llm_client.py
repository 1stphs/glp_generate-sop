import os
import json
from openai import OpenAI
from sop_deeplang.utils.config import MODEL_CONFIG

def chat_json(messages, model=None, temperature=0.1, max_tokens=8000):
    """Simple adapter to make generate_report.py work with our config"""
    config = MODEL_CONFIG["writer"] # Re-use writer config
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    
    response = client.chat.completions.create(
        model=model or config["model"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
