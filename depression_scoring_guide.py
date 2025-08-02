scoring_guides = {
    "phq9": {
        "range": [0, 27],
        "thresholds": [
            [1, 4, "Minimal depression"],
            [5, 9, "Mild depression"],
            [10, 14, "Moderate depression"],
            [15, 19, "Moderately severe depression"],
            [20, 27, "Severe depression"]
        ],
        "note": "Each of the 9 items is scored 0-3 (Not at all = 0, Several days = 1, More than half the days = 2, Nearly every day = 3). Update question pool's score_range from [0, 3] to [0, 1, 2, 3] for phq9_1, phq9_2, phq9_9."
    },
    "kads11": {
        "range": [0, 22],
        "thresholds": [
            [0, 5, "Minimal or Normal feelings"],
            [6, 11, "Mild feelings"],
            [12, 16, "Moderate feelings"],
            [17, 22, "Severe feelings"]
        ],
        "note": "Based on question pool's 11 items with 3 options (0-2: Hardly ever = 0, Much of the time = 1, Most of the time = 2), max score 22. Standard KADS-11 uses 4 options (0-3), max 33; update question pool to align or adjust thresholds."
    },
    "rcads_depression": {
        "range": [0, 30],
        "note": "Raw scores (10 items, 0-3: Never = 0, Sometimes = 1, Often = 2, Always = 3) use age/gender-based T-scores; Below 65: Normal, 65-70: Borderline, 70+: Clinical. Question pool has 9 items (max 27), update score_range from [0, 3] to [0, 1, 2, 3]."
    },
    "dass21_depression": {
        "range": [0, 42],
        "thresholds": [
            [0, 9, "Normal"],
            [10, 13, "Mild"],
            [14, 20, "Moderate"],
            [21, 27, "Severe"],
            [28, 42, "Extremely Severe"]
        ],
        "note": "Raw subscale scores (7 items, 0-3: Not at all = 0, To some degree = 1, Considerably = 2, Very much = 3) multiplied by 2. Update question pool's score_range from [0, 3] to [0, 1, 2, 3]."
    },
    "cesd": {
        "range": [0, 60],
        "thresholds": [
            [0, 15, "Low risk of depression"],
            [16, 60, "Possible risk for clinical depression"]
        ],
        "note": "20 items, scored 0-3 (Rarely = 0, Some = 1, Occasionally = 2, Most = 3). Items 4, 8, 12, 16 reverse-scored (Rarely = 3, Some = 2, Occasionally = 1, Most = 0). Ensure score_range is [0, 1, 2, 3] for non-reverse items, [3, 2, 1, 0] for reverse items."
    },
    "mfqsf": {
        "range": [0, 26],
        "thresholds": [
            [0, 6, "Minimal or Normal feelings"],
            [7, 12, "Mild feelings"],
            [13, 19, "Moderate feelings"],
            [20, 26, "Severe feelings"]
        ],
        "note": "13 items, scored 0-2 (Not True = 0, Sometimes = 1, True = 2)."
    }
}