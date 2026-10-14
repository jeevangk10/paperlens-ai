import json, re
import httpx
from ..config import settings

SYSTEM = """You are PaperLens AI. Analyze ONLY the supplied research paper text. Never invent facts, metrics, authors, datasets, references, or section content. If information is absent, say it is unavailable. Return valid JSON matching the requested schema. Include page numbers when the source text contains [Page N]. Clearly distinguish direct paper facts from cautious interpretation."""


def _demo(text: str):
    first = next((x.strip() for x in text.splitlines() if x.strip() and not x.startswith('[Page')), "Uploaded research paper")
    title = first[:180]
    return {
      "title": title, "authors": [], "abstract": "Demo mode: connect an AI API to generate a paper-specific abstract.",
      "research_problem": "Demo mode is active; the uploaded text is available, but an AI provider is not configured.",
      "objective": "Provide a safe demonstration without inventing paper facts.",
      "methodology": {"dataset":"Not generated in demo mode.","approach":"Connect an AI provider for structured analysis.","evaluation":"Not generated in demo mode."},
      "key_findings": ["AI analysis is disabled until AI_API_KEY is configured."],
      "conclusion": "Demo mode intentionally avoids fabricating research findings.",
      "limitations": ["No external AI provider configured."], "future_work": ["Configure AI_API_KEY and rerun analysis."],
      "sections": [], "concepts": [], "results": [], "references": [],
      "quick_summary": "Demo mode is active. Configure an AI provider to generate a paper-grounded summary.",
      "standard_summary": "Demo mode is active. Paper text extraction works, while AI-generated analysis is disabled until an API key is configured.",
      "detailed_summary": "PaperLens successfully extracts the uploaded PDF text. To prevent fabricated research claims, this demo does not synthesize academic findings without an AI provider.",
      "beginner_explanation": "The app has read the PDF text. Connect an AI provider to turn that text into a beginner-friendly explanation."
    }

async def analyze(text: str):
    if not settings.ai_api_key:
        return _demo(text)
    schema = {"title":"","authors":[],"abstract":"","research_problem":"","objective":"","methodology":{},"key_findings":[],"conclusion":"","limitations":[],"future_work":[],"sections":[],"concepts":[],"results":[],"references":[],"quick_summary":"","standard_summary":"","detailed_summary":"","beginner_explanation":""}
    prompt = SYSTEM + "\nReturn exactly this JSON shape:\n" + json.dumps(schema) + "\nPAPER:\n" + text[:180000]
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(f"{settings.ai_base_url.rstrip('/')}/chat/completions", headers={"Authorization":f"Bearer {settings.ai_api_key}"}, json={"model":settings.ai_model,"temperature":0.1,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]})
        r.raise_for_status()
        return json.loads(r.json()["choices"][0]["message"]["content"])


def retrieve(text: str, question: str, limit=5):
    terms = [t.lower() for t in re.findall(r"\w+", question) if len(t) > 3]
    chunks = re.split(r"\n\s*\n", text)
    scored=[]
    for c in chunks:
        low=c.lower(); score=sum(low.count(t) for t in terms)
        if score: scored.append((score,c))
    return [c for _,c in sorted(scored, reverse=True)[:limit]]

async def answer(text: str, question: str):
    context = "\n\n".join(retrieve(text, question))
    if not context:
        return {"answer":"I couldn't find enough information about this in the uploaded paper.","sources":[]}
    if not settings.ai_api_key:
        return {"answer":"Demo mode retrieved these paper passages. Configure AI_API_KEY for a generated answer.\n\n" + context[:2500],"sources":re.findall(r"\[Page (\d+)\]",context)}
    prompt=f"Answer the user's question using ONLY the context. If insufficient, say so. Cite page numbers from [Page N].\nQuestion: {question}\nContext:\n{context}"
    async with httpx.AsyncClient(timeout=60) as client:
        r=await client.post(f"{settings.ai_base_url.rstrip('/')}/chat/completions",headers={"Authorization":f"Bearer {settings.ai_api_key}"},json={"model":settings.ai_model,"temperature":0.1,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]})
        r.raise_for_status(); ans=r.json()["choices"][0]["message"]["content"]
    return {"answer":ans,"sources":re.findall(r"\[Page (\d+)\]",context)}

async def quiz(text: str, count: int, difficulty: str):
    if not settings.ai_api_key:
        return [{"question":"Which source should PaperLens use as the primary basis for paper-specific answers?","options":["The uploaded paper","Random web pages","Unrelated papers","Guesses"],"correct_answer":"The uploaded paper","explanation":"PaperLens is designed to ground answers in the uploaded paper.","page_number":None} for _ in range(count)]
    prompt=f"Generate {count} {difficulty} multiple-choice questions ONLY from this paper. Return JSON array with question, options, correct_answer, explanation, page_number. PAPER:\n{text[:180000]}"
    async with httpx.AsyncClient(timeout=90) as client:
        r=await client.post(f"{settings.ai_base_url.rstrip('/')}/chat/completions",headers={"Authorization":f"Bearer {settings.ai_api_key}"},json={"model":settings.ai_model,"temperature":0.2,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]})
        r.raise_for_status(); data=json.loads(r.json()["choices"][0]["message"]["content"])
        return data.get("questions", data if isinstance(data,list) else [])
