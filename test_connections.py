#!/usr/bin/env python3
"""
Hukuk RAG MVP - Bağlantı Testi
"""

import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# .env dosyasını yükle
load_dotenv()

def test_huggingface_api():
    """Hugging Face Router API testi"""
    print("🔍 Hugging Face API testi başlıyor...")
    
    try:
        # API bilgilerini al
        base_url = os.getenv("BASE_URL")
        api_key = os.getenv("API_KEY")
        model = os.getenv("MODEL")
        
        print(f"📡 Base URL: {base_url}")
        print(f"🤖 Model: {model}")
        
        # OpenAI compatible client oluştur
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # Test mesajı gönder
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Sen bir Türk hukuk asistanısın."},
                {"role": "user", "content": "Merhaba, nasılsın?"}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        print("✅ Hugging Face API bağlantısı BAŞARILI!")
        print(f"🤖 Yanıt: {response.choices[0].message.content}")
        print(f"📊 Token kullanımı: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ Hugging Face API hatası: {str(e)}")
        return False

def test_alternative_model():
    """Alternatif model testi"""
    print("\n🔍 Alternatif model testi başlıyor...")
    
    try:
        base_url = os.getenv("BASE_URL")
        api_key = os.getenv("API_KEY")
        model2 = os.getenv("MODEL2")
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        response = client.chat.completions.create(
            model=model2,
            messages=[
                {"role": "user", "content": "Test mesajı"}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        print("✅ Alternatif model bağlantısı BAŞARILI!")
        print(f"🤖 Yanıt: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Alternatif model hatası: {str(e)}")
        return False

def test_embedding_model():
    """Embedding model testi (sentence-transformers)"""
    print("\n🔍 Embedding model testi başlıyor...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Türkçe destekleyen embedding model
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        # Test metni
        test_texts = [
            "Bu bir hukuk belgesidir.",
            "Mahkeme kararı önemlidir.",
            "Türk Ceza Kanunu madde 1"
        ]
        
        # Embeddingleri oluştur
        embeddings = model.encode(test_texts)
        
        print("✅ Embedding model BAŞARILI!")
        print(f"📏 Embedding boyutu: {embeddings.shape}")
        print(f"📝 Test metinleri: {len(test_texts)} adet işlendi")
        return True
        
    except Exception as e:
        print(f"❌ Embedding model hatası: {str(e)}")
        print("💡 Çözüm: pip install sentence-transformers")
        return False

def test_chromadb():
    """ChromaDB testi"""
    print("\n🔍 ChromaDB testi başlıyor...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Test için geçici ChromaDB oluştur
        client = chromadb.Client(Settings(
            persist_directory="./test_chroma",
            is_persistent=True
        ))
        
        # Test koleksiyonu oluştur
        collection = client.create_collection(
            name="test_collection",
            get_or_create=True
        )
        
        print("✅ ChromaDB BAŞARILI!")
        print(f"📚 Koleksiyon oluşturuldu: {collection.name}")
        
        # Test temizliği
        client.delete_collection(name="test_collection")
        print("🧹 Test verisi temizlendi")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB hatası: {str(e)}")
        print("💡 Çözüm: pip install chromadb")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 HUKUK RAG MVP - BAĞLANTI TESTLERİ")
    print("=" * 50)
    
    results = {}
    
    # Testleri çalıştır
    results['huggingface'] = test_huggingface_api()
    results['alternative_model'] = test_alternative_model()
    results['embedding'] = test_embedding_model()
    results['chromadb'] = test_chromadb()
    
    # Sonuç raporu
    print("\n" + "=" * 50)
    print("📋 TEST SONUÇLARI:")
    
    for test_name, result in results.items():
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"  {test_name.upper()}: {status}")
    
    # Genel durum
    success_count = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 GENEL DURUM: {success_count}/{total_tests} test başarılı")
    
    if success_count == total_tests:
        print("🎉 Tüm bağlantılar hazır! Projeye devam edebiliriz.")
    else:
        print("⚠️  Bazı bağlantılar başarısız. Eksik kütüphaneleri yükleyin.")
        print("💡 Çalıştırın: pip install -r requirements.txt")

if __name__ == "__main__":
    main()