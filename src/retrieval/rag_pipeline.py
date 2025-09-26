#!/usr/bin/env python3
"""
RAG Pipeline - Retrieval-Augmented Generation sistemi
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import yaml
from loguru import logger
from openai import OpenAI

# Local imports
sys.path.append('src')
from database.chroma_manager import ChromaManager

class RAGPipeline:
    """RAG Pipeline ana sınıfı"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Başlatma"""
        self.config = self._load_config(config_path)
        self.chroma_manager = ChromaManager(config_path)
        self.llm_client = None
        
        # LLM client'ı başlat
        self._initialize_llm()
        
        logger.info("RAG Pipeline başlatıldı")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Konfigürasyon yükle"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Config yüklenemedi: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Varsayılan config"""
        return {
            'llm': {
                'provider': 'huggingface',
                'base_url': 'https://router.huggingface.co/v1',
                'model': 'openai/gpt-oss-120b:novita',
                'temperature': 0.1,
                'max_tokens': 1000
            },
            'retrieval': {
                'top_k': 5,
                'similarity_threshold': 0.7
            }
        }
    
    def _initialize_llm(self):
        """LLM client'ı başlat"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # HuggingFace Router için OpenAI compatible client
            self.llm_client = OpenAI(
                base_url=os.getenv("BASE_URL", self.config['llm']['base_url']),
                api_key=os.getenv("API_KEY", "dummy_key")
            )
            
            logger.info(f"LLM client başlatıldı: {self.config['llm']['model']}")
            
        except Exception as e:
            logger.error(f"LLM başlatma hatası: {e}")
            raise
    
    def query(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Ana RAG sorgu fonksiyonu"""
        try:
            logger.info(f"🔍 Sorgu: {question}")
            
            # 1. Retrieval - İlgili belgeleri bul
            relevant_docs = self.chroma_manager.search(
                question, 
                n_results=self.config['retrieval']['top_k']
            )
            
            if not relevant_docs:
                return {
                    'answer': 'Üzgünüm, sorunuzla ilgili belge bulamadım. Lütfen daha spesifik bir soru sormayı deneyin.',
                    'sources': [],
                    'confidence': 0.0,
                    'query': question,
                    'timestamp': datetime.now().isoformat()
                }
            
            # 2. Context hazırla
            context = self._prepare_context(relevant_docs)
            
            # 3. Prompt oluştur
            prompt = self._create_prompt(question, context, chat_history)
            
            # 4. LLM'den cevap al
            llm_response = self._get_llm_response(prompt)
            
            # 5. Sonucu formatla
            result = {
                'answer': llm_response,
                'sources': self._format_sources(relevant_docs),
                'confidence': self._calculate_confidence(relevant_docs),
                'query': question,
                'timestamp': datetime.now().isoformat(),
                'retrieved_docs_count': len(relevant_docs)
            }
            
            logger.success(f"✅ Sorgu tamamlandı: {len(llm_response)} karakter cevap")
            return result
            
        except Exception as e:
            logger.error(f"RAG sorgu hatası: {e}")
            return {
                'answer': f'Üzgünüm, sorunuzu işlerken bir hata oluştu: {str(e)}',
                'sources': [],
                'confidence': 0.0,
                'query': question,
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_context(self, relevant_docs: List[Dict]) -> str:
        """Context metni hazırla"""
        context_parts = []
        
        for i, doc in enumerate(relevant_docs):
            # Similarity threshold kontrolü
            similarity = doc.get('similarity', 0)
            threshold = self.config['retrieval']['similarity_threshold']
            
            if similarity < threshold:
                continue
            
            # Context formatı
            source_info = f"[Kaynak {i+1}: {doc['metadata']['filename']}]"
            content = doc['content'].strip()
            
            context_parts.append(f"{source_info}\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str, chat_history: Optional[List[Dict]] = None) -> str:
        """LLM için prompt oluştur"""
        
        # Sistem mesajı
        system_prompt = """Sen uzman bir Türk hukuk asistanısın. Görevin:

1. Verilen hukuki belgelerden yararlanarak kullanıcının sorularını yanıtlamak
2. Sadece verilen belgeler temelinde cevap vermek
3. Yanıtlarını net, anlaşılır ve hukuki açıdan doğru şekilde sunmak
4. Eğer belgeler yetersizse bunu belirtmek
5. Kaynak referanslarını göstermek

KURALLARIN:
- Sadece verilen belgelerdeki bilgileri kullan
- Spekülasyon yapma
- Belirsizlik durumunda "Bu konuda verilen belgelerde yeterli bilgi bulunmuyor" de
- Türkçe dilbilgisi kurallarına uygun yanıt ver
- Hukuki terimler kullanırken açıklama yap"""

        # Chat history varsa ekle
        history_context = ""
        if chat_history:
            history_parts = []
            for msg in chat_history[-3:]:  # Son 3 mesaj
                role = "Kullanıcı" if msg.get('role') == 'user' else "Asistan"
                content = msg.get('content', '')
                history_parts.append(f"{role}: {content}")
            
            if history_parts:
                history_context = f"\nÖnceki konuşma:\n" + "\n".join(history_parts) + "\n"
        
        # Ana prompt
        user_prompt = f"""Hukuki belgeler:
{context}

{history_context}
Kullanıcı sorusu: {question}

Lütfen bu soruyu sadece verilen hukuki belgelere dayanarak yanıtla. Kaynak referanslarını da belirt."""

        return system_prompt + "\n\n" + user_prompt
    
    def _get_llm_response(self, prompt: str) -> str:
        """LLM'den cevap al"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.config['llm']['model'],
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config['llm']['temperature'],
                max_tokens=self.config['llm']['max_tokens']
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM response hatası: {e}")
            
            # Fallback: Alternatif model dene
            try:
                alt_model = self.config['llm'].get('alternative_model')
                if alt_model:
                    response = self.llm_client.chat.completions.create(
                        model=alt_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.config['llm']['temperature'],
                        max_tokens=self.config['llm']['max_tokens']
                    )
                    return response.choices[0].message.content.strip()
            except:
                pass
            
            return "LLM yanıt vermedi. Lütfen daha sonra tekrar deneyin."
    
    def _format_sources(self, relevant_docs: List[Dict]) -> List[Dict]:
        """Kaynak bilgilerini formatla"""
        sources = []
        
        for doc in relevant_docs:
            similarity = doc.get('similarity', 0)
            threshold = self.config['retrieval']['similarity_threshold']
            
            if similarity < threshold:
                continue
            
            source = {
                'filename': doc['metadata']['filename'],
                'similarity': f"{similarity:.2f}",
                'chunk_index': doc['metadata'].get('chunk_index', 0),
                'preview': doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
            }
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, relevant_docs: List[Dict]) -> float:
        """Cevap güven skorunu hesapla"""
        if not relevant_docs:
            return 0.0
        
        # En iyi similarity skorunu al
        best_similarity = max(doc.get('similarity', 0) for doc in relevant_docs)
        
        # Threshold üzerindeki doc sayısı
        threshold = self.config['retrieval']['similarity_threshold']
        good_docs = sum(1 for doc in relevant_docs if doc.get('similarity', 0) >= threshold)
        
        # Confidence skoru hesapla (0-1 arası)
        base_confidence = min(best_similarity, 1.0)
        doc_bonus = min(good_docs * 0.1, 0.3)  # Max 0.3 bonus
        confidence = min(base_confidence + doc_bonus, 1.0)
        
        return round(confidence, 2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Pipeline istatistikleri"""
        chroma_stats = self.chroma_manager.get_stats()
        
        return {
            **chroma_stats,
            'llm_model': self.config['llm']['model'],
            'retrieval_top_k': self.config['retrieval']['top_k'],
            'similarity_threshold': self.config['retrieval']['similarity_threshold']
        }


# Test fonksiyonu
def test_rag_pipeline():
    """RAG Pipeline test fonksiyonu"""
    print("🧪 RAG Pipeline Testi Başlıyor...")
    
    try:
        # Pipeline oluştur
        rag = RAGPipeline()
        
        # Test soruları
        test_questions = [
            "Türk Ceza Kanunu'nun amacı nedir?",
            "Medeni Kanun'da hakim nasıl karar verir?",
            "İcra takibi nasıl başlar?",
            "Ödeme emrine itiraz edilebilir mi?",
            "Bu kanunlar ne zaman yürürlüğe girdi?"
        ]
        
        print(f"📊 Pipeline istatistikleri:")
        stats = rag.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\n🔍 {len(test_questions)} test sorusu çalıştırılıyor...")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Test {i} ---")
            print(f"❓ Soru: {question}")
            
            result = rag.query(question)
            
            print(f"✅ Cevap ({result['confidence']} güven): {result['answer'][:200]}...")
            print(f"📚 {len(result['sources'])} kaynak kullanıldı")
            
            if result['sources']:
                print(f"📄 Ana kaynak: {result['sources'][0]['filename']}")
        
        print("\n✅ RAG Pipeline testi başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ RAG Pipeline test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_rag_pipeline()