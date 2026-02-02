# src/text_analyzer.py
import re
from typing import Dict, List, Tuple

import re

_STOP_TITLES = {
    "about the job", "introduction", "your role", "your role and responsibilities",
    "responsibilities", "preferred education", "required technical and professional expertise",
    "preferred technical and professional experience", "topics include", "topics include but are not limited to",
}

def _clean_company_candidate(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    s = re.sub(r"^(about the job|introduction|company|organization)\s*[:\-]?\s*", "", s, flags=re.I)
    if len(s.split()) > 6:
        return ""
    return s

def extract_company_from_text(jd_text: str) -> str:
    text = _normalize(jd_text)

    # 常见标题词，避免被误判为公司
    BAD_HEADINGS = {
        "about the job", "introduction", "your role", "your role and responsibilities",
        "responsibilities", "what you'll do", "what you will do", "requirements",
        "preferred qualifications", "preferred", "education"
    }

    # 1) At <Company>,
    m = re.search(r"\bAt\s+([A-Z][A-Za-z0-9&.\-]+(?:\s+[A-Z][A-Za-z0-9&.\-]+){0,4})\s*,", text)
    if m:
        c = m.group(1).strip()
        if c.lower() not in BAD_HEADINGS:
            return c

    # 2) <Company> Research / <Company> Labs / <Company> AI
    m = re.search(r"\b([A-Z][A-Za-z0-9&.\-]+)\s+(Research|Labs|Lab|AI|Data|Engineering|Semiconductor)\b", text)
    if m:
        c = m.group(1).strip()
        if c.lower() not in BAD_HEADINGS:
            return c

    # 3) fallback：从前 15 行里找“像公司名”的行（且过滤标题）
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    head = lines[:15]

    for ln in head:
        low = ln.lower().strip(": -")
        if low in BAD_HEADINGS:
            continue
        # 很短的一行、Title Case，可能是公司/部门名
        if 2 <= len(ln) <= 40 and re.match(r"^[A-Z][A-Za-z0-9&.\- ]+$", ln):
            # 避免 "About the job Netflix" 这种组合
            ln2 = re.sub(r"(?i)^about the job\s+", "", ln).strip()
            if ln2 and ln2.lower() not in BAD_HEADINGS:
                return ln2

    return ""


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
import re
from typing import Dict, List, Tuple

def _normalize(text: str) -> str:
    if not text:
        return ""
    # unify newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # normalize fancy quotes
    text = (text
        .replace("’", "'")
        .replace("“", '"').replace("”", '"')
        .replace("–", "-").replace("—", "-")
    )

    # normalize bullets
    text = text.replace("•", "- ")

    # collapse weird spaces
    text = re.sub(r"[ \t]+", " ", text)
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

def _detect_sections(jd_text: str) -> Dict[str, str]:
    """
    Return blocks of text by section key.
    """
    text = _normalize(jd_text)
    lines = [ln.strip() for ln in text.split("\n")]

    # 标题模式：尽量覆盖常见JD写法（大小写不敏感）
    SECTION_PATTERNS = {
        "responsibilities": re.compile(
            r"^(responsibilities|what (you'?ll|you will) do|what you'?ll work on|your role( and responsibilities)?|role and responsibilities|in this role(,)? you will)\s*[:\-]?$",
            re.IGNORECASE
        ),
        "requirements": re.compile(
            r"^(requirements|required (skills|experience|expertise)|required technical|required technical and professional expertise|basic qualifications)\s*[:\-]?$",
            re.IGNORECASE
        ),
        "preferred": re.compile(
            r"^(preferred (skills|experience|expertise)|preferred technical|preferred technical and professional experience|preferred qualifications)\s*[:\-]?$",
            re.IGNORECASE
        ),
        "education": re.compile(
            r"^(education|preferred education|minimum education|qualification|qualifications)\s*[:\-]?$",
            re.IGNORECASE
        ),
    }

    # 找到每个 section 的起点行号
    starts: List[Tuple[int, str]] = []
    for i, ln in enumerate(lines):
        if not ln:
            continue
        # “看起来像标题”的行：短、没有句号结尾、词数不太多
        if len(ln) <= 80:
            for key, pat in SECTION_PATTERNS.items():
                if pat.match(ln):
                    starts.append((i, key))
                    break

    # 没检测到任何标题，就返回整段给 requirements/responsibilities 备用
    if not starts:
        return {"__all__": "\n".join(lines).strip()}

    # 根据 starts 切块
    starts.sort(key=lambda x: x[0])
    blocks: Dict[str, str] = {}
    for idx, (start_i, key) in enumerate(starts):
        end_i = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start_i + 1 : end_i]).strip()
        # 同一个key出现多次就拼起来
        if block:
            blocks[key] = (blocks.get(key, "") + "\n" + block).strip()

    return blocks


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
    """
    Extract bullet responsibilities.
    """
    # 1) 优先用 responsibilities block
    block = sections.get("responsibilities", "").strip()

    # 2) 如果没有，就用全文里“你将会…”那段做兜底
    if not block:
        block = sections.get("__all__", "")

    if not block:
        return []

    lines = [ln.strip() for ln in block.split("\n") if ln.strip()]

    bullets: List[str] = []
    bullet_pat = re.compile(r"^\s*(?:[-*]|(\d+)[\).\]])\s+(.*)$")

    for ln in lines:
        m = bullet_pat.match(ln)
        if m:
            item = m.group(2).strip()
            if item:
                bullets.append(item)

    # 如果没有 bullet，就从句子里抽一些 “will/you will” 句子作为责任描述
    if not bullets:
        # 简单句子切分
        sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", block).strip())
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            if re.search(r"\byou will\b|\byou'll\b|\bwill\b", s_clean, re.IGNORECASE):
                bullets.append(s_clean)
            if len(bullets) >= 6:
                break

    # 去重保持顺序
    seen = set()
    out = []
    for b in bullets:
        if b.lower() not in seen:
            seen.add(b.lower())
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

    company = extract_company_from_text(jd_text)
    if not company:
        company = _extract_company(jd_text)  # 你原来的兜底

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
