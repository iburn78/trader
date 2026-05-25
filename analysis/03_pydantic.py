#%%
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    active: bool = True

u = User(name="Andy", age="35")

print(u)
print(type(u.age))
print(u.model_dump())
print(u.model_dump_json())


#%% 

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

provider = OpenAIProvider(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

model = OpenAIModel(
    model_name='gemma4:latest',
    provider=provider
)

agent = Agent(model)

result = await agent.run(
    "What is the capital of Korea?"
)

print(result.output)


lets retry later