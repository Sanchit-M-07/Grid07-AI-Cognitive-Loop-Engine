# router.py — Phase 1
# this is the "who cares about this post?" logic
# instead of blasting every post to every bot, we embed the post text
# and find which bots are topically close using cosine similarity

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.phase1_router.personas import BOT_PERSONAS

# using MiniLM here because it's fast and decent quality
# doesn't need an API key either which is nice for local dev
model = SentenceTransformer("all-MiniLM-L6-v2")


class PersonaRouter:

    def __init__(self):
        self.bot_ids = []
        self.vectors = []
        self._load_personas()

    def _load_personas(self):
        print("[router] loading personas into vector store...")

        for bot_id, persona in BOT_PERSONAS.items():
            vec = model.encode(persona["description"])
            self.bot_ids.append(bot_id)
            self.vectors.append(vec)
            print(f"  stored: {bot_id} ({persona['name']})")

        # stack into a matrix so we can do batch cosine sim in one shot
        self.vectors = np.array(self.vectors)
        print("[router] ready\n")

    def route_post_to_bots(self, post_content: str, threshold: float = 0.3):
        """
        Takes an incoming post, embeds it, compares against all persona vectors.
        Returns a list of bots whose score clears the threshold.

        threshold of 0.3 works well with MiniLM — bump it up if you're getting
        too many false positives, lower it if nothing's matching
        """
        print(f'[router] incoming post: "{post_content}"')

        post_vec = model.encode(post_content).reshape(1, -1)
        scores = cosine_similarity(post_vec, self.vectors)[0]

        results = []
        for i, bot_id in enumerate(self.bot_ids):
            score = float(scores[i])
            persona_name = BOT_PERSONAS[bot_id]["name"]
            print(f"  {bot_id} ({persona_name}) → {score:.4f}")

            if score >= threshold:
                results.append(
                    {
                        "bot_id": bot_id,
                        "name": persona_name,
                        "score": round(score, 4),
                    }
                )

        if results:
            print(f"\n  matched {len(results)} bot(s):")
            for r in results:
                print(f"    → {r['bot_id']} score={r['score']}")
        else:
            print(f"\n  no matches above {threshold} — post might be too generic?")

        return results


# quick smoke test — run this file directly to see routing in action
if __name__ == "__main__":
    router = PersonaRouter()

    posts = [
        "OpenAI just released a new model that might replace junior developers.",
        "The Federal Reserve raised interest rates again, causing market volatility.",
        "Big Tech companies are lobbying to kill privacy legislation in Congress.",
    ]

    for p in posts:
        print("=" * 55)
        router.route_post_to_bots(p)
        print()
