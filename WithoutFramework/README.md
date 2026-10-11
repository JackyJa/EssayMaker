# EssayMaker

A multi-agent system that turns a single topic into a well-researched,
professional article — powered by [aisuite](https://github.com/andrewyng/aisuite)
and the Model Context Protocol (MCP).

Give it a topic (in any language), and three specialized agents collaborate
to research it, write it, and critique it — with a reflection loop that keeps
revising until the article is properly grounded in real sources.

```
"How has AI changed everyday life?"
                │
                ▼
        ┌───────────────┐
        │   Researcher  │  Searches the web (Tavily, DuckDuckGo) and
        │     Agent     │  academic papers (arXiv) via MCP tools,
        │               │  gathers and summarizes credible sources
        └───────┬───────┘
                │  research findings
                ▼
        ┌───────────────┐
        │     Writer    │  Writes a full article grounded strictly
        │     Agent     │  in the research — hook, structure, sources
        └───────┬───────┘
                │  draft
                ▼
        ┌───────────────┐
        │     Critic    │  Checks for unsupported claims, topic drift,
        │     Agent     │  overclaiming, and structural issues
        └───────┬───────┘
                │
          ┌─────┴─────┐
          │ approved? │
          └─────┬─────┘
        no │           │ yes
           ▼           ▼
     back to Writer   ┌──────────────┐
     with feedback    │  Translator  │  (only if the question wasn't
     (max N times)    │    Agent     │   in English) translates the
                      └──────┬───────┘   final article
                               ▼
                    Essay.md / Essay.html
              (+ Essay_Translated.md / .html)
```

## Why this project

Built to explore agentic AI patterns beyond simple tool-calling:
multi-agent orchestration, the reflection pattern, and connecting LLMs to
external tools through the standardized Model Context Protocol (MCP)
instead of hand-rolled API integrations.

It's deliberately built **without a high-level agent framework** (e.g.
CrewAI, LangGraph). The orchestration, tool-calling loop, and structured
feedback parsing are all implemented directly — to understand and
demonstrate what those frameworks abstract away, and to keep the pipeline
predictable and easy to debug for a task with well-defined, sequential
stages (research → write → review, not an open-ended multi-agent
negotiation).

## How it works

1. **Researcher Agent** connects to MCP servers (Tavily, DuckDuckGo, arXiv,
   and a page-fetch tool) and gathers sources on the given topic — web
   results and academic papers, verified for genuine relevance rather than
   superficial keyword matches. It only researches; it never writes.

2. **Writer Agent** drafts a complete Markdown article strictly grounded in
   the research — every claim must trace back to a source. It always
   writes in English, regardless of the input language, so quality stays
   consistent no matter what the user asks in.

3. **Critic Agent** reviews the draft against the original topic and the
   raw research, returning structured JSON: unsupported claims, topic
   drift, overclaiming, and structural issues, each with a suggested fix.

4. **Revision loop**: if the Critic doesn't approve, the *same* Writer
   Agent is called again with the Critic's feedback (there's no separate
   "rewriter" — the agent that wrote the piece is best positioned to revise
   it coherently as a whole). This repeats up to a configurable number of
   times.

5. **Translator Agent** (conditional): if the original question wasn't in
   English, the approved English article is translated into that language
   — Markdown formatting and source links/titles are preserved untouched.

6. The final article (and its translation, if any) is saved as both
   `.md` and `.html`.

## Tech stack

- **Python**, [aisuite](https://github.com/andrewyng/aisuite) — unified LLM
  client with automatic MCP tool-schema generation and tool-calling loop
  handling
- **MCP (Model Context Protocol)** — Tavily, DuckDuckGo, arXiv, and fetch
  servers for research tools
- **OpenAI** (`gpt-4o-mini` by default, configurable per agent)
- `markdown` — Markdown → HTML conversion for the final output

## Project structure

```
EssayMaker/
├── Agents/
│   ├── researcher_agent.py
│   ├── writer_agent.py
│   ├── critic_agent.py
│   └── translator_agent.py
├── Prompts/
│   ├── researcher_prompt.py
│   ├── writer_prompt.py
│   ├── critic_prompt.py
│   └── translator_prompt.py
├── tools/
│   └── server_config.json      # MCP server definitions
├── EssayMaker.py                # pipeline entry point
├── .env                         # API keys (not committed)
└── Output/
    └── <timestamp>/
        ├── Essay.md / Essay.html
        └── Essay_Translated.md / .html   (if applicable)
```

## Setup

**1. Install dependencies**
```bash
pip install aisuite python-dotenv mcp markdown
```

**2. Set up API keys**

Create a `.env` file in the project root:
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

**3. MCP tools**

The MCP servers used are defined in `tools/server_config.json`:

| Server | Purpose | Requires a key |
|---|---|---|
| Tavily | Web search | Yes |
| DuckDuckGo | Web search (free fallback) | No |
| fetch | Read full page content from a URL | No |
| arXiv | Academic paper search | No |

`Tavily` and `fetch`/`arXiv` run locally via `npx`/`uvx`, so `Node.js` and
`uv` need to be installed and available on your `PATH`.

## Usage

```bash
python EssayMaker.py
```

You'll be prompted for:
- **Subject** — the topic to write about, in any language
- **Number of revisions** — how many Critic → Writer cycles to allow before
  returning the last draft even if not fully approved

The final article(s) are saved under `Output/<timestamp>/`.

## Design decisions worth noting

- **No separate "Rewriter" agent.** The Critic's feedback is descriptive
  rather than an exact quote, so targeted line-editing isn't reliable —
  and the Writer that authored the piece is best positioned to revise it
  coherently. Revision reuses `WriterAgent.write()` with a `feedback`
  parameter instead.
- **Writer always outputs English**, independent of the input language.
  This keeps the Writer/Critic prompts (tuned and tested in English)
  consistent in quality, and pushes translation into a single, isolated,
  well-defined step at the very end.
- **Grounding rules were iterated based on real failures**, not designed
  upfront and left untested. Early drafts fabricated an entire section on
  a topic absent from the research, and later revisions leaked
  meta-commentary about source gaps (e.g. *"sources do not specifically
  address..."*) while trying to soften unsupported claims. Both were
  caught through repeated testing and fixed with explicit rules in the
  Writer prompt.

## Status

✅ Core pipeline complete: Researcher → Writer → Critic (with revision
loop) → optional Translator → Markdown/HTML output.
