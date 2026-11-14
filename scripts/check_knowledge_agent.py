
import json

from src.agents.knowledge_agent import run_knowledge_agent


result = run_knowledge_agent(
    question="How do stockouts affect retail demand forecasting?",
    top_k=3
)

print(json.dumps(result, indent=4))
