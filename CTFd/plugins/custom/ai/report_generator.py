from openai import OpenAI
from pprint import pprint

#client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    #api_key="My API Key",
#)
client = OpenAI()

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-3.5-turbo",
)

pprint("Testing...")