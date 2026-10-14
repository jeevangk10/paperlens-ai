from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import Base,engine
from .routers import auth,papers
app=FastAPI(title='PaperLens AI API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
Base.metadata.create_all(bind=engine)
app.include_router(auth.router,prefix='/api')
app.include_router(papers.router,prefix='/api')
@app.get('/health')
def health(): return {'status':'ok','ai_configured':bool(settings.ai_api_key)}
