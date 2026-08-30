from dotenv import load_dotenv
from Agents.researcher_agent import ResearcherAgent
from Agents.writer_agent import WriterAgent
from Agents.critic_agent import CriticAgent
import json

load_dotenv()


def run_single_revision(topic: str, model: str = "openai:gpt-4o-mini"):

    researcher = ResearcherAgent(model=model)
    writer = WriterAgent(model=model)
    critic = CriticAgent(model=model)

    try:
        researcher.load_tools()

        print("\n[1/4] Researching...")
        research = researcher.research(topic)

        print("\n[2/4] Writing first draft...")
        first_draft = writer.write(topic, research)

        print("\n[3/4] Critic reviewing first draft...")
        review = critic.review(topic, research, first_draft)

        if review["approved"]:
            print("\n✅ First draft was approved. No revision needed.")
            return first_draft

        print("\n[4/4] Revising based on feedback...")
        feedback_text = review["summary"] + "\n\n" + json.dumps(
            review["issues"], indent=2, ensure_ascii=False
        )
        revised_draft = writer.write(topic, research, feedback=feedback_text)

        print("\n" + "=" * 50)
        print("Research:")
        print("=" * 50)
        print(research)

        print("\n" + "=" * 50)
        print("First Draft:")
        print("=" * 50)
        print(first_draft)

        print("\n" + "=" * 50)
        print("Review:")
        print("=" * 50)
        print(json.dumps(review, indent=2, ensure_ascii=False))

        print("\n" + "=" * 50)
        print("Revised Draft:")
        print("=" * 50)
        print(revised_draft)

        return revised_draft

    finally:
        researcher.cleanup()


if __name__ == "__main__":
    topic = input("Subject: ")
    run_single_revision(topic)