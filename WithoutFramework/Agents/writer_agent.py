from dotenv import load_dotenv
from Prompts.writer_prompt import WRITER_SYSTEM_PROMPT
import aisuite as ai
import re

load_dotenv()


class WriterAgent:
    """
    فقط یک وظیفه داره: گرفتن یک موضوع + نتایج تحقیق (خروجی Researcher Agent)
    و نوشتن یک مقاله‌ی کامل و حرفه‌ای بر اساس اون، به فرمت Markdown خالص.
    """

    def __init__(self, model: str):
        self.client = ai.Client()
        self.model = model

    def clean_markdown(self, text: str) -> str:
        
        text = text.strip()
        text = re.sub(r"^```(?:markdown)?\n", "", text)
        text = re.sub(r"\n```$", "", text)
        return text.strip()

    def write(self, topic: str, research: str, feedback: str = None) -> str:
        user_content = f"Topic: {topic}\n\nResearch findings:\n{research}"

        if feedback:
            user_content += f"\n\nEditor feedback from previous draft (revise accordingly):\n{feedback}"

        messages = [
            {"role": "system", "content": WRITER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.6
        )

        raw_output = response.choices[0].message.content
        return self.clean_markdown(raw_output)

    def save_to_file(self, markdown_text: str, filepath: str = "output/article.md"):
        
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        print(f"[Writer] Saved article to {filepath}")


if __name__ == "__main__":

    from Agents.researcher_agent import ResearcherAgent

    researcher = ResearcherAgent(model="openai:gpt-4o-mini")
    writer = WriterAgent(model="openai:gpt-4o-mini")

    try:
        researcher.load_tools()
        topic = input("Subject: ")

        print("\n[Researching...]\n")
        research = researcher.research(topic)

        print("\n[Writing article...]\n")
        article = writer.write(topic, research)

        writer.save_to_file(article)

        print("\n" + "=" * 50)
        print("Article (Markdown):")
        print("=" * 50)
        print(article)
    finally:
        researcher.cleanup()