
import os

from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY=os.getenv('OPENROUTER_API_KEY')
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')


class DeepSeekV3:
    def __init__(self):
        from openai import OpenAI

        # LLM Setup
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

        # self.model="deepseek/deepseek-r1-distill-llama-70b:free"
        self.model="deepseek/deepseek-chat:free"

    def call(self, prompt):
        messages=[
            {
            "role": "user",
            "content": prompt
            }
        ]

        completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
        # print(completion)
        return completion.choices[0].message.content

class Llama3:
    def __init__(self):
        from openai import OpenAI

        self.model="meta-llama/llama-3.3-70b-instruct:free"
        # LLM Setup
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

    def call(self, prompt):
        messages=[
            {
            "role": "user",
            "content": prompt
            }
        ]

        completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
        # print(completion)
        return completion.choices[0].message.content

class GeminiFlash:
    def __init__(self):
        """ Gemini 2.0 Flash delivers next-gen features and improved capabilities, including superior speed, native tool use, multimodal generation, and a 1M token context window. """
        from google import genai
        self.model = "gemini-2.0-flash"
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        pass

    def call(self, prompt):
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return response.text
