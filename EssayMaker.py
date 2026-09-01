from Agents import critic_agent , researcher_agent , writer_agent
import json
import os
import markdown
from datetime import datetime

class EssayMaker:

    def __init__(self , question : str , model_research : str = "openai:gpt-4o-mini", model_writer : str = "openai:gpt-4o-mini" , model_critic : str = "openai:gpt-4o-mini"):

        self.question = question
        self.model_research = model_research
        self.model_writer = model_writer
        self.model_critic = model_critic
        self.researcher = None

    def build_agents(self):

        self.researcher = researcher_agent.ResearcherAgent(self.model_research)
        self.writer = writer_agent.WriterAgent(self.model_writer)
        self.critic = critic_agent.CriticAgent(self.model_critic)

    def run_pipeline(self, MAX_REVISION: int = 5):

        try:
            self.build_agents()
            self.researcher.load_tools()

            print("\nResearching....\n")
            research = self.researcher.research(self.question)

            print("Writing first draft....\n")
            essay = self.writer.write(self.question, research)

            for i in range(MAX_REVISION + 1): 
                print(f"Reviewing (attempt {i+1}/{MAX_REVISION+1})....\n")
                feedback = self.critic.review(self.question, research, essay)

                if feedback["approved"]:
                    print("✅ Approved.")
                    return essay

                if i == MAX_REVISION:
                    print("⚠️ Max revisions reached. Returning last (unapproved) draft.\n")
                    return essay

                print("Revising based on feedback...\n")
                feedback_text = feedback["summary"] + "\n\n" + json.dumps(feedback["issues"], indent=2, ensure_ascii=False)
                essay = self.writer.write(self.question, research, feedback_text)

        except Exception as e:
            print(f"Error: {e}")
            return None
        
        finally:
            if self.researcher is not None:
                self.researcher.cleanup()
            


question = input("Subject: ")

EssayAgent = EssayMaker(question)

try:
    max_revision = int(input("How many times do you want revision to take place: "))
except ValueError:
    print("Invalid number, defaulting to 3.\n")
    max_revision = 3

FinalEssay = EssayAgent.run_pipeline(int(max_revision))

if FinalEssay is None:
    print("Pipeline failed, nothing to save.\n")
    exit()

now = datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
filepath_md = f"Output{timestamp}/Essay.md"
filepath_html = f"Output{timestamp}/Essay.html"

os.makedirs(os.path.dirname(filepath_md), exist_ok=True)
with open(filepath_md, "w", encoding="utf-8") as f:
    f.write(FinalEssay)
    print(f"✅ File {filepath_md} Was Created successfully.\n")

try:
    with open(filepath_md, 'r', encoding='utf-8') as md_file:
        md_content = md_file.read()

    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])

    with open(filepath_html, 'w', encoding='utf-8') as html_file:
        html_file.write(html_content)

    print(f"✅ Converted '{filepath_md}' → '{filepath_html}' successfully.")

except Exception as e:
    print(f"❌ Error: {e}")