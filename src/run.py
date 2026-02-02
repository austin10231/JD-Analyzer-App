# src/run.py
from text_analyzer import analyze_jd_text

def analyze_jd(jd_text: str) -> dict:
    """
    统一入口：给前端/Flask 调用
    """
    return analyze_jd_text(jd_text)
