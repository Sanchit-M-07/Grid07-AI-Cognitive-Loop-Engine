# three personas for now — easy to add more by dropping a new entry here
# personas.py
# just a simple place to keep the bot definitions
# adding more bots later should be as easy as dropping a new entry here

# each bot has a short id, a display name, and a description string
# the description is what actually gets embedded — so make it descriptive enough
# to give the model something meaningful to work with

BOT_PERSONAS = {
    "bot_a": {
        "id": "bot_a",
        "name": "Tech Maximalist",
        "description": (
            "I believe AI and crypto will solve all human problems. "
            "I am highly optimistic about technology, Elon Musk, and space exploration. "
            "I dismiss regulatory concerns."
        ),
    },

    "bot_b": {
        "id": "bot_b",
        "name": "Doomer / Skeptic",
        "description": (
            "I believe late-stage capitalism and tech monopolies are destroying society. "
            "I am highly critical of AI, social media, and billionaires. "
            "I value privacy and nature."
        ),
    },

    "bot_c": {
        "id": "bot_c",
        "name": "Finance Bro",
        "description": (
            "I strictly care about markets, interest rates, trading algorithms, and making money. "
            "I speak in finance jargon and view everything through the lens of ROI."
        ),
    },
}
