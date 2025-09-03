scoring_guides = {
    # ----------------
    # Depression
    # ----------------
    "phq9": {
        "range": [0, 27],
        "thresholds": [
            [0, 4, "Minimal depression"],
            [5, 9, "Mild depression"],
            [10, 14, "Moderate depression"],
            [15, 19, "Moderately severe depression"],
            [20, 27, "Severe depression"]
        ]
    },
    "kads11": {
        "range": [0, 22],   # 11 items × max 2
        "thresholds": [
            [0, 8, "Minimal or normal"],
            [9, 16, "Mild"],
            [17, 22, "Moderate–Severe"]
        ],
        "note": "Your earlier bands (0–33) assumed 0–3 scoring; current items are 0–2. If you intend 0–3 anchors, update item scoring (options & scores) and restore the 0–33 range."
    },
    "cesd": {
        "range": [0, 60],
        "thresholds": [
            [0, 15, "Low risk"],
            [16, 60, "Possible risk for clinical depression"]
        ],
        "note": "Reverse-score items 4, 8, 12, 16."
    },
    "mfqsf": {
        "range": [0, 26],
        "thresholds": [
            [0, 6, "Minimal or normal"],
            [7, 12, "Mild"],
            [13, 19, "Moderate"],
            [20, 26, "Severe"]
        ]
    },
    "dass21_depression": {
        "range": [0, 42],
        "thresholds": [
            [0, 9, "Normal"],
            [10, 13, "Mild"],
            [14, 20, "Moderate"],
            [21, 27, "Severe"],
            [28, 42, "Extremely severe"]
        ],
        "note": "Score the 7-item depression subscale (0–21) and multiply by 2 before interpretation."
    },

    # ----------------
    # Anxiety (screens & core)
    # ----------------
    "dsm5_level1_anxiety": {
        "range": [0, 12],  # 3 items × 0–4
        "note": "Screen only; use as a gateway to level-2 or disorder-specific scales."
    },
    "promis_anxiety_l2": {
        "range": [4, 20],  # 4 items × 1–5 (per your anchors)
        "note": "Interpret with PROMIS T-scores (lookup table). Raw sums are not comparable across ages."
    },
    "gad7": {
        "range": [0, 21],
        "thresholds": [
            [0, 4, "Minimal anxiety"],
            [5, 9, "Mild anxiety"],
            [10, 14, "Moderate anxiety"],
            [15, 21, "Severe anxiety"]
        ]
    },

    # SCARED (Child)
    "scared_total": {
        "range": [0, 82],  # 41 items × 0–2
        "thresholds": [
            [0, 24, "Below clinical cutoff"],
            [25, 82, "Elevated (screen-positive)"]
        ],
        "note": "Use subscale cutoffs for Panic, GAD, Separation, Social, School avoidance when possible; confirm with clinical assessment."
    },

    # RCADS – Anxiety subset
    "rcads_anxiety": {
        "range": [0, 141],  # 47 anxiety items × 0–3 (per your selection)
        "note": "Interpret via age/sex T-scores. Rule of thumb: T<65 normal, 65–69 borderline, ≥70 clinical, but always use official norms."
    },

    # SCAS
    "scas_total": {
        "range": [0, 144],  # 36 selected items × 0–3 (in your set)
        "note": "SCAS uses age/sex norms/percentiles; no universal raw cutoff. Convert to T-scores/percentiles."
    },

    # Youth PSC-17 (Internalizing focus)
    "y_psc17_internalizing": {
        "range": [0, 22],  # 11 items × 0–2 (your subset)
        "thresholds": [
            [0, 4, "Below cutoff"],
            [5, 22, "Elevated internalizing (screen-positive)"]
        ],
        "note": "Standard PSC-17 total cutoff is ≥15; internalizing subscale cutoff commonly ≥5."
    },

    # DASS-Y (Anxiety/Stress items you included)
    "dassy_anxiety_stress": {
        "range": [0, 42],  # 14 items × 0–3 (mixed anxiety+stress per your selection)
        "note": "No widely adopted clinical bands for DASS-Y short forms; consider separate reporting for the anxiety-like and stress-like items, or map to percentiles if you have norms."
    },

    # DASS-21 (Anxiety & Stress)
    "dass21_anxiety": {
        "range": [0, 42],
        "thresholds": [
            [0, 7, "Normal"],
            [8, 9, "Mild"],
            [10, 14, "Moderate"],
            [15, 19, "Severe"],
            [20, 42, "Extremely severe"]
        ],
        "note": "Score 7 anxiety items (0–21) then multiply by 2."
    },
    "dass21_stress": {
        "range": [0, 42],
        "thresholds": [
            [0, 14, "Normal"],
            [15, 18, "Mild"],
            [19, 25, "Moderate"],
            [26, 33, "Severe"],
            [34, 42, "Extremely severe"]
        ],
        "note": "Score 7 stress items (0–21) then multiply by 2."
    },

    # LSAS-CA (child/adolescent)
    "lsas_ca_total": {
        "range": [0, 144],  # 24 situations × (fear 0–3 + avoidance 0–3)
        "note": "Higher scores indicate greater social anxiety/avoidance. Cutoffs vary across studies (e.g., ~60 for probable SAD); use with diagnostic interview."
    },

    # PDSS (adapted)
    "pdss": {
        "range": [0, 28],  # 7 items × 0–4
        "note": "Use as a severity index for panic; study-specific cutoffs vary. Consider flagging item scores ≥3 and totals in the teens as high severity pending clinical review."
    },

    # ----------------
    # OCD
    # ----------------
    "oci_r": {
        "range": [0, 72],  # 18 × 0–4
        "note": "Report total and (optionally) subscales. Cutoffs vary (often low-20s to upper-20s) by population; use norms if available."
    },
    "ybocs": {
        "range": [0, 40],  # 10 × 0–4
        "thresholds": [
            [0, 7, "Subclinical"],
            [8, 15, "Mild"],
            [16, 23, "Moderate"],
            [24, 31, "Severe"],
            [32, 40, "Extreme"]
        ]
    },

    # ----------------
    # PTSD
    # ----------------
    "pcl5": {
        "range": [0, 80],  # 20 × 0–4
        "note": "Common screening cut score ranges ~31–33 in adults; use age-appropriate guidance and clinical judgment for adolescents."
    },
    "ies_r": {
        "range": [0, 88],  # 22 × 0–4
        "note": "No universal diagnostic cutoff; higher scores reflect greater post-traumatic stress symptoms. Many services use internal norms."
    }
}
