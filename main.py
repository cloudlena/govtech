import os
import requests
from dotenv import load_dotenv
import chainlit as cl
from openai import OpenAI

load_dotenv()


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@cl.on_message
async def main(message: cl.Message):
    tags = extract_tokens(message.content)
    csv_url = run_search(tags)

    await cl.Message(content=f"Shizzle can be downloaded from {csv_url}").send()


@cl.step
def extract_tokens(message: str) -> list[str]:
    alternatives_completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": f"Extract the most relevant words from the following string: {message}. Output only the words, one per line as raw strings.",
            }
        ],
    )
    alternatives = alternatives_completion.choices[0].message.content.splitlines()

    return alternatives


@cl.step
def run_search(tags: str) -> list[str]:
    tags += ["csv"]

    resp = requests.get(
        f"https://ckan.opendata.swiss/api/3/action/package_search?q={'+'.join(tags)}"
    )
    resp_json = resp.json()
    result = resp_json["result"]

    if result["count"] == 0:
        raise f"No results found for searching with {' '.join(tags)}"

    best_match = resp_json["result"]["results"][0]

    for r in best_match["resources"]:
        if r["format"] == "CSV":
            return r["url"]

    raise "No CSV results found"
