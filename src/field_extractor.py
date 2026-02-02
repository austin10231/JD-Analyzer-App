def extract_fields(jd_text: str) -> list[str]:
    """
    Extract academic or professional background fields from job description text.
    """
    text = jd_text.lower()
    fields = set()

    field_keywords = {
        "Computer Science": ["computer science", "cs"],
        "Data Science": ["data science"],
        "Information Systems": ["information systems", "information system", "is"],
        "Engineering": ["engineering", "engineer"],
        "Mathematics": ["mathematics", "math"],
        "Statistics": ["statistics", "statistic"]
    }

    for field, keywords in field_keywords.items():
        if any(keyword in text for keyword in keywords):
            fields.add(field)

    if "related field" in text or "related discipline" in text:
        fields.add("Related Field")

    return list(fields)
