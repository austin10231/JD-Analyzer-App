# src/skill_extractor.py

import re
from typing import List, Tuple

def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences using simple punctuation rules.
    """
    return re.split(r"[.\n]+", text)

def extract_skills(jd_text: str) -> Tuple[List[str], List[str]]:
    """
    Extract required and preferred skills using sentence-level semantics.
    """
    text = jd_text.lower()
    sentences = split_sentences(text)

    skill_keywords = {
        "Python": ["python"],
        "SQL": ["sql"],
        "Machine Learning": ["machine learning", "ml"],
        "Deep Learning": ["deep learning"],
        "Data Analysis": ["data analysis", "data analytics"],
        "AWS": ["aws", "amazon web services"],
        "Docker": ["docker"],
        "Git": ["git"]
    }

    preferred_triggers = [
        "nice to have",
        "preferred",
        "a plus",
        "plus if",
        "bonus",
        "optional"
    ]

    required_skills = set()
    preferred_skills = set()

    for sentence in sentences:
        if not sentence.strip():
            continue

        is_preferred_sentence = any(trigger in sentence for trigger in preferred_triggers)

        for skill, keywords in skill_keywords.items():
            if any(keyword in sentence for keyword in keywords):
                if is_preferred_sentence:
                    preferred_skills.add(skill)
                else:
                    required_skills.add(skill)

    # required 优先级更高
    preferred_skills -= required_skills

    return sorted(required_skills), sorted(preferred_skills)
