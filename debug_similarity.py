#!/usr/bin/env python3
"""
Similarity ve threshold debug scripti
"""

import sys
sys.path.append('src')

from database.chroma_manager import ChromaManager

def debug_similarity_scores():
    """Similarity skorlarını debug et"""
    print("🔍 SİMİLARİTY SKORLARI DEBUG")
    print("=" * 40)
    
    try:
        # ChromaManager oluştur
        chroma = ChromaManager()
        
        # Test soruları
        test_questions = [
            "Türk Ceza Kanunu'nun amacı nedir?",
            "Hakim kanunda hüküm bulamazsa ne yapar?", 
            "İcra takibi nasıl başlar?",
            "ödeme emri nedir?",
            "kanun ne zaman yürürlüğe girdi?"
        ]
        
        for question in test_questions:
            print(f"\n❓ Soru: {question}")
            
            # Arama yap
            results = chroma.search(question, n_results=5)
            
            if results:
                print(f"📊 {len(results)} sonuç bulundu:")
                for i, result in enumerate(results):
                    distance = result.get('distance', 0)
                    similarity = result.get('similarity', 0)
                    filename = result['metadata']['filename']
                    content_preview = result['content'][:100] + "..."
                    
                    print(f"  {i+1}. {filename}")
                    print(f"     Distance: {distance:.3f}")
                    print(f"     Similarity: {similarity:.3f}")
                    print(f"     Preview: {content_preview}")
                    print()
            else:
                print("❌ Sonuç bulunamadı!")
        
        # Veritabanı durumunu kontrol et
        print("\n📊 VERİTABANI DURUMU:")
        stats = chroma.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Tüm belgeleri listele
        print("\n📚 VERİTABANINDAKİ BELGELER:")
        
        # ChromaDB'den tüm belgeleri çek
        all_docs = chroma.collection.get()
        
        if all_docs and all_docs['documents']:
            for i, (doc_id, document, metadata) in enumerate(zip(
                all_docs['ids'], 
                all_docs['documents'], 
                all_docs['metadatas']
            )):
                print(f"  {i+1}. {metadata.get('filename', 'unknown')}")
                print(f"     ID: {doc_id}")
                print(f"     Content: {document[:150]}...")
                print()
        else:
            print("  ❌ Veritabanında belge yok!")
        
    except Exception as e:
        print(f"❌ Debug hatası: {e}")
        import traceback
        traceback.print_exc()

def test_direct_similarity():
    """Direkt similarity testi"""
    print("\n🧪 DİREKT SİMİLARİTY TESTİ")
    print("=" * 40)
    
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # Model yükle
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        # Test metinleri
        query = "Türk Ceza Kanunu'nun amacı nedir?"
        documents = [
            "Türk Ceza Kanunu - Madde 1 (Amaç) Bu Kanunun amacı, suç teşkil eden fiilleri ve bunlara uygulanacak cezaları göstermektir.",
            "Türk Medeni Kanunu - Madde 1 (Kanunun uygulanması) Kanun, lafzı veya ruhu ile bir hükme bağlamış olduğu hallerde hâkim bu hükmü uygulamakla yükümlüdür.",
            "İcra ve İflas Kanunu - Temel Hükümler Madde 1: Bu kanun, alacaklıların alacaklarını elde etmeleri için takip edilecek usulleri düzenler."
        ]
        
        # Embeddingleri oluştur
        query_embedding = model.encode([query])
        doc_embeddings = model.encode(documents)
        
        # Cosine similarity hesapla
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        print(f"🔍 Query: {query}")
        print(f"\n📊 Manuel similarity skorları:")
        
        for i, (doc, sim) in enumerate(zip(documents, similarities)):
            print(f"  {i+1}. Similarity: {sim:.3f}")
            print(f"     Document: {doc[:100]}...")
            print()
        
        # En iyi eşleşme
        best_idx = np.argmax(similarities)
        print(f"✅ En iyi eşleşme: {best_idx+1}. belge (similarity: {similarities[best_idx]:.3f})")
        
    except Exception as e:
        print(f"❌ Direkt test hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_similarity_scores()
    test_direct_similarity()