# src/run_demo.py

from text_preprocessor import clean_jd_text
from title_company_extractor import extract_job_title_and_company
from seniority_extractor import extract_seniority
from degree_extractor import extract_degree_requirement
from field_extractor import extract_fields
from skill_extractor import extract_skills
import json

def analyze_jd(raw_text: str) -> dict:
    cleaned_text = clean_jd_text(raw_text)

    job_title, company = extract_job_title_and_company(cleaned_text)
    seniority = extract_seniority(cleaned_text)
    degree = extract_degree_requirement(cleaned_text)
    fields = extract_fields(cleaned_text)
    required_skills, preferred_skills = extract_skills(cleaned_text)

    return {
        "job_title": job_title,
        "company": company,
        "seniority": seniority,
        "degree_requirement": degree,
        "fields": fields,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "raw_text": raw_text
    }


if __name__ == "__main__":
    sample_jd = """
    About the job
Netflix is one of the world's leading entertainment services, with over 300 million paid memberships in over 190 countries enjoying TV series, films and games across a wide variety of genres and languages. Members can play, pause and resume watching as much as they want, anytime, anywhere, and can change their plans at any time.

The Teams

The Data Engineering function is foundational to Netflix’s success. Data Science and Engineering (DSE) teams across the company aim to improve various aspects of our business. These teams build software and data solutions and create foundational data products that enable end-to-end analysis, run sophisticated experimentation, and generate key insights. This is an exciting space to gain hands-on experience with new technologies and the company’s unique culture.

Who Are You?

You are a curious, collaborative, resourceful, and motivated student who is eager to learn from a team of senior engineers. You possess a passion for problem-solving and are comfortable tackling complex, open-ended challenges using data-driven solutions.

Must-Haves

Currently enrolled in a full-time accredited academic program (M.S., or Ph.D.) in Computer Science, Engineering, Data Science, or a related technical field graduating in December 2026, Summer 2027 or later.
To be intern-eligible, you must be returning to school for one semester or quarter post-Summer internship.
Solid programming proficiency in at least one major language, such as Python, Java, or Scala.
Strong foundational knowledge of SQL (any variant).
Strong fundamentals in data structures and algorithms.
Comfortable applying software engineering best practices, such as version control, testing, and code reviews.
 Excellent communication and collaboration skills.
Nice-to-Haves

Previous project or internship experience working with large-scale data.
Familiarity with distributed frameworks (e.g., Spark, Kafka) and distributed system architectures.
Knowledge of MPP/Cloud data warehouse solutions (e.g., Snowflake, Redshift, BigQuery, Hive, Iceberg).
Exposure to schema design or data modeling concepts.
Experience in preparing and enriching data for machine learning pipelines.

What You'll Do

As a fully embedded within a Data Engineering team on a high-impact project, you will:

Collaborate closely with data scientists, analysts, product managers, and senior engineers to understand analytical needs and translate them into scalable data solutions.
Design, build, deploy, and maintain robust data pipelines.
Build data products that answer high-impact business questions.
Learn and apply data modeling best practices.
Help increase the automation and scale of complex data sets.
Gain experience applying data engineering principles to solve internet scale problems

The Summer Internship

At Netflix, we offer a personalized experience for interns, and our aim is to offer an experience that mimics what it is like to actually work here. We match qualified interns with projects and groups based on interests and skill sets, and fully embed interns within those groups for the summer. Netflix is a unique place to work and we live by our values, so it's worth learning more about our culture.

Internships are typically 12 weeks long. Conditions permitting, our summer internships will be located in our Los Gatos, CA office, or in our Los Angeles, CA office, depending on the team. The overall market range for Netflix Internships is typically $40/hour - $110/hour. This market range is based on total compensation (vs. only base salary), which is in line with our compensation philosophy. Netflix is a unique culture and environment. Learn more here.

Our culture is unique, and we live by our values. For more information on what it's like to work at Netflix, please take a look at our culture memo.

Inclusion is a Netflix value and we strive to host a meaningful interview experience for all candidates. If you want an accommodation/adjustment for a disability or any other reason during the hiring process, please send a request to your recruiting partner.

We are an equal-opportunity employer and celebrate diversity, recognizing that diversity builds stronger teams. We approach diversity and inclusion seriously and thoughtfully. We do not discriminate on the basis of race, religion, color, ancestry, national origin, caste, sex, sexual orientation, gender, gender identity or expression, age, disability, medical condition, pregnancy, genetic makeup, marital status, or military service.

Job is open for no less than 7 days and will be removed when the position is filled.
    """

    result = analyze_jd(sample_jd)
    print(json.dumps(result, indent=2, ensure_ascii=False))
