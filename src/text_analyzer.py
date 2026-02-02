# src/text_analyzer.py
import re
from typing import Dict, List, Tuple

# -----------------------------
# 1) 词表：你后面想扩充很容易
# -----------------------------
LANGUAGES = ["python", "java", "c++", "c#", "javascript", "typescript", "sql", "nosql", "r", "go", "scala"]
CLOUD = ["aws", "azure", "gcp", "google cloud", "amazon web services"]
DATA = ["dataops", "devops", "data engineering", "analytics", "data systems", "database", "databases",
        "knowledge graph", "knowledge graphs", "multimodal", "multi-modal", "data discovery", "question answering"]
AI = ["llm", "llms", "large language model", "large language models", "foundation model", "foundation models",
      "ai agents", "agentic", "rag", "retrieval augmented generation", "prompt", "prompting",
      "prompt optimization", "reinforcement learning", "rl", "planning", "ai planning", "model inference",
      "generative ai", "genai", "code generation"]

FRAMEWORKS = ["langchain", "llamaindex", "hugging face", "pytorch", "tensorflow", "sklearn", "scikit-learn"]

DEGREE_WORDS = [
    ("phd", ["phd", "ph.d", "doctor", "doctoral"]),
    ("master", ["master", "m.s", "ms", "graduate"]),
    ("bachelor", ["bachelor", "b.s", "bs", "undergraduate"])
]

# -----------------------------
# 2) 基础清洗
# -----------------------------
def _normalize(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def _lower(text: str) -> str:
    return text.lower()

def _split_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.split("\n") if ln.strip()]

# -----------------------------
# 3) 章节切分（Required/Preferred/Responsibilities 等）
# -----------------------------
SECTION_HEADERS = [
    "your role and responsibilities",
    "topics include",
    "topics include but are not limited to",
    "required technical and professional expertise",
    "preferred technical and professional experience",
    "preferred education",
    "required education",
    "this internship is a great fit",
    "this role",
    "responsibilities",
]

def _detect_sections(text: str) -> Dict[str, str]:
    """
    用粗粒度方式把文本按常见 heading 切开。
    找不到也不报错。
    """
    raw = _normalize(text)
    low = _lower(raw)

    # 记录每个header出现的位置
    hits: List[Tuple[int, str]] = []
    for h in SECTION_HEADERS:
        idx = low.find(h)
        if idx != -1:
            hits.append((idx, h))

    hits.sort(key=lambda x: x[0])
    if not hits:
        return {"full": raw}

    sections: Dict[str, str] = {}
    for i, (pos, h) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(raw)
        chunk = raw[pos:end].strip()
        sections[h] = chunk
    sections["full"] = raw
    return sections

# -----------------------------
# 4) 抽取：公司 / 职位名 / 级别
# -----------------------------
def _extract_company(text: str) -> str:
    """
    尽量从开头/介绍里抓一个组织名。
    抓不到返回 "Unknown".
    """
    lines = _split_lines(text)
    head = " ".join(lines[:8])

    # 常见：IBM Research takes...
    m = re.search(r"\b([A-Z][A-Za-z&.\- ]{2,60})\s+(takes|is|means|has|are)\b", head)
    if m:
        cand = m.group(1).strip()
        # 过滤掉 "Introduction" 这种标题
        if cand.lower() not in ["introduction", "your role and responsibilities"]:
            return cand

    # 兜底：找 IBM / Google / Microsoft 这种大写品牌词
    m2 = re.search(r"\b(IBM Research|IBM|Google|Microsoft|Amazon|Meta|Apple)\b", text)
    if m2:
        return m2.group(1)

    return "Unknown"

def _extract_seniority(text: str) -> str:
    low = _lower(text)
    if "intern" in low or "internship" in low:
        return "Intern"
    if "new grad" in low or "graduate" in low:
        return "New Grad"
    if "senior" in low:
        return "Senior"
    return "Unknown"

def _infer_job_title(text: str, company: str, seniority: str) -> str:
    """
    JD文本里经常没有明确 title，这里用可解释的推断。
    """
    low = _lower(text)
    if "autonomous data management" in low:
        base = "Autonomous Data Management Systems"
    elif "data management" in low:
        base = "Data Management"
    elif "data systems" in low:
        base = "Data Systems"
    else:
        base = "Research"

    if seniority == "Intern":
        if company != "Unknown":
            return f"Research Intern – {base}"
        return f"Intern – {base}"
    return f"{base}"

# -----------------------------
# 5) 学历/专业方向
# -----------------------------
def _extract_degrees(text: str) -> Dict[str, List[str]]:
    """
    返回 required / preferred 两个列表（保证字段存在）
    """
    low = _lower(text)
    required, preferred = set(), set()

    # 优先利用关键词 "required" / "preferred" 周围窗口
    # 但你这份 JD：写了 “Pursuing an undergraduate degree or masters…”，preferred education 又写了 Bachelor
    # 所以：出现就都记录，再做归类
    for key, variants in DEGREE_WORDS:
        for v in variants:
            if re.search(rf"\b{re.escape(v)}\b", low):
                # 默认先放 required，再根据 "preferred education" 再补 preferred
                required.add(key)

    # preferred education 段落
    m = re.search(r"preferred education(.+?)(required technical|preferred technical|$)", low, flags=re.S)
    if m:
        seg = m.group(1)
        for key, variants in DEGREE_WORDS:
            for v in variants:
                if re.search(rf"\b{re.escape(v)}\b", seg):
                    preferred.add(key)

    # 规范化输出（映射回展示用）
    def _pretty(k: str) -> str:
        return {"phd": "PhD", "master": "Master", "bachelor": "Bachelor"}.get(k, k)

    return {
        "required": sorted({_pretty(x) for x in required}) if required else [],
        "preferred": sorted({_pretty(x) for x in preferred}) if preferred else []
    }

def _extract_fields(text: str) -> List[str]:
    low = _lower(text)
    fields = set()

    if "computer science" in low:
        fields.add("Computer Science")
    if "software engineering" in low:
        fields.add("Software Engineering")
    if "data engineering" in low:
        fields.add("Data Engineering")
    if "data systems" in low or "data management" in low:
        fields.add("Data Systems")
    if "related field" in low:
        fields.add("Related Field")

    return sorted(fields)

# -----------------------------
# 6) 技能：required vs preferred（按段落/关键词分类）
# -----------------------------
def _find_terms(text: str, vocab: List[str]) -> List[str]:
    low = _lower(text)
    found = set()
    for t in vocab:
        # 兼容 "knowledge graphs" / "knowledge graph"
        pat = rf"\b{re.escape(t)}\b"
        if re.search(pat, low):
            found.add(t)
    # 输出时做展示友好化
    return sorted({_pretty_skill(x) for x in found})

def _pretty_skill(s: str) -> str:
    s = s.strip()
    # 常见大写
    mapping = {
        "llm": "LLM",
        "llms": "LLMs",
        "nosql": "NoSQL",
        "sql": "SQL",
        "rag": "RAG",
        "genai": "Generative AI",
        "google cloud": "GCP",
        "amazon web services": "AWS",
        "knowledge graph": "Knowledge Graphs",
        "knowledge graphs": "Knowledge Graphs",
        "multi-modal": "Multimodal",
        "multimodal": "Multimodal",
        "ai agents": "AI Agents",
    }
    low = s.lower()
    if low in mapping:
        return mapping[low]
    # Title Case
    return s[0].upper() + s[1:] if s else s

def _extract_skills(text: str, sections: Dict[str, str]) -> Dict[str, List[str]]:
    """
    required_skills / preferred_skills 同时给出，并且再给分类桶（方便你网页扩展）
    """
    full = sections.get("full", text)

    # required 段：required technical...
    req_seg = sections.get("required technical and professional expertise", "")
    pref_seg = sections.get("preferred technical and professional experience", "")

    # 如果没有明确段落，就从全文推断
    if not req_seg:
        req_seg = full
    if not pref_seg:
        pref_seg = ""

    required = set()
    preferred = set()

    # required：语言/AI/数据/云
    required.update(_find_terms(req_seg, LANGUAGES))
    required.update(_find_terms(req_seg, AI))
    required.update(_find_terms(req_seg, DATA))
    required.update(_find_terms(req_seg, CLOUD))
    required.update(_find_terms(req_seg, FRAMEWORKS))

    # preferred：优先从 preferred 段落抓
    preferred.update(_find_terms(pref_seg, LANGUAGES))
    preferred.update(_find_terms(pref_seg, AI))
    preferred.update(_find_terms(pref_seg, DATA))
    preferred.update(_find_terms(pref_seg, CLOUD))
    preferred.update(_find_terms(pref_seg, FRAMEWORKS))

    # 这份 JD 的实际“偏好技能”就写在 preferred experience 段里
    # 再从 “Topics include …” 抓一些核心能力（通常也算 required/核心）
    topics_seg = sections.get("topics include but are not limited to", "") or sections.get("topics include", "")
    if topics_seg:
        required.update(_find_terms(topics_seg, LANGUAGES))
        required.update(_find_terms(topics_seg, AI))
        required.update(_find_terms(topics_seg, DATA))

    # 输出时：保证 list
    required_list = sorted(required)
    preferred_list = sorted(preferred)

    # 分类桶（你网页“完整分析”会更像样）
    buckets = {
        "languages": sorted(set(_find_terms(full, LANGUAGES))),
        "cloud": sorted(set(_find_terms(full, CLOUD))),
        "ai_ml": sorted(set(_find_terms(full, AI))),
        "data_systems": sorted(set(_find_terms(full, DATA))),
        "frameworks": sorted(set(_find_terms(full, FRAMEWORKS))),
    }

    return {
        "required_skills": required_list,
        "preferred_skills": preferred_list,
        "skill_buckets": buckets
    }

# -----------------------------
# 7) 责任/工作内容（bullet抽取）
# -----------------------------
def _extract_responsibilities(sections: Dict[str, str]) -> List[str]:
    seg = (
        sections.get("your role and responsibilities", "")
        + "\n"
        + (sections.get("topics include but are not limited to", "") or sections.get("topics include", ""))
    ).strip()

    if not seg:
        return []

    lines = _split_lines(seg)

    bullets = []
    for ln in lines:
        # 跳过标题行
        low = ln.lower()
        if low in SECTION_HEADERS or low.startswith("your role") or low.startswith("topics include"):
            continue

        # 常见 bullet / 列表
        if ln.startswith(("-", "•", "*")):
            bullets.append(ln.lstrip("-•* ").strip())
        else:
            # 对这种“Using..., Exploring..., Improving...”也当 bullet
            if re.match(r"^(Using|Exploring|Improving|Building)\b", ln):
                bullets.append(ln.strip())

    # 去重 + 控制长度
    out = []
    seen = set()
    for b in bullets:
        b = re.sub(r"\s+", " ", b).strip()
        if b and b not in seen:
            seen.add(b)
            out.append(b)
    return out

# -----------------------------
# 8) 总控：对外接口
# -----------------------------
def analyze_jd_text(jd_text: str) -> Dict:
    """
    永远返回完整 schema；抽不到就给空/Unknown。
    """
    jd_text = _normalize(jd_text)
    sections = _detect_sections(jd_text)

    company = _extract_company(jd_text)
    seniority = _extract_seniority(jd_text)
    job_title = _infer_job_title(jd_text, company, seniority)

    degrees = _extract_degrees(jd_text)
    fields = _extract_fields(jd_text)

    skills_pack = _extract_skills(jd_text, sections)
    responsibilities = _extract_responsibilities(sections)

    # 你网页想“像样”，最好再给 summary / keywords
    keywords = sorted(set(skills_pack["skill_buckets"]["ai_ml"] + skills_pack["skill_buckets"]["data_systems"]))
    summary = ""
    if responsibilities:
        summary = responsibilities[0]

    return {
        "company": company,
        "job_title": job_title,
        "seniority": seniority,

        "education": degrees,                 # {"required":[], "preferred":[]}
        "fields": fields,                     # e.g., ["Computer Science", "Data Systems", ...]

        "responsibilities": responsibilities, # list of bullets

        "required_skills": skills_pack["required_skills"],
        "preferred_skills": skills_pack["preferred_skills"],
        "skill_buckets": skills_pack["skill_buckets"],

        "keywords": keywords,
        "summary": summary
    }
