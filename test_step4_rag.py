#!/usr/bin/env python3
"""
Adım 4 Test: RAG Pipeline - Tam entegrasyon testi
"""

import os
import sys
from pathlib import Path

# src klasörünü path'e ekle
sys.path.append('src')

from retrieval.rag_pipeline import RAGPipeline
from processing.document_processor import DocumentProcessor
from database.chroma_manager import ChromaManager

def ensure_test_data():
    """Test verilerinin olduğundan emin ol"""
    test_dir = Path("data/test_documents")
    
    if not test_dir.exists() or len(list(test_dir.glob("*.txt"))) < 3:
        print("📁 Test verileri oluşturuluyor...")
        
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Test belgeleri
        documents = {
            "tck_madde1.txt": """
Türk Ceza Kanunu - Madde 1 (Amaç)

Bu Kanunun amacı, suç teşkil eden fiilleri ve bunlara uygulanacak cezaları göstermektir.

Kanunda suç sayılan fiiller dışında hiçbir fiil, suç sayılamaz ve bunlar hakkında ceza verilemez.

Bu kanun 1 Haziran 2005 tarihinde yürürlüğe girmiştir.
            """,
            
            "tmk_madde1.txt": """
Türk Medeni Kanunu - Madde 1 (Kanunun uygulanması)

Kanun, lafzı veya ruhu ile bir hükme bağlamış olduğu hallerde hâkim bu hükmü uygulamakla yükümlüdür.

Kanunda uygulanabilir bir hüküm bulunmayan hallerde hâkim, örf ve âdet hukukuna göre, 
bunlar da yoksa kendisinin kanun koyucu olsaydı vaz'edeceği kurala göre karar verir.

Bu kanun 1 Ocak 2002 tarihinde yürürlüğe girmiştir.
            """,
            
            "icra_iflas_kanunu.txt": """
İcra ve İflas Kanunu - Temel Hükümler

Madde 1: Bu kanun, alacaklıların alacaklarını elde etmeleri için takip edilecek usulleri düzenler.

Madde 2: İcra takibi, ödeme emri ile başlar. Ödeme emri, alacaklının talebi üzerine icra müdürü tarafından düzenlenir.

Madde 3: Borçlu, ödeme emrine karşı yedi gün içinde itiraz edebilir. İtiraz halinde alacaklının mahkemeye başvurması gerekir.

Bu kanunun amacı, adil ve hızlı bir icra sistemi kurmaktır.
            """
        }
        
        # Dosyaları oluştur
        for filename, content in documents.items():
            file_path = test_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
        
        # Vektör veritabanına yükle
        processor = DocumentProcessor()
        chroma_manager = ChromaManager()
        
        documents = processor.process_directory(str(test_dir))
        chroma_manager.delete_all()
        chroma_manager.add_documents(documents)
        
        print(f"✅ {len(documents)} test belgesi hazırlandı")
    
    return test_dir

def test_rag_complete():
    """Tam RAG sistem testi"""
    print("🚀 ADIM 4: RAG PIPELINE TAM TEST")
    print("=" * 50)
    
    try:
        # 1. Test verilerini hazırla
        test_dir = ensure_test_data()
        
        # 2. RAG Pipeline oluştur
        print("\n🔧 RAG Pipeline başlatılıyor...")
        rag = RAGPipeline()
        
        # 3. Pipeline istatistikleri
        print("\n📊 Sistem Durumu:")
        stats = rag.get_stats()
        for key, value in stats.items():
            print(f"  📋 {key}: {value}")
        
        # 4. Detaylı test soruları
        print("\n🧪 Detaylı Test Soruları:")
        
        test_cases = [
            {
                "question": "Türk Ceza Kanunu'nun amacı nedir?",
                "expected_keywords": ["suç", "ceza", "fiil"],
                "expected_source": "tck_madde1.txt"
            },
            {
                "question": "Hakim kanunda hüküm bulamazsa ne yapar?",
                "expected_keywords": ["örf", "âdet", "kanun koyucu"],
                "expected_source": "tmk_madde1.txt"
            },
            {
                "question": "İcra takibi nasıl başlar ve borçlu ne yapabilir?",
                "expected_keywords": ["ödeme emri", "itiraz", "yedi gün"],
                "expected_source": "icra_iflas_kanunu.txt"
            },
            {
                "question": "Bu kanunlar hangi tarihlerde yürürlüğe girdi?",
                "expected_keywords": ["2005", "2002", "yürürlüğe"],
                "expected_source": None  # Çoklu kaynak
            },
            {
                "question": "Miras hukuku hakkında ne biliyorsun?",
                "expected_keywords": [],  # Bu soruya cevap veremeyecek
                "expected_source": None
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            question = test_case["question"]
            expected_keywords = test_case["expected_keywords"]
            expected_source = test_case["expected_source"]
            
            print(f"\n--- Test {i} ---")
            print(f"❓ Soru: {question}")
            
            # RAG sorgusu
            result = rag.query(question)
            
            answer = result['answer']
            sources = result['sources']
            confidence = result['confidence']
            
            print(f"🤖 Cevap: {answer[:300]}{'...' if len(answer) > 300 else ''}")
            print(f"📊 Güven Skoru: {confidence}")
            print(f"📚 Kaynak Sayısı: {len(sources)}")
            
            # Test değerlendirmesi
            test_passed = True
            
            # Keyword kontrolü
            if expected_keywords:
                found_keywords = sum(1 for keyword in expected_keywords 
                                   if keyword.lower() in answer.lower())
                keyword_ratio = found_keywords / len(expected_keywords)
                print(f"🔍 Anahtar kelime eşleşmesi: {found_keywords}/{len(expected_keywords)} ({keyword_ratio:.1%})")
                
                if keyword_ratio < 0.5:
                    print("⚠️  Düşük anahtar kelime eşleşmesi")
                    test_passed = False
            
            # Kaynak kontrolü
            if expected_source and sources:
                source_found = any(expected_source in source['filename'] for source in sources)
                if source_found:
                    print(f"✅ Doğru kaynak bulundu: {expected_source}")
                else:
                    print(f"❌ Beklenen kaynak bulunamadı: {expected_source}")
                    print(f"📄 Bulunan kaynaklar: {[s['filename'] for s in sources]}")
                    test_passed = False
            
            # Güven skoru kontrolü
            if confidence > 0.5:
                print(f"✅ Yeterli güven skoru: {confidence}")
            else:
                print(f"⚠️  Düşük güven skoru: {confidence}")
                if expected_keywords:  # Cevabı olması beklenen sorular için
                    test_passed = False
            
            if test_passed:
                success_count += 1
                print("✅ TEST GEÇTİ")
            else:
                print("❌ TEST BAŞARISIZ")
        
        # 5. Sohbet geçmişi testi
        print(f"\n🗣️  Sohbet Geçmişi Testi:")
        
        chat_history = [
            {"role": "user", "content": "Ceza kanunu nedir?"},
            {"role": "assistant", "content": "Türk Ceza Kanunu, suç teşkil eden fiilleri ve bunlara uygulanacak cezaları gösteren kanundur."}
        ]
        
        follow_up = rag.query("Bu kanun ne zaman yürürlüğe girdi?", chat_history)
        print(f"🤖 Takip sorusu cevabı: {follow_up['answer'][:200]}...")
        
        # 6. Sonuç raporu
        print(f"\n" + "=" * 50)
        print(f"📊 TEST SONUÇLARI:")
        print(f"  ✅ Başarılı: {success_count}/{len(test_cases)}")
        print(f"  📊 Başarı oranı: {success_count/len(test_cases)*100:.1f}%")
        
        if success_count >= len(test_cases) * 0.8:  # %80 başarı oranı
            print(f"\n🎉 RAG PİPELİNE BAŞARILI!")
            print(f"✅ Belge arama çalışıyor")
            print(f"✅ LLM entegrasyonu çalışıyor")
            print(f"✅ Kaynak referanslama çalışıyor")
            print(f"✅ Güven skoru hesaplama çalışıyor")
            print(f"\n🚀 Adım 5'e hazırız: Web Interface!")
            return True
        else:
            print(f"\n⚠️  RAG Pipeline bazı testlerde sorunlu")
            print(f"🔧 İyileştirme gerekebilir")
            return False
        
    except Exception as e:
        print(f"❌ RAG test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_rag_complete()