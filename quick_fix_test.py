#!/usr/bin/env python3
"""
Hızlı düzeltme testi
"""

import sys
sys.path.append('src')

from database.chroma_manager import ChromaManager
from retrieval.rag_pipeline import RAGPipeline

def test_fix():
    """Düzeltme testi"""
    print("🔧 DÜZELTİLEN SİMİLARİTY SKORLARI TEST")
    print("=" * 45)
    
    try:
        # ChromaManager test
        chroma = ChromaManager()
        
        question = "Türk Ceza Kanunu'nun amacı nedir?"
        print(f"❓ Test sorusu: {question}")
        
        results = chroma.search(question, n_results=3)
        
        print(f"\n📊 Düzeltilmiş similarity skorları:")
        for i, result in enumerate(results, 1):
            similarity = result['similarity']
            distance = result['distance'] 
            filename = result['metadata']['filename']
            
            print(f"  {i}. {filename}")
            print(f"     Distance: {distance:.3f}")
            print(f"     Similarity: {similarity:.3f}")
        
        # RAG Pipeline test
        print(f"\n🤖 RAG Pipeline Test:")
        rag = RAGPipeline()
        
        result = rag.query(question)
        
        print(f"✅ Cevap: {result['answer']}")
        print(f"📊 Güven Skoru: {result['confidence']}")
        print(f"📚 Kaynak Sayısı: {len(result['sources'])}")
        
        if result['sources']:
            print(f"📄 Ana kaynak: {result['sources'][0]['filename']}")
        
        # Başarı kontrolü
        if result['confidence'] > 0.5 and len(result['sources']) > 0:
            print(f"\n🎉 DÜZELTİLDİ! Sistem çalışıyor!")
            return True
        else:
            print(f"\n⚠️  Hala sorun var...")
            return False
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False

if __name__ == "__main__":
    test_fix()