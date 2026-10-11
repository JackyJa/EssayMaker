from dotenv import load_dotenv
from Prompts.critic_prompt import CRITIC_SYSTEM_PROMPT
import aisuite as ai
import json
import re

load_dotenv()


class CriticAgent:
    """
    فقط یک وظیفه داره: گرفتن موضوع اصلی + research خام + draft مقاله،
    و برگردوندن یک feedback ساختاریافته (JSON). هیچ‌چیزی رو خودش بازنویسی نمی‌کنه.
    """

    def __init__(self, model: str):
        self.client = ai.Client()
        self.model = model

    def parse_json(self, text: str) -> dict:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\n", "", text)
        text = re.sub(r"\n```$", "", text)
        return json.loads(text.strip())

    def review(self, topic: str, research: str, draft: str) -> dict:
        user_content = (
            f"Original topic/question: {topic}\n\n"
            f"Research findings:\n{research}\n\n"
            f"Article draft:\n{draft}"
        )

        messages = [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1
        )

        raw_output = response.choices[0].message.content

        try:
            return self.parse_json(raw_output)
        
        except json.JSONDecodeError:
            return {
                "approved": False,
                "issues": [{
                    "type": "structure",
                    "location": "N/A",
                    "problem": "Critic model returned invalid JSON",
                    "suggested_fix": "Retry the review"
                }],
                "summary": "Review failed due to malformed model output.",
                "raw_output": raw_output 
            }


if __name__ == "__main__":

    from Agents.researcher_agent import ResearcherAgent
    from Agents.writer_agent import WriterAgent

    researcher = ResearcherAgent(model="openai:gpt-4o-mini")
    writer = WriterAgent(model="openai:gpt-4o-mini")
    critic = CriticAgent(model="openai:gpt-4o-mini")

    try:
        researcher.load_tools()
        topic = input("Subject: ")

        print("\n[Researching...]\n")
        research = researcher.research(topic)

        print("\n[Writing draft...]\n")
        draft = writer.write(topic, research)

        print("\n[Reviewing draft...]\n")
        review = critic.review(topic, research, draft)

        print("\n" + "=" * 50)
        print("Critic Review:")
        print("=" * 50)
        print(json.dumps(review, indent=2, ensure_ascii=False))

    finally:
        researcher.cleanup()