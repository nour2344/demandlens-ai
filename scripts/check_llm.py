
from src.llm import get_llm


llm = get_llm()

response = llm.invoke(
    "Explain censored demand in retail in three sentences."
)

print("\n===== LLM RESPONSE =====")
print(response.content)

print("\n===== TOKEN USAGE =====")
print(response.usage_metadata)
