import os
import aiohttp
# https://docs.python.org/3/library/asyncio-task.html
import asyncio
from dotenv import load_dotenv

# Add Azure OpenAI package
# from openai import AzureOpenAI
from openai import AsyncAzureOpenAI

LLM_GUARD_API_KEY = os.environ.get("LLM_GUARD_API_KEY")
LLM_GUARD_BASE_URL = os.environ.get("LLM_GUARD_URL")

class LLMGuardMaliciousPromptException(Exception):
    scores = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.scores = kwargs.get("scores", {})

    def __str__(self):
        scanners = [scanner for scanner, score in self.scores.items() if score > 0]

        return f"LLM Guard detected a malicious prompt. Scanners triggered: {', '.join(scanners)}; scores: {self.scores}"

class LLMGuardRequestException(Exception):
    pass

async def request_llm_guard_prompt(prompt: str):
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                url=f"{LLM_GUARD_BASE_URL}/analyze/prompt",
                json={"prompt": prompt},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LLM_GUARD_API_KEY}",
                },
                ssl=False,
                raise_for_status=True,
            )

            response_json = await response.json()
        except Exception as e:
            raise LLMGuardRequestException(e)

        if not response_json["is_valid"]:
            print(f'Response from LLM Guard:\n{LLMGuardMaliciousPromptException(scores=response_json["scanners"])}\n')
            raise LLMGuardMaliciousPromptException(scores=response_json["scanners"])

async def request_azure_openai(prompt: str) -> str:
    try:    
        # Get configuration settings 
        load_dotenv()
        azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
        azure_oai_key = os.getenv("AZURE_OAI_KEY")
        azure_oai_deployment = os.getenv("AZURE_OAI_DEPLOYMENT")

        print("\nSending prompt to Azure OpenAI endpoint...\n\n")
        
        # Add code to build request...
        # Initialize the Azure OpenAI client
        client = AsyncAzureOpenAI(
                 azure_endpoint = azure_oai_endpoint, 
                 api_key=azure_oai_key,  
                 api_version="2023-05-15"
                 )

        # Send request/prompt to Azure OpenAI model
        response = await client.chat.completions.create(
            model=azure_oai_deployment,
            temperature=0.7,
            max_tokens=120,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{prompt}"}
            ]
         )
        print("Response from Azure OpenAI:\n" + response.choices[0].message.content + "\n")
        
        return response.choices[0].message.content
    except Exception as ex:
        print(ex)

async def generate_completion(prompt: str) -> str:
    try:
        # https://superfastpython.com/asyncio-gather/    
        result = await asyncio.gather(
            request_llm_guard_prompt(prompt),
            request_azure_openai(prompt),
        )
        return result[1]
    except LLMGuardMaliciousPromptException:
        SystemExit('LLM Guard terminated application!')
    
def main(): 
    # prompt = "Write a Python function to calculate the factorial of a number."
    prompt = "My credit card number is 5555555555554444. What is the provider?"
    message = asyncio.run(
        generate_completion(prompt)
    )
    print(f"Response from Azure OpenAI After Treated by LLM Guard:\n{message}")
if __name__ == '__main__': 
    main()