# src/text_analyzer.py
import re
from typing import Dict, List, Tuple

import re

_STOP_TITLES = {
    "about the job", "introduction", "your role", "your role and responsibilities",
    "responsibilities", "preferred education", "required technical and professional expertise",
    "preferred technical and professional experience", "topics include", "topics include but are not limited to",
}

import re

# 这些词很容易被误判成“公司”
_BAD_COMPANY = {
    "about", "about the job", "job", "job overview", "company overview",
    "introduction", "overview", "responsibilities", "what you'll do",
    "what you will do", "requirements", "qualifications", "preferred",
    "education", "skills", "role", "your role", "the role",
    "electrical", "software", "engineering", "computer", "science",
    "data", "analytics", "research"
}

def extract_company_from_text(jd_text: str) -> str:
    """
    Best-effort extract company name from pasted JD text.
    Prefer explicit "Company:" lines, then strong textual signals like:
      - "At Netflix, ..."
      - "IBM Research ..."
      - "KLA is a global leader ..."
    """
    text = jd_text or ""
    t = re.sub(r"\r\n?", "\n", text).strip()
    if not t:
        return ""

    # 1) Explicit "Company: X"
    m = re.search(r"(?im)^\s*company\s*[:\-]\s*(.+?)\s*$", t)
    if m:
        cand = m.group(1).strip()
        cand = re.split(r"\s{2,}|\s*\|\s*|\s*•\s*", cand)[0].strip()
        if cand and cand.lower() not in _BAD_COMPANY:
            return cand

    # 2) "At {Company}, ..."  (Netflix / Google / Apple)
    m = re.search(r"(?im)^\s*(?:at|within)\s+([A-Z][A-Za-z0-9&.\-]{1,40})\b", t)
    if m:
        cand = m.group(1).strip()
        if cand and cand.lower() not in _BAD_COMPANY:
            return cand

    # 3) Acronym company at beginning: "KLA is ...", "IBM Research ..."
    #    - first non-empty line
    first_lines = [ln.strip() for ln in t.split("\n") if ln.strip()][:6]
    head = " ".join(first_lines)

    # 3a) "KLA is a ..." / "IBM is ..."
    m = re.search(r"^\s*([A-Z][A-Z0-9&.\-]{1,15})\s+is\b", head)
    if m:
        cand = m.group(1).strip()
        if cand.lower() not in _BAD_COMPANY:
            return cand

    # 3b) "IBM Research ..." -> IBM
    m = re.search(r"^\s*(IBM)\s+Research\b", head, re.IGNORECASE)
    if m:
        return "IBM"

    # 3c) "{Company} is a global leader ..." where Company can be TitleCase too (e.g., "OpenAI is ...")
    m = re.search(r"^\s*([A-Z][A-Za-z0-9&.\-]{1,40})\s+is\s+(?:a|an|the)\b", head)
    if m:
        cand = m.group(1).strip()
        if cand.lower() not in _BAD_COMPANY:
            return cand

    # 4) Last resort: look for frequent brand-like token (all-caps or TitleCase) that repeats
    #    Keep it conservative to avoid "Electrical".
    tokens = re.findall(r"\b[A-Z][A-Za-z0-9&.\-]{2,20}\b", t)
    freq = {}
    for w in tokens:
        lw = w.lower()
        if lw in _BAD_COMPANY:
            continue
        freq[w] = freq.get(w, 0) + 1

    if freq:
        # pick the most repeated; require at least 2 occurrences to be safe
        best = max(freq.items(), key=lambda x: x[1])
        if best[1] >= 2:
            return best[0]

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
            r"^(?:"
            r"responsibilities|"
            r"what\s+(?:you['’]ll|you\s+will)\s+do|"
            r"what\s+(?:you['’]ll|you\s+will)\s+be\s+doing|"
            r"what\s+(?:you['’]ll|you\s+will)\s+work\s+on|"
            r"your\s+role(?:\s+and\s+responsibilities)?|"
            r"role\s+and\s+responsibilities|"
            r"in\s+this\s+role,?\s+you\s+will|"
            r"what\s+we['’]re\s+looking\s+for"
            r")\s*[:\-–—]?\s*$",
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
    Supports unicode bullets and multiline bullet continuation.
    """
    block = sections.get("responsibilities", "").strip()

    # fallback：没检测到 responsibilities section，就用全文兜底
    if not block:
        block = sections.get("__all__", "") or ""

    if not block.strip():
        return []

    # 保留原始换行（不要一上来 strip 掉每行），否则无法做“续行合并”
    raw_lines = block.splitlines()

    bullets: List[str] = []

    # 识别更多 bullet 形式：- * • · ● ◦ ‣ 以及 1. 1) (1) 1]
    bullet_pat = re.compile(
        r"^\s*(?:"
        r"[-*•·●◦‣]|"                 # unicode / ascii bullets
        r"\(?\d{1,3}\)?[.)\]]|"        # 1. / 1) / (1) / 1]
        r"[a-zA-Z][.)\]]"              # a) / A)
        r")\s+(.*)\s*$"
    )

    # 一些“像标题”的行：不要当作续行拼进去
    header_like = re.compile(
        r"^\s*(?:about\s+the\s+job|company\s+overview|requirements|preferred|education|qualifications|"
        r"what\s+(?:you['’]ll|you\s+will)\s+do|responsibilities|your\s+role|"
        r"required\s+technical|preferred\s+technical|skills)\s*[:\-–—]?\s*$",
        re.IGNORECASE,
    )

    current = None

    for ln in raw_lines:
        if not ln.strip():
            # 空行：结束续行（但不强制结束 bullet）
            continue

        m = bullet_pat.match(ln)
        if m:
            item = m.group(1).strip()
            if item:
                bullets.append(item)
                current = len(bullets) - 1
            continue

        # 非 bullet 行：如果前面已经有 bullet，且这一行看起来是“续行”，就拼到上一条 bullet 后面
        if current is not None:
            # 满足续行条件：不是新标题、且这行不是明显的 section 头
            if not header_like.match(ln):
                # 拼接（用空格连接，避免把句子粘住）
                bullets[current] = (bullets[current].rstrip() + " " + ln.strip()).strip()
                continue

        # 如果没有 bullet：尝试从句子里抽取职责（you will / build / design 等）
        # 只在 bullets 为空时做，避免污染已经抽出来的 bullets
        if not bullets:
            # 简单句切分
            sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", block).strip())
            for s in sentences:
                s_clean = s.strip()
                if not s_clean:
                    continue
                if re.search(r"\b(you\s+will|you['’]ll|responsible\s+for|design|build|develop|collaborate|implement|maintain|deliver)\b",
                             s_clean, re.IGNORECASE):
                    bullets.append(s_clean)
            break

    # 去重（保持顺序）
    seen = set()
    dedup = []
    for b in bullets:
        key = b.lower()
        if key not in seen:
            seen.add(key)
            dedup.append(b)

    return dedup


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
