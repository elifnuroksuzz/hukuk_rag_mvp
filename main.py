#!/usr/bin/env python3
"""
Hukuk RAG API - Ana Sunucu Dosyası
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import time
import os
from datetime import datetime

# ChromaDB import kontrolü
try:
    from src.database.chroma_manager import ChromaManager
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("⚠️ ChromaDB bulunamadı, temel mod çalışacak")

# FastAPI uygulaması
app = FastAPI(
    title="Hukuk RAG API",
    description="Hukuk belgeleri için RAG (Retrieval-Augmented Generation) API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global değişkenler
documents_count = 0
start_time = time.time()
chroma_manager = None

# ChromaDB başlat
if CHROMA_AVAILABLE:
    try:
        chroma_manager = ChromaManager()
        print("✅ ChromaDB bağlantısı başarılı")
    except Exception as e:
        print(f"⚠️ ChromaDB başlatma hatası: {e}")
        chroma_manager = None

# ------------------ MODELLER ------------------ #
class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = None
    max_sources: Optional[int] = 5

class QueryResponse(BaseModel):
    query: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    response_time: float

# ------------------ ENDPOINTLER ------------------ #
@app.get("/")
async def root():
    """Ana sayfa"""
    return {
        "message": "Hukuk RAG API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health"
    }

@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    components = {
        "api": "healthy",
        "database": "healthy" if chroma_manager else "unavailable",
        "llm": "healthy"
    }
    status = "healthy" if chroma_manager else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "components": components,
        "uptime_seconds": time.time() - start_time
    }

@app.get("/stats")
async def get_stats():
    """Sistem istatistikleri"""
    total_docs = 0
    if chroma_manager:
        try:
            stats = chroma_manager.get_stats()
            total_docs = stats.get('total_documents', 0)
        except:
            pass
    
    uptime = time.time() - start_time
    return {
        "total_documents": total_docs,
        "llm_model": "test-model",
        "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2" if chroma_manager else "none",
        "uptime": f"{uptime:.2f} seconds",
        "chroma_status": "connected" if chroma_manager else "disconnected"
    }

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """RAG sorgusu"""
    start_query_time = time.time()
    try:
        if chroma_manager:
            search_results = chroma_manager.search(
                request.question, 
                n_results=request.max_sources or 5
            )
            if search_results:
                context = "\n".join([doc['content'] for doc in search_results[:3]])
                answer = generate_answer(request.question, context)
                confidence = calculate_confidence(search_results)
                sources = [
                    {
                        "filename": doc['metadata'].get('filename', 'unknown'),
                        "content": doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                        "similarity": doc['similarity'],
                        "chunk_index": doc['metadata'].get('chunk_index', 0)
                    }
                    for doc in search_results
                ]
            else:
                answer = "Üzgünüm, sorunuzla ilgili belgelerde bilgi bulunamadı."
                confidence = 0.0
                sources = []
        else:
            answer = get_fallback_answer(request.question)
            confidence = 0.5
            sources = []
        
        response_time = time.time() - start_query_time
        return QueryResponse(
            query=request.question,
            answer=answer,
            confidence=confidence,
            sources=sources,
            response_time=response_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sorgu hatası: {str(e)}")

@app.get("/documents/search")
async def search_documents(query: str, limit: int = 5):
    """Belgelerde arama"""
    try:
        if chroma_manager:
            results = chroma_manager.search(query, n_results=limit)
            return {"query": query, "count": len(results), "results": results}
        else:
            return {"query": query, "count": 0, "results": [], "error": "ChromaDB bağlantısı yok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arama hatası: {str(e)}")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Dosya yükleme"""
    global documents_count
    if not chroma_manager:
        raise HTTPException(status_code=503, detail="ChromaDB bağlantısı yok")
    
    uploaded_files = []
    for file in files:
        try:
            content = await file.read()
            text_content = content.decode('utf-8', errors='ignore')
            doc_data = {
                'content': text_content,
                'filename': file.filename,
                'file_type': file.content_type,
                'file_size': len(content),
                'timestamp': datetime.now().isoformat(),
                'chunk_index': 0,
                'total_chunks': 1
            }
            success = chroma_manager.add_documents([doc_data])
            if success:
                documents_count += 1
                uploaded_files.append({"filename": file.filename, "size": len(content), "type": file.content_type, "status": "success"})
            else:
                uploaded_files.append({"filename": file.filename, "status": "failed"})
        except Exception as e:
            uploaded_files.append({"filename": file.filename, "error": str(e), "status": "error"})
    
    return {
        "message": f"{len([f for f in uploaded_files if f.get('status') == 'success'])} dosya başarıyla yüklendi",
        "files": uploaded_files
    }

@app.delete("/documents")
async def clear_documents():
    """Tüm belgeleri sil"""
    global documents_count
    if not chroma_manager:
        raise HTTPException(status_code=503, detail="ChromaDB bağlantısı yok")
    try:
        success = chroma_manager.delete_all()
        if success:
            old_count = documents_count
            documents_count = 0
            return {"message": f"{old_count} belge silindi", "remaining_documents": 0}
        else:
            raise HTTPException(status_code=500, detail="Belgeler silinemedi")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Silme hatası: {str(e)}")

# ------------------ YARDIMCI FONKSİYONLAR ------------------ #
def generate_answer(question: str, context: str) -> str:
    q = question.lower()
    if "ceza kanunu" in q:
        return f"Türk Ceza Kanunu ile ilgili sorunuza dayanarak: {context[:300]}..."
    elif "medeni kanun" in q:
        return f"Türk Medeni Kanunu kapsamında: {context[:300]}..."
    elif "anayasa" in q:
        return f"Anayasa hükümleri çerçevesinde: {context[:300]}..."
    else:
        return f"Belgelerimizde bulunan bilgilere göre: {context[:300]}..."

def calculate_confidence(results: List[Dict]) -> float:
    if not results: return 0.0
    avg_similarity = sum(doc.get('similarity', 0) for doc in results) / len(results)
    return min(avg_similarity, 1.0)

def get_fallback_answer(question: str) -> str:
    q = question.lower()
    if "ceza kanunu" in q:
        return "Türk Ceza Kanunu, suç teşkil eden fiilleri ve bunlara uygulanacak cezaları düzenler."
    elif "medeni kanun" in q:
        return "Türk Medeni Kanunu, özel hukuk ilişkilerini düzenleyen temel kanundur."
    elif "anayasa" in q:
        return "Türkiye Cumhuriyeti Anayasası, devletin temel yapısını ve hukuki düzenini belirler."
    else:
        return "Bu konuda detaylı bilgi için lütfen belge yükleyiniz ve ChromaDB bağlantısını kontrol ediniz."

# ------------------ MAIN ------------------ #
if __name__ == "__main__":
    print("🚀 Hukuk RAG API Başlatılıyor...")
    print("📍 URL: http://localhost:8000")
    print("📚 Dokümantasyon: http://localhost:8000/docs")
    print("❤️ Sağlık Kontrolü: http://localhost:8000/health")
    print(f"🔌 ChromaDB: {'Bağlı' if chroma_manager else 'Bağlı Değil'}")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
