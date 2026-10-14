from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Paper, Conversation, Message, Quiz
from ..security import current_user
from ..config import settings
from ..services.pdf_service import extract_pdf
from ..services.ai_service import analyze, answer, quiz
from ..schemas import ChatIn, QuizIn, CompareIn
router=APIRouter(prefix='/papers',tags=['papers'])

def owned(db,pid,user):
    p=db.get(Paper,pid)
    if not p or p.user_id!=user.id: raise HTTPException(404,'Paper not found')
    return p

@router.post('/upload')
async def upload(file:UploadFile=File(...), db:Session=Depends(get_db), user:User=Depends(current_user)):
    if file.content_type!='application/pdf': raise HTTPException(400,'Only PDF files are supported')
    data=await file.read()
    if len(data)>settings.max_file_size: raise HTTPException(413,'PDF is too large')
    try: text,pages,_=extract_pdf(data)
    except Exception: raise HTTPException(400,'Could not read this PDF')
    if len(text.strip())<50: raise HTTPException(400,'No readable text was found. Try a text-based PDF or configure OCR.')
    p=Paper(user_id=user.id,title=file.filename.rsplit('.',1)[0],authors=[],file_name=file.filename,page_count=pages,raw_text=text,status='analyzing')
    db.add(p); db.commit(); db.refresh(p)
    try:
        p.analysis=await analyze(text); p.title=p.analysis.get('title') or p.title; p.authors=p.analysis.get('authors',[]); p.status='ready'; p.last_opened=datetime.utcnow(); db.commit(); db.refresh(p)
    except Exception as e:
        p.status='error'; db.commit(); raise HTTPException(502,'AI analysis failed. Check your AI configuration.')
    return serialize(p)

@router.get('')
def list_papers(db:Session=Depends(get_db),user=Depends(current_user)):
    return [serialize(p) for p in db.query(Paper).filter(Paper.user_id==user.id).order_by(Paper.uploaded_at.desc()).all()]

@router.post('/demo')
def demo(db:Session=Depends(get_db),user=Depends(current_user)):
    text='[Page 1]\nPaperLens Demo: A sample research paper about explainable artificial intelligence.\n\n[Page 2]\nThe paper studies how explanations can help beginners understand machine-learning predictions.'
    analysis={"title":"A Demo Study of Explainable AI","authors":["Demo Author"],"abstract":"A demonstration paper used by PaperLens.","research_problem":"How can complex model predictions be explained to learners?","objective":"Explore accessible explanations for machine-learning outputs.","methodology":{"dataset":"Demo dataset","approach":"Illustrative explanation workflow","evaluation":"Demo only"},"key_findings":["Clear explanations can make model outputs easier to discuss."],"conclusion":"This is demo data, not a real publication.","limitations":["Synthetic demo content."],"future_work":["Upload a real paper for analysis."],"sections":[],"concepts":[{"term":"Explainable AI","simple_definition":"Methods that help people understand AI outputs.","technical_definition":"Techniques for interpreting model behavior.","example":"Feature importance.","why_it_matters":"It can improve understanding of model predictions."}],"results":[],"references":[],"quick_summary":"A demo research paper showing how explanations can make AI easier to understand.","standard_summary":"This sample paper explores accessible explanations for machine-learning predictions and is included so users can test PaperLens without uploading a document.","detailed_summary":"The demo describes a simple research scenario around explainable AI. It is intentionally synthetic and should not be treated as a real academic source.","beginner_explanation":"Think of explainable AI as adding a reason to an AI answer so a person can understand how the system arrived at it."}
    p=Paper(user_id=user.id,title=analysis['title'],authors=analysis['authors'],file_name='demo.pdf',page_count=2,raw_text=text,analysis=analysis,status='ready'); db.add(p); db.commit(); db.refresh(p); return serialize(p)

@router.get('/{pid}')
def get_paper(pid:int,db:Session=Depends(get_db),user=Depends(current_user)):
    p=owned(db,pid,user); p.last_opened=datetime.utcnow(); db.commit(); return serialize(p)

@router.delete('/{pid}')
def delete_paper(pid:int,db:Session=Depends(get_db),user=Depends(current_user)):
    p=owned(db,pid,user); db.delete(p); db.commit(); return {'ok':True}

@router.post('/{pid}/chat')
async def chat(pid:int,data:ChatIn,db:Session=Depends(get_db),user=Depends(current_user)):
    p=owned(db,pid,user); result=await answer(p.raw_text,data.question)
    c=db.get(Conversation,data.conversation_id) if data.conversation_id else None
    if not c: c=Conversation(user_id=user.id,paper_id=p.id); db.add(c); db.commit(); db.refresh(c)
    db.add_all([Message(conversation_id=c.id,role='user',content=data.question),Message(conversation_id=c.id,role='assistant',content=result['answer'])]); db.commit()
    return {**result,'conversation_id':c.id}

@router.post('/{pid}/quiz')
async def make_quiz(pid:int,data:QuizIn,db:Session=Depends(get_db),user=Depends(current_user)):
    p=owned(db,pid,user); questions=await quiz(p.raw_text,data.count,data.difficulty); q=Quiz(paper_id=p.id,difficulty=data.difficulty,question_count=len(questions),questions=questions); db.add(q); db.commit(); db.refresh(q); return {'id':q.id,'questions':questions}

@router.post('/compare')
def compare(data:CompareIn,db:Session=Depends(get_db),user=Depends(current_user)):
    a=owned(db,data.paper_id,user); b=owned(db,data.other_paper_id,user)
    def field(p,k): return (p.analysis or {}).get(k,'Unavailable')
    return {'paper_a':{'id':a.id,'title':a.title,'problem':field(a,'research_problem'),'objective':field(a,'objective'),'methodology':field(a,'methodology'),'findings':field(a,'key_findings'),'limitations':field(a,'limitations')},'paper_b':{'id':b.id,'title':b.title,'problem':field(b,'research_problem'),'objective':field(b,'objective'),'methodology':field(b,'methodology'),'findings':field(b,'key_findings'),'limitations':field(b,'limitations')}}

def serialize(p):
    return {'id':p.id,'title':p.title,'authors':p.authors or [],'file_name':p.file_name,'page_count':p.page_count,'status':p.status,'uploaded_at':p.uploaded_at.isoformat() if p.uploaded_at else None,'last_opened':p.last_opened.isoformat() if p.last_opened else None,'analysis':p.analysis or {}}
