# content_engine.py — Phase 2
# this is the autonomous posting brain
# each bot wakes up, picks a topic it cares about, searches for context,
# then writes a post — all without being told what to say
#
# flow: decide what to search → run the search → draft the post
# output is always a JSON object with bot_id, topic, post_content

import os
import json
import re
from typing import TypedDict

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from src.phase1_router.personas import BOT_PERSONAS

# swap this out for ChatOpenAI or Ollama if you'd prefer
# see .env.example for the key setup
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.8,
)


# ── mock search tool ─────────────────────────────────────────

# for now we just return hardcoded headlines based on keywords
# it's enough to give the bot something to react to
# in prod this would hit a real searxng instance


@tool
def mock_searxng_search(query: str) -> str:
    """Simulates a SearxNG search. Returns relevant headlines based on the query keywords."""
    q = query.lower()

    if any(word in q for word in ["crypto", "bitcoin", "blockchain", "web3"]):
        return (
            "Bitcoin hits new all-time high amid ETF approvals. "
            "BlackRock's spot BTC ETF sees record $1.2B inflow in a single day."
        )

    if any(word in q for word in ["ai", "openai", "llm", "gpt", "model"]):
        return (
            "OpenAI releases GPT-5 claiming PhD-level reasoning on STEM benchmarks. "
            "Sam Altman says AGI is closer than most people think."
        )

    if any(
        word in q for word in ["market", "stock", "fed", "rate", "trading", "interest"]
    ):
        return (
            "S&P 500 jumps 2.3% after Fed signals rate pause. "
            "Hedge funds rotate into tech as yield curve inverts for 18th consecutive month."
        )

    if any(
        word in q for word in ["privacy", "surveillance", "data", "regulation", "gdpr"]
    ):
        return (
            "EU AI Act passes final vote. "
            "Meta fined $1.3B for GDPR violations in transatlantic data transfer case."
        )

    if any(word in q for word in ["space", "elon", "tesla", "spacex", "mars"]):
        return (
            "SpaceX Starship completes first full orbital flight test. "
            "Elon Musk sets 2029 as target date for crewed Mars mission."
        )

    if any(
        word in q for word in ["climate", "environment", "nature", "carbon", "green"]
    ):
        return (
            "UN report warns of irreversible climate tipping points by 2035. "
            "Big Tech carbon pledges called greenwashing in new investigative report."
        )

    # fallback for anything else
    return (
        "Tech layoffs hit record high as AI automation accelerates across sectors. "
        "Economists debate whether universal basic income can offset structural unemployment."
    )


# ── graph state ───────────────────────────────────────────────
# just a typed dict that gets passed between nodes
# each node reads what it needs and writes what comes next


class PostState(TypedDict):
    bot_id: str
    persona: str
    search_query: str
    search_results: str
    topic: str
    post_content: str
    final_output: dict


# ── node 1: decide what to search ────────────────────────────
def decide_search(state: PostState) -> PostState:
    print(f"\n[node 1] {state['bot_id']} deciding what to post about...")

    prompt = f"""You're a social media bot. Your worldview:
"{state['persona']}"

Pick ONE topic you'd want to post about today — something that fits your personality.
Then write a short search query (3-5 words) to find recent news about it.

Reply ONLY with valid JSON, nothing else:
{{"topic": "...", "search_query": "..."}}"""

    resp = llm.invoke(prompt)
    raw = resp.content.strip()
    # strip markdown fences if the model added them
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    parsed = json.loads(raw)
    state["topic"] = parsed["topic"]
    state["search_query"] = parsed["search_query"]

    print(f"  topic: {state['topic']}")
    print(f"  query: {state['search_query']}")
    return state


# ── node 2: run the search ────────────────────────────────────
def run_search(state: PostState) -> PostState:
    print(f"\n[node 2] searching for: '{state['search_query']}'")

    result = mock_searxng_search.invoke({"query": state["search_query"]})
    state["search_results"] = result

    print(f"  got: {result[:100]}...")
    return state


# ── node 3: write the post ────────────────────────────────────
def draft_post(state: PostState) -> PostState:
    print(f"\n[node 1] {state['bot_id']} picking topic...")

    prompt = f"""You're a social media bot. Your worldview:
"{state['persona']}"

Today's topic: {state['topic']}

What's in the news:
{state['search_results']}

Write a tweet (max 280 chars) that sounds exactly like you — opinionated, direct, no hashtags.

Then return ONLY this JSON (nothing else):
{{"bot_id": "{state['bot_id']}", "topic": "{state['topic']}", "post_content": "<tweet here>"}}"""

    resp = llm.invoke(prompt)
    raw = resp.content.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    # sometimes the model wraps it in extra text — just grab the JSON part
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        parsed = json.loads(match.group())
    else:
        # fallback — shouldn't happen often
        parsed = {
            "bot_id": state["bot_id"],
            "topic": state["topic"],
            "post_content": raw[:280],
        }

    parsed["post_content"] = parsed["post_content"][:280]
    state["final_output"] = parsed

    print(f"  drafted: {parsed['post_content'][:80]}...")
    return state


# ── assemble the graph ────────────────────────────────────────
def build_graph():
    g = StateGraph(PostState)

    g.add_node("decide_search", decide_search)
    g.add_node("run_search", run_search)
    g.add_node("draft_post", draft_post)

    g.set_entry_point("decide_search")
    g.add_edge("decide_search", "run_search")
    g.add_edge("run_search", "draft_post")
    g.add_edge("draft_post", END)

    return g.compile()


def generate_post_for_bot(bot_id: str) -> dict:
    persona = BOT_PERSONAS[bot_id]
    graph = build_graph()

    init: PostState = {
        "bot_id": bot_id,
        "persona": persona["description"],
        "search_query": "",
        "search_results": "",
        "topic": "",
        "post_content": "",
        "final_output": {},
    }

    print(f"\n{'='*55}")
    print(f"[langgraph] running pipeline → {bot_id} ({persona['name']})")
    print("=" * 55)

    result_state = graph.invoke(init)
    output = result_state["final_output"]

    print(f"\n[langgraph] final JSON:")
    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    for bot in ["bot_a", "bot_b", "bot_c"]:
        generate_post_for_bot(bot)
        print()
