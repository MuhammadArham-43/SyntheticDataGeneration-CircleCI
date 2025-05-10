import re
import os
import json
from tqdm import tqdm
from together import Together

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
assert TOGETHER_API_KEY, "Together API key is requierd to generate data"
CLEINT = Together()

def build_prompt(title, context):
    return f"""You are an AI assistant that generates training data for large language models.

Title: {title}
Article:
{context}

Task:
Based on the article above, generate a list of question and answer pairs in the following JSON format:
```json
{{
  "question": "...",
  "answer": "..."
}}
```
Enclose JSON between ```json and ``` code blocks.
"""

def generate_qa(title, content, model="mistralai/Mixtral-8x7B-Instruct-v0.1"):
    prompt = build_prompt(title, content)
    
    response = CLEINT.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": "You are a helpful assistant to generate structured synthetic question answering dataset for an LLM."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=model,
    )

    return response.choices[0].message.content


def extract_json_from_markdown(text):
    # Match content between ```json and ```
    matches = re.findall(r"```json(.*?)```", text, re.DOTALL)
    json_objects = []

    for match in matches:
        try:
            obj = json.loads(match.strip())
            json_objects.append(obj)
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)

    return json_objects

def main():
    FILE_PATH = "data/scraped_articles.json"
    assert os.path.exists(FILE_PATH), "No scrpaed data file found."
    
    with open(FILE_PATH) as f:
        articles = json.load(f)
        articles = list(filter(lambda x: "text" in x, articles))
    
    qa_pairs = []
    for article in tqdm(articles, desc="Generating Q/A Pairs"):
        try:
            qa_json = generate_qa(article["title"], article["text"])
            qa_json = extract_json_from_markdown(qa_json)
            qa_pairs.append({
                "url": article["url"],
                "generated_questions": qa_json
            })
        except Exception as e:
            print(f"Error processing article: {article['url']}\n{e}")

    with open("data/qa_dataset.json", "w") as f:
        json.dump(qa_pairs, f, indent=2)

if __name__ == "__main__":
    main()

