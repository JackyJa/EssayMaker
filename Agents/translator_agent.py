from dotenv import load_dotenv
from Prompts.translator_prompt import TRANSLATOR_SYSTEM_PROMPT
from Agents.rewrite_agent import run_single_revision
import aisuite as ai
import re

load_dotenv()

class TranslatorAgent:

    def __init__(self, model: str):

        self.client = ai.Client()
        self.model = model


    def clean_markdown(self, text: str) -> str:
        
        text = text.strip()
        text = re.sub(r"^```(?:markdown)?\n", "", text)
        text = re.sub(r"\n```$", "", text)
        return text.strip()

    def translate(self, essay: str, user_question: str) -> str:


        messages = [
            {"role": "system", "content": TRANSLATOR_SYSTEM_PROMPT},
            {"role": "user", "content": f"Essay : {essay}\nuser question : {user_question}"}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2
        )

        raw_output = response.choices[0].message.content
        return self.clean_markdown(raw_output)



if __name__ == "__main__":

    topic = input("Subject: ")
    essay = run_single_revision(topic=topic)

    translator_agent = TranslatorAgent(model="openai:gpt-4o-mini")
    translated_essay = translator_agent.translate(essay,topic)

    print("\n" + "=" * 50)
    print("Translated Essay:")
    print("=" * 50)
    print(translated_essay)