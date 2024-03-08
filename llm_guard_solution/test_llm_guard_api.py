import os
import requests

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

def request_llm_guard_prompt(prompt: str):
    try:
        response = requests.post(
            url=f"{LLM_GUARD_BASE_URL}/analyze/prompt",
            json={"prompt": prompt},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LLM_GUARD_API_KEY}",
            },
        )

        response_json = response.json()
    except requests.RequestException as err:
        raise LLMGuardRequestException(err)

    if not response_json["is_valid"]:
        raise LLMGuardMaliciousPromptException(scores=response_json["scanners"])

    return response_json["sanitized_prompt"]

def main():
    try: 
        # prompt = "Write a Python function to calculate the factorial of a number."
        prompt = "My credit card number is 5555555555554444. What is the provider?"
        sanitized_prompt = request_llm_guard_prompt(prompt)
        print(sanitized_prompt)
    except LLMGuardMaliciousPromptException:
        print('Malicious prompt detected!')
    
if __name__ == '__main__': 
    main()
    