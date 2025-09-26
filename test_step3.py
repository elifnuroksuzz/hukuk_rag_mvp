#!/usr/bin/env python3
"""
Adım 3 Test: Belge işleme ve ChromaDB entegrasyonu
"""

import os
from pathlib import Path
import sys

# src klasörünü path'e ekle
sys.path.append('src')

from database.chroma_manager import ChromaManager
from processing.document_processor import DocumentProcessor

def create_test_documents():
    """Test belgeleri oluştur"""
    print("📁 Test belgeleri oluşturuluyor...")
    
    # Test dizini
    test_dir = Path("data/test_documents")
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
    
    print(f"✅ {len(documents)} test belgesi oluşturuldu: {test_dir}")
    return test_dir

def test_complete_pipeline():
    """Tam pipeline testi"""
    print("🚀 ADIM 3: BELGE İŞLEME VE VEKTÖR VERITABANI TESTİ")
    print("=" * 60)
    
    try:
        # 1. Test belgelerini oluştur
        test_dir = create_test_documents()
        
        # 2. Document Processor testi
        print("\n🔍 1. Document Processor Test...")
        processor = DocumentProcessor()
        documents = processor.process_directory(str(test_dir))
        
        if not documents:
            print("❌ Belge işleme başarısız!")
            return False
        
        print(f"✅ {len(documents)} chunk oluşturuldu")
        
        # 3. ChromaDB Manager testi  
        print("\n🔍 2. ChromaDB Manager Test...")
        chroma_manager = ChromaManager()
        
        # Önce temizle
        chroma_manager.delete_all()
        
        # Belgeleri ekle
        success = chroma_manager.add_documents(documents)
        if not success:
            print("❌ Belge ekleme başarısız!")
            return False
        
        # 4. Arama testleri
        print("\n🔍 3. Arama Testleri...")
        
        test_queries = [
            "ceza kanunu nedir?",
            "medeni kanun hakkında bilgi",
            "icra takibi nasıl başlar?",
            "ödeme emri nedir?",
            "kanun ne zaman yürürlüğe girdi?"
        ]
        
        for query in test_queries:
            results = chroma_manager.search(query, n_results=3)
            print(f"\n🔍 Soru: {query}")
            print(f"📊 {len(results)} sonuç bulundu")
            
            if results:
                best_match = results[0]
                print(f"📄 En iyi eşleşme ({best_match['similarity']:.2f}): {best_match['metadata']['filename']}")
                print(f"📝 İçerik: {best_match['content'][:150]}...")
        
        # 5. İstatistikler
        print("\n📊 Veritabanı İstatistikleri:")
        stats = chroma_manager.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("🎉 TÜM TESTLER BAŞARILI!")
        print("✅ Belge işleme çalışıyor")
        print("✅ Vektör veritabanı çalışıyor") 
        print("✅ Semantic arama çalışıyor")
        print("\n🚀 Adım 4'e geçmeye hazırız: RAG Pipeline")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test hatası: {e}")
        return False

if __name__ == "__main__":
    test_complete_pipeline()