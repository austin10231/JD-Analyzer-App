# src/html_extractor.py

from bs4 import BeautifulSoup
import re

def extract_job_page_inputs(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    # ---------- 1) job_title ----------
    job_title = ""

    # 优先从 <title> 里拿（LinkedIn / 官网都稳）
    if soup.title and soup.title.text:
        title_text = soup.title.text.strip()
        # 常见格式： "Data Engineering Intern - Netflix | LinkedIn"
        # ---------- job_title (robust) ----------
        job_title = ""

        if soup.title and soup.title.text:
            title_text = soup.title.text.strip()

            # 去掉 LinkedIn / 领英后缀
            title_text = re.split(r"\||｜", title_text)[0]

            # 去掉“正在招聘 / is hiring”前缀
            title_text = re.sub(r".*正在招聘\s*", "", title_text)
            title_text = re.sub(r".*is hiring\s*", "", title_text, flags=re.I)

            # 常见格式：Data Engineering Intern, Summer 2026
            job_title = title_text.strip()
        

    # ---------- 2) company ----------
    company = ""

    # LinkedIn 常见：canonical URL 含 company
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        href = canonical["href"]
        # 例： data-engineering-intern-summer-2026-at-netflix-4348163604
        m = re.search(r"-at-([a-zA-Z0-9\-]+)-\d+", href)
        if m:
            company = m.group(1).replace("-", " ").title()

    # 兜底：从 title 中猜公司
    if not company and soup.title:
        if " at " in soup.title.text:
            company = soup.title.text.split(" at ")[-1].split("|")[0].strip()

    # ---------- 3) jd_text（内部用） ----------
    # 策略：取页面中“可见文本最多的区域”
    jd_text = ""

    candidates = soup.find_all(["section", "div"], recursive=True)
    best_text = ""
    for tag in candidates:
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > len(best_text):
            best_text = text

    jd_text = best_text

    return {
        "job_title": job_title,
        "company": company,
        "jd_text": jd_text
    }
