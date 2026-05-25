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
# run in terminal
# Only:
# run_sync()
# vs
# await run()

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from openai import AsyncOpenAI


# connect to local Ollama server
client = AsyncOpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',  # required but can be anything
)

# define model
model = OpenAIChatModel(
    model_name='gemma4:latest',
    provider=OpenAIProvider(openai_client=client),
)

# create agent
agent = Agent(model)

# run
result = agent.run_sync('Explain recursion in one sentence.')

print(result.output)

#%% 
# run in vscode (jupyter)
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from openai import AsyncOpenAI

print('async')
client = AsyncOpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

model = OpenAIChatModel(
    model_name='gemma4:latest',
    provider=OpenAIProvider(openai_client=client),
)

agent = Agent(model)

# await 
result = await agent.run(
    'Explain recursion in one sentence.'
)

print(result.output)

#%%
from pydantic import BaseModel
from pydantic_ai import Agent

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from openai import AsyncOpenAI


# structured output schema
class StockAnalysis(BaseModel):
    ticker: str
    sentiment: str
    confidence: float


# connect to local Ollama
client = AsyncOpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

# model
model = OpenAIChatModel(
    model_name='gemma4:latest',
    provider=OpenAIProvider(openai_client=client),
)

# agent with enforced output type
agent = Agent(
    model=model,
    output_type=StockAnalysis,
)

# run
result = await agent.run(
    'Analyze NVDA stock sentiment.'
)

# typed result
print(result.output)

# normal python object access
print(result.output.ticker)
print(result.output.sentiment)
print(result.output.confidence)

# even stronger type forcing
# from typing import Literal

# class StockAnalysis(BaseModel):
#     ticker: str
#     sentiment: Literal['bullish', 'bearish', 'neutral']
#     confidence: float

#%%
from typing import Annotated
from pydantic import BaseModel, StringConstraints


# uppercase only
# letters only
# 1 to 5 chars
# exactly one token

TickerStr = Annotated[
    str,
    StringConstraints(
        pattern=r'^[A-Z]{1,5}$'
    )
]


class StockAnalysis(BaseModel):
    ticker: TickerStr
    sentiment: str
    confidence: float


# If you want dots/dashes too: 
pattern=r'^[A-Z.\-]{1,10}$'
# include / too
pattern=r'^[A-Z0-9.\-\/]{1,15}$'



#%% 
# internet search version
from pydantic_ai import Agent, RunContext

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from openai import AsyncOpenAI


client = AsyncOpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

model = OpenAIChatModel(
    model_name='gemma4:latest',
    provider=OpenAIProvider(openai_client=client),
)

agent = Agent(model)


@agent.tool
def web_search(ctx: RunContext, query: str) -> str:
    return f"Fake web results for: {query}"


result = await agent.run(
    "Search web for NVIDIA news"
)

print(result.output)
# may need to use duckduckgo
#%%
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("NVIDIA news", max_results=5))

print(results)
# It simply asks DuckDuckGo for search results and returns:

# titles
# snippets
# URLs

#################################
# study Crawl4AI 