def extract_seniority(jd_text: str) -> str:
    """
    Determine job seniority level from job description text.
    """
    text = jd_text.lower()

    if any(keyword in text for keyword in ["intern", "internship"]):
        return "Intern"

    if any(keyword in text for keyword in ["senior", "lead", "principal", "staff"]):
        return "Senior"

    if any(keyword in text for keyword in ["mid-level", "3+ years", "4+ years", "5+ years"]):
        return "Mid"

    if any(keyword in text for keyword in ["entry-level", "junior", "new grad", "0-1 years", "1+ years"]):
        return "Entry"

    return "Not Specified"
