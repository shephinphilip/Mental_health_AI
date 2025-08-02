question_pool = [
    {
    "id": "phq9_1",
    "category": "depression",
    "text": "Little interest or pleasure in doing things?",
    "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
    "score_range": [0, 1, 2, 3]
    },
    {"id": "phq9_2", "category": "depression", "text": "Feeling down, depressed, or hopeless?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"], "score_range": [0, 1, 2, 3]},
    {"id": "phq9_9", "category": "depression", "text": "Thoughts that you would be better off dead, or of hurting yourself?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"], "score_range": [0, 1, 2, 3]},
    {"id": "kads_6", "category": "depression", "text": "Feeling tired, fatigued, low in energy, hard to get motivated?", "options": ["Hardly Ever", "Much of The Time", "Most of The Time", "All of The Time"], "score_range": [0, 1, 2, 3]},
    {"id": "kads_7", "category": "depression", "text": "Thoughts or actions of suicide or self-harm?", "options": ["No thoughts or plans or actions", "Occasional thoughts, no plans or actions", "Frequent thoughts, no plans or actions", "Plans and/or actions that have hurt"], "score_range": [0, 1, 2, 3]},
    {"id": "pcl5_1", "category": "ptsd", "text": "Repeated, disturbing memories of a stressful experience?", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"], "score_range": [0, 1, 2, 3,4]},
    {"id": "pcl5_15", "category": "ptsd", "text": "Feeling very upset when something reminded you of a stressful experience?", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"], "score_range": [0, 1, 2, 3,4]},
    {"id": "hama_1", "category": "anxiety", "text": "Feeling tense or 'wound up'?", "options": ["Not present", "Mild", "Moderate", "Severe", "Very Severe"], "score_range": [0, 1, 2, 3,4]},
    {"id": "hama_7", "category": "anxiety", "text": "Feelings of fear or worry?", "options": ["Not present", "Mild", "Moderate", "Severe", "Very Severe"], "score_range": [0, 1, 2, 3,4]},


#KADS-11 – Kutcher Adolescent Depression Scale

    {"id": "kads_1", "category": "depression", "text": "Low mood, sadness, feeling blah or down, depressed, or just generally unhappy?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_2", "category": "depression", "text": "Feeling tired, feeling fatigued, or having little energy?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_3", "category": "depression", "text": "Feeling that you are a failure or not good enough or feeling very discouraged?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_4", "category": "depression", "text": "Trouble concentrating, thinking, or making decisions?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_5", "category": "depression", "text": "Feeling slowed down, having trouble getting going, or keeping up your usual pace?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_6", "category": "depression", "text": "Feeling restless or fidgety, like you have to keep moving or can't sit still?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_7", "category": "depression", "text": "Sleep problems can't sleep, waking up early, or sleeping too much?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_8", "category": "depression", "text": "Feeling hopeless about the future?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_9", "category": "depression", "text": "Feeling that life isn't worth living or thinking about death or suicide?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_10", "category": "depression", "text": "Feeling irritable or angry?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},
    {"id": "kads_11", "category": "depression", "text": "Avoiding friends, wanting to be alone more than usual?", "options": ["Hardly ever", "Much of the time", "Most of the time"], "score_range": [0, 1, 2]},


#RCADS – Depression Subscale

    {"id": "rcads_dep_1", "category": "depression", "text": "Nothing is much fun anymore.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_2", "category": "depression", "text": "I feel sad or empty.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_3", "category": "depression", "text": "I feel lonely.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_4", "category": "depression", "text": "I cry a lot.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_5", "category": "depression", "text": "I feel like I have no energy.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_6", "category": "depression", "text": "I feel like I am not as good as other kids.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_7", "category": "depression", "text": "I have trouble sleeping.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_8", "category": "depression", "text": "I feel like something awful might happen.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},
    {"id": "rcads_dep_9", "category": "depression", "text": "I feel like my life is bad.", "options": ["Never", "Sometimes", "Often", "Always"], "score_range": [0, 1, 2, 3]},


#DASS-21 – Depression Subscale

    {"id": "dass_dep_1", "category": "depression", "text": "I couldn't seem to experience any positive feeling at all.", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me to a considerable degree", "Applied to me very much"], "score_range": [0, 1, 2, 3]},
    {"id": "dass_dep_2", "category": "depression", "text": "I found it difficult to work up the initiative to do things.", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me to a considerable degree", "Applied to me very much"], "score_range": [0, 1, 2, 3]},
    {"id": "dass_dep_3", "category": "depression", "text": "I felt that I had nothing to look forward to.", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me to a considerable degree", "Applied to me very much"], "score_range": [0, 1, 2, 3]},
    {"id": "dass_dep_4", "category": "depression", "text": "I felt down-hearted and blue.", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me to a considerable degree", "Applied to me very much"], "score_range": [0, 1, 2, 3]},
    {"id": "dass_dep_5", "category": "depression", "text": "I was unable to become enthusiastic about anything.", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me to a considerable degree", "Applied to me very much"], "score_range": [0, 1, 2, 3]},
    {"id": "dass_dep_6", "category": "depression", "text": "I felt I wasn't worth much as a person.", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me to a considerable degree", "Applied to me very much"], "score_range": [0, 1, 2, 3]},
    {"id": "dass_dep_7", "category": "depression", "text": "I felt that life was meaningless.", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me to a considerable degree", "Applied to me very much"], "score_range": [0, 1, 2, 3]},


#CES-D – Center for Epidemiologic Studies Depression Scale

    {"id": "cesd_1", "category": "depression", "text": "I was bothered by things that usually don't bother me.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_2", "category": "depression", "text": "I did not feel like eating; my appetite was poor.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_3", "category": "depression", "text": "I felt that I could not shake off the blues even with help from my family or friends.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_4", "category": "depression", "text": "I felt that I was just as good as other people.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [3, 2, 1, 0]},  # reverse scored
    {"id": "cesd_5", "category": "depression", "text": "I had trouble keeping my mind on what I was doing.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_6", "category": "depression", "text": "I felt depressed.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_7", "category": "depression", "text": "I felt that everything I did was an effort.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_8", "category": "depression", "text": "I felt hopeful about the future.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [3, 2, 1, 0]},  # reverse scored
    {"id": "cesd_9", "category": "depression", "text": "I thought my life had been a failure.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_10", "category": "depression", "text": "I felt fearful.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_11", "category": "depression", "text": "My sleep was restless.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_12", "category": "depression", "text": "I was happy.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [3, 2, 1, 0]},  # reverse scored
    {"id": "cesd_13", "category": "depression", "text": "I talked less than usual.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_14", "category": "depression", "text": "I felt lonely.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_15", "category": "depression", "text": "People were unfriendly.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_16", "category": "depression", "text": "I enjoyed life.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [3, 2, 1, 0]},  # reverse scored
    {"id": "cesd_17", "category": "depression", "text": "I had crying spells.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_18", "category": "depression", "text": "I felt sad.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_19", "category": "depression", "text": "I felt that people dislike me.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},
    {"id": "cesd_20", "category": "depression", "text": "I could not get going.", "options": ["Rarely or none of the time", "Some or a little of the time", "Occasionally or a moderate amount of time", "Most or all of the time"], "score_range": [0, 1, 2, 3]},



# MFQ-SF – Mood and Feelings Questionnaire (Short Form)

    {"id": "mfqsf_1", "category": "depression", "text": "I felt miserable or unhappy.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_2", "category": "depression", "text": "I didn't enjoy anything at all.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_3", "category": "depression", "text": "I felt so tired I just sat around and did nothing.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_4", "category": "depression", "text": "I was very restless.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_5", "category": "depression", "text": "I felt I was no good anymore.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_6", "category": "depression", "text": "I cried a lot.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_7", "category": "depression", "text": "I found it hard to think properly or concentrate.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_8", "category": "depression", "text": "I hated myself.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_9", "category": "depression", "text": "I was a bad person.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_10", "category": "depression", "text": "I felt lonely.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_11", "category": "depression", "text": "I thought nobody really loved me.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_12", "category": "depression", "text": "I thought I could never be as good as other kids.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},
    {"id": "mfqsf_13", "category": "depression", "text": "I did everything wrong.", "options": ["Not true", "Sometimes", "True"], "score_range": [0, 1, 2]},


]