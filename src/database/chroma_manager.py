#!/usr/bin/env python3
"""
ChromaDB Yöneticisi - Vektör veritabanı işlemleri
"""

import os

import uuid
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import yaml
from loguru import logger

class ChromaManager:
    """ChromaDB vektör veritabanı yöneticisi"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Başlatma"""
        self.config = self._load_config(config_path)
        self.embedding_model = None
        self.client = None
        self.collection = None
        
        # Başlatma işlemleri
        self._initialize_client()
        self._initialize_embedding_model()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Konfigürasyon dosyasını yükle"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Config yüklenemedi: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Varsayılan konfigürasyon"""
        return {
            'vector_db': {
                'collection_name': 'hukuk_documents',
                'persist_directory': './data/chroma_db'
            },
            'embedding': {
                'model_name': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                'chunk_size': 1000,
                'chunk_overlap': 200
            },
            'retrieval': {
                'top_k': 5,
                'similarity_threshold': 0.7
            }
        }
    
    def _initialize_client(self):
        """ChromaDB client'ı başlat"""
        try:
            persist_dir = self.config['vector_db']['persist_directory']
            
            # Dizini oluştur
            os.makedirs(persist_dir, exist_ok=True)
            
            # Client oluştur
            self.client = chromadb.PersistentClient(path=persist_dir)
            
            # Koleksiyon oluştur veya getir
            collection_name = self.config['vector_db']['collection_name']
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Hukuk belgeleri için vektör veritabanı"}
            )
            
            logger.info(f"ChromaDB başlatıldı: {collection_name}")
            
        except Exception as e:
            logger.error(f"ChromaDB başlatma hatası: {e}")
            raise
    
    def _initialize_embedding_model(self):
        """Embedding modelini yükle"""
        try:
            model_name = self.config['embedding']['model_name']
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Embedding model yüklendi: {model_name}")
            
        except Exception as e:
            logger.error(f"Embedding model hatası: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Belgeleri vektör veritabanına ekle"""
        try:
            if not documents:
                logger.warning("Eklenecek belge yok")
                return False
            
            # Belge verilerini hazırla
            texts = []
            metadatas = []
            ids = []
            
            for doc in documents:
                # UUID oluştur
                doc_id = str(uuid.uuid4())
                
                # Metin içeriği
                content = doc.get('content', '')
                if not content:
                    continue
                
                # Metadata hazırla
                metadata = {
                    'filename': doc.get('filename', 'unknown'),
                    'file_type': doc.get('file_type', 'txt'),
                    'chunk_index': doc.get('chunk_index', 0),
                    'total_chunks': doc.get('total_chunks', 1),
                    'timestamp': doc.get('timestamp', ''),
                    'file_size': doc.get('file_size', 0)
                }
                
                texts.append(content)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            if not texts:
                logger.warning("İşlenebilir metin yok")
                return False
            
            # Embeddingleri oluştur
            logger.info(f"Embedding oluşturuluyor: {len(texts)} chunk")
            embeddings = self.embedding_model.encode(texts)
            
            # ChromaDB'ye ekle
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings.tolist()
            )
            
            logger.success(f"✅ {len(texts)} belge eklendi")
            return True
            
        except Exception as e:
            logger.error(f"Belge ekleme hatası: {e}")
            return False
    
    def search(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """Semantic arama yap"""
        try:
            if n_results is None:
                n_results = self.config['retrieval']['top_k']
            
            # Query embeddingini oluştur
            query_embedding = self.embedding_model.encode([query])
            
            # Arama yap
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Sonuçları formatla
            formatted_results = []
            for i in range(len(results['ids'][0])):
                distance = results['distances'][0][i]
                # ChromaDB distance'ı daha iyi similarity'ye çevir
                # Squared Euclidean distance'ı normalize et
                similarity = max(0, 1.0 - (distance / 20.0))  # 20 ile normalize et
                
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': distance,
                    'similarity': similarity
                }
                formatted_results.append(result)
            
            logger.info(f"🔍 Arama tamamlandı: {len(formatted_results)} sonuç")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Arama hatası: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Veritabanı istatistikleri"""
        try:
            count = self.collection.count()
            
            return {
                'total_documents': count,
                'collection_name': self.config['vector_db']['collection_name'],
                'embedding_model': self.config['embedding']['model_name']
            }
            
        except Exception as e:
            logger.error(f"İstatistik hatası: {e}")
            return {}
    
    def delete_all(self) -> bool:
        """Tüm belgeleri sil (dikkatli kullan!)"""
        try:
            # Koleksiyonu sil ve yeniden oluştur
            collection_name = self.config['vector_db']['collection_name']
            self.client.delete_collection(name=collection_name)
            
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Hukuk belgeleri için vektör veritabanı"}
            )
            
            logger.warning("⚠️ Tüm belgeler silindi!")
            return True
            
        except Exception as e:
            logger.error(f"Silme hatası: {e}")
            return False
    
    def close(self):
        """Bağlantıyı kapat"""
        logger.info("ChromaDB bağlantısı kapatıldı")


# Test fonksiyonu
def test_chroma_manager():
    """ChromaManager test fonksiyonu"""
    print("🧪 ChromaManager Testi Başlıyor...")
    
    try:
        # Manager oluştur
        manager = ChromaManager()
        
        # Test belgeleri
        test_docs = [
            {
                'content': 'Türk Ceza Kanunu madde 1: Bu Kanunun amacı, suç teşkil eden fiilleri ve bunlara uygulanacak cezaları göstermektir.',
                'filename': 'tck_madde1.txt',
                'file_type': 'txt',
                'chunk_index': 0,
                'total_chunks': 1
            },
            {
                'content': 'Türk Medeni Kanunu madde 1: Kanun, lafzı veya ruhu ile bir hükme bağlamış olduğu hallerde hakim bu hükmü uygulamak zorundadır.',
                'filename': 'tmk_madde1.txt',
                'file_type': 'txt',
                'chunk_index': 0,
                'total_chunks': 1
            }
        ]
        
        # Belgeleri ekle
        success = manager.add_documents(test_docs)
        if success:
            print("✅ Test belgeleri eklendi")
        
        # Arama testi
        results = manager.search("ceza kanunu nedir?")
        print(f"🔍 Arama sonucu: {len(results)} belge bulundu")
        
        if results:
            print(f"📄 En iyi eşleşme: {results[0]['content'][:100]}...")
            print(f"📊 Benzerlik skoru: {results[0]['similarity']:.2f}")
        
        # İstatistikler
        stats = manager.get_stats()
        print(f"📊 Toplam belge: {stats.get('total_documents', 0)}")
        
        print("✅ ChromaManager testi başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False

if __name__ == "__main__":
    test_chroma_manager()