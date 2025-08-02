# Define welcome questions separately
welcome_questions = [
    {
        "id": "welcome_1",
        "text": "Before we vibe — what should we call you? Could be your name, your nickname, or your secret alter ego from the multiverse. Whatever feels comfy — this is your space.",
        "type": "text",
        "options": None
    },
    {
        "id": "welcome_2",
        "text": "If your brain was a playlist today, what would it be called? Think album titles like: 'Lo-Fi Overthinking'",
        "type": "text",
        "options": None
    },
    {
        "id": "welcome_3",
        "text": "Which emoji has been carrying your mental state lately? (Or just type yours. No wrong answer, promise.)",
        "type": "text",
        "options": None
    },
    {
        "id": "welcome_4",
        "text": "What’s one thing that kept you semi-sane this week? A meme that wrecked you (in a good way)? A song? A snack? Someone who actually texted back?",
        "type": "text",
        "options": None
    },
    {
        "id": "welcome_5",
        "text": "Be honest, how’s your sleep game lately?",
        "type": "radio",
        "options": [
            "Winning = full 8 hours",
            "Lol what is sleep?",
            "Sleep is my only bliss",
            "Sleep but still tired"
        ],
        "score_range": [0, 1, 2, 3]  # for storage, not clinical scoring
    }
]