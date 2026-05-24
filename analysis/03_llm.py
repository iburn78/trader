#%% 
from ollama import chat

response = chat(
    model='gemma4',
    messages=[
        {
            'role': 'user',
            'content': 'Analyze this image',
            'images': ['c:/Users/andy/Downloads/img_test.jpg']
        }
    ]
)

print(response['message']['content'])

#%%

from openai import OpenAI
import base64


client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="gemma4",
    messages=[
        {"role": "user", "content": "hello"}
    ]
)

print(response.choices[0].message.content)
# %%
from openai import OpenAI
import base64

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy"
)

# encode image
with open('c:/Users/andy/Downloads/img_test.jpg', "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="gemma4",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this chart - with some plot twist"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}"
                    }
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
# %%
# 1) html search -> text should be extracted and provided
# 2) pdf -> pypdf etc exract text
# 3) image -> done as above image_url
