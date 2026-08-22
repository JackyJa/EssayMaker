from dotenv import load_dotenv
from Prompts.researcher_prompt import RESEARCHER_SYSTEM_PROMPT
import aisuite as ai
from aisuite.mcp import MCPClient
import json
import os

load_dotenv()


class ResearcherAgent:
    """
    فقط یک وظیفه داره: گرفتن یک موضوع/سؤال از کاربر و جمع‌آوری منابع مرتبط
    (وب + مقالات علمی). هیچ مقاله‌ای نمی‌نویسه، فقط تحقیق می‌کنه.
    """

    def __init__(self, model : str ,config_path="tools/server_config.json"):
        self.client = ai.Client()
        self.mcp_clients = []
        self.tools = []
        self.config_path = config_path
        self.model = model

    def load_tools(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        servers = data.get("mcpServers", {})

        for server_name, server_config in servers.items():
         
            env_vars = {}
            if "env" in server_config:
                for key in server_config["env"]:
                    env_vars[key] = os.getenv(key)  

            mcp = MCPClient(
                command=server_config["command"],
                args=server_config.get("args", []),
                env=env_vars if env_vars else None
            )
            self.mcp_clients.append(mcp)

            server_tools = mcp.get_callable_tools()
            self.tools.extend(server_tools)

            print(f"[Researcher] Connected to '{server_name}' "
                  f"({len(server_tools)} tools)")

        print(f"[Researcher] Total tools loaded: {len(self.tools)}")

    def research(self, topic: str) -> str:
        """
        موضوع رو می‌گیره، با tools سرچ می‌کنه، و فقط منابع جمع‌آوری‌شده
        رو به‌شکل خلاصه برمی‌گردونه. هیچ مقاله‌ای نمی‌نویسه.
        """
        messages = [
        {"role": "system", "content": RESEARCHER_SYSTEM_PROMPT},
        {"role": "user", "content": topic}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            max_turns=7,
            temperature=0.1
        )

        return response.choices[0].message.content

    def cleanup(self):
        for mcp in self.mcp_clients:
            mcp.close()


if __name__ == "__main__":
    agent = ResearcherAgent(model="openai:gpt-4o-mini")
    try:
        agent.load_tools()
        topic = input("Subject: ")
        result = agent.research(topic)
        print("\n" + "=" * 50)
        print("Result:")
        print("=" * 50)
        print(result)
    finally:
        agent.cleanup()