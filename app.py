import json
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage, HumanMessage
from duckduckgo_search import DDGS
from typing import List


def run_web_search(query: str, search_url_count: int) -> List[dict]:
    search_results = []
    with DDGS() as ddgs:
        results = ddgs.text(
            keywords=query,
            safesearch='moderate',
        )
    if results:
        search_results = [
            {
                "title": res["title"],
                "body": res["body"],
                "url": res["href"],
            }
            for res in results[:search_url_count]
        ]
    return search_results

def prompt_template(query):
    prompt = """To appropriately answer the user's question, it would be helpful to search for the latest web information.
User's Question: {query}
Please use the search results as a reference to provide a comprehensive answer to the question."""
    return prompt.format(query=query)

base_model="llama3"
model = OllamaFunctions(model=base_model, format="json")
model = model.bind_tools(
    tools=[
        {
            "name": "get_web_search",
            "description": "Get the top k search results (title, body, url) from website for a given query. 'title' refers to the title of the webpage or the name of the website. 'body' refers to the document body or content of the webpage. 'url' refers to the uniform resource locator, which is the address of the webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "search_url_count": {
                        "type": "integer",
                        "description": "The number of searching URL to use",
                    },
                },
                "required": ["query"],
            },
        }
    ]
)

functions = {
    "get_web_search": run_web_search,
}

def invoke_and_run(model, query: str):
    try:
        prompt = prompt_template(query)
        first_response = model.invoke(prompt)
        first_response_message = first_response.content  
        messages = [HumanMessage(prompt), AIMessage(first_response_message)]  

        if first_response and first_response.tool_calls:
            for tool_call in first_response.tool_calls:
                if tool_call['name'] == 'get_web_search':
                    arguments = tool_call['args']
                    search_query = arguments['query']
                    search_url_count = arguments.get('search_url_count', 3)
                    function_response = run_web_search(search_query, search_url_count)

                    tool_message_content = f"Search results: {json.dumps(function_response)}"
                    tool_message = AIMessage(content=tool_message_content)
                    messages.append(tool_message)

                    second_response = model.invoke(messages)
                    second_response_message = second_response.content

            search_result_info = []
            for res in function_response:
                body = res['body'][:200] + '...' if len(res['body']) > 200 else res['body']
                search_result_info.append(f"Title: {res['title']}\nURL: {res['url']}\nBody: {body}")

            search_result_info = "\n\n".join(search_result_info)
            final_response_message = f"{second_response_message}\n\n### Search results:\n{search_result_info}"
        else:
            final_response_message = first_response_message
        print(f"### Answer: {final_response_message}")

    except Exception as e:  
        print(f"An error occurred: {e}")  

def main():
    query = input("Query: ") 
    invoke_and_run(model, query)

if __name__ == "__main__":
    main()
