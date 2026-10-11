from Agents import critic_agent , researcher_agent , writer_agent , translator_agent
import json
import os
import markdown
from datetime import datetime
import re



def is_english(text: str) -> bool:
   
    letters = re.findall(r'[^\s\d\W]', text, re.UNICODE)

    if not letters:
        return True  

    non_ascii_letters = [c for c in letters if ord(c) > 127]
  
    ratio_non_ascii = len(non_ascii_letters) / len(letters)

    return ratio_non_ascii < 0.1 


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
output_dir = f"Output/{timestamp}"
os.makedirs(output_dir, exist_ok=True)

filepath_md = f"{output_dir}/Essay.md"
filepath_html = f"{output_dir}/Essay.html"

with open(filepath_md, "w", encoding="utf-8") as f:
    f.write(FinalEssay)
print(f"✅ File {filepath_md} created.\n")

html_content = markdown.markdown(FinalEssay, extensions=['fenced_code', 'tables'])
with open(filepath_html, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"✅ File {filepath_html} created.\n")

if not is_english(question):
    try:
        translator = translator_agent.TranslatorAgent("openai:gpt-4o-mini")
        translated_essay = translator.translate(FinalEssay, question)

        filepath_md_tr = f"{output_dir}/Essay_Translated.md"
        filepath_html_tr = f"{output_dir}/Essay_Translated.html"

        with open(filepath_md_tr, "w", encoding="utf-8") as f:
            f.write(translated_essay)
        print(f"✅ File {filepath_md_tr} created.\n")

        html_translated = markdown.markdown(translated_essay, extensions=['fenced_code', 'tables'])
        with open(filepath_html_tr, 'w', encoding='utf-8') as f:
            f.write(html_translated)
        print(f"✅ File {filepath_html_tr} created.\n")

    except Exception as e:
        print(f"❌ Translation error: {e}")