#!/usr/bin/env python3
"""
Belge İşleyici - PDF, DOCX, TXT dosyalarını işler ve parçalara böler
"""

import os
import re
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Belge okuma kütüphaneleri
import PyPDF2
from docx import Document
import yaml
from loguru import logger

class DocumentProcessor:
    """Belge işleme sınıfı"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Başlatma"""
        self.config = self._load_config(config_path)
        self.supported_formats = self.config['document_processing']['supported_formats']
        self.chunk_size = self.config['embedding']['chunk_size']
        self.chunk_overlap = self.config['embedding']['chunk_overlap']
        
        logger.info(f"DocumentProcessor başlatıldı - Desteklenen formatlar: {self.supported_formats}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Konfigürasyon yükle"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Config yüklenemedi: {e}")
            # Varsayılan değerler
            return {
                'document_processing': {'supported_formats': ['.pdf', '.docx', '.txt']},
                'embedding': {'chunk_size': 1000, 'chunk_overlap': 200}
            }
    
    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Tek dosya işle"""
        try:
            file_path = Path(file_path)
            
            # Dosya kontrolü
            if not file_path.exists():
                logger.error(f"Dosya bulunamadı: {file_path}")
                return []
            
            # Format kontrolü
            if file_path.suffix.lower() not in self.supported_formats:
                logger.error(f"Desteklenmeyen format: {file_path.suffix}")
                return []
            
            # Dosya boyutu kontrolü (MB)
            file_size = file_path.stat().st_size
            max_size = self.config['document_processing'].get('max_file_size_mb', 50) * 1024 * 1024
            
            if file_size > max_size:
                logger.error(f"Dosya çok büyük: {file_size / 1024 / 1024:.1f}MB")
                return []
            
            # Metni çıkar
            text_content = self._extract_text(file_path)
            
            if not text_content.strip():
                logger.warning(f"Dosyada metin bulunamadı: {file_path.name}")
                return []
            
            # Temizle
            cleaned_text = self._clean_text(text_content)
            
            # Parçalara böl
            chunks = self._split_into_chunks(cleaned_text)
            
            # Belge objelerini oluştur
            documents = []
            for i, chunk in enumerate(chunks):
                doc = {
                    'content': chunk,
                    'filename': file_path.name,
                    'file_path': str(file_path),
                    'file_type': file_path.suffix.lower(),
                    'file_size': file_size,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'timestamp': datetime.now().isoformat(),
                    'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                documents.append(doc)
            
            logger.success(f"✅ Dosya işlendi: {file_path.name} ({len(chunks)} chunk)")
            return documents
            
        except Exception as e:
            logger.error(f"Dosya işleme hatası ({file_path}): {e}")
            return []
    
    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Dizindeki tüm dosyaları işle"""
        try:
            directory = Path(directory_path)
            
            if not directory.exists():
                logger.error(f"Dizin bulunamadı: {directory}")
                return []
            
            all_documents = []
            processed_files = 0
            
            # Tüm dosyaları tara
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    documents = self.process_file(str(file_path))
                    all_documents.extend(documents)
                    if documents:
                        processed_files += 1
            
            logger.success(f"✅ Dizin işlendi: {processed_files} dosya, {len(all_documents)} chunk")
            return all_documents
            
        except Exception as e:
            logger.error(f"Dizin işleme hatası: {e}")
            return []
    
    def _extract_text(self, file_path: Path) -> str:
        """Dosya türüne göre metin çıkar"""
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_path.suffix.lower() == '.docx':
                return self._extract_from_docx(file_path)
            elif file_path.suffix.lower() == '.txt':
                return self._extract_from_txt(file_path)
            else:
                logger.error(f"Desteklenmeyen format: {file_path.suffix}")
                return ""
                
        except Exception as e:
            logger.error(f"Metin çıkarma hatası ({file_path.name}): {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """PDF'den metin çıkar"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Sayfa {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"Sayfa {page_num + 1} okunamadı: {e}")
            
            return text
            
        except Exception as e:
            logger.error(f"PDF okuma hatası: {e}")
            return ""
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """DOCX'den metin çıkar"""
        try:
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"DOCX okuma hatası: {e}")
            return ""
    
    def _extract_from_txt(self, file_path: Path) -> str:
        """TXT dosyasını oku"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        except UnicodeDecodeError:
            # Türkçe karakter sorunu için alternatif encoding'ler dene
            for encoding in ['cp1254', 'iso-8859-9', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        logger.info(f"Dosya {encoding} ile okundu: {file_path.name}")
                        return file.read()
                except:
                    continue
            
            logger.error(f"Dosya encoding sorunu: {file_path.name}")
            return ""
            
        except Exception as e:
            logger.error(f"TXT okuma hatası: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Metni temizle"""
        # Çoklu boşlukları tek boşluğa çevir
        text = re.sub(r'\s+', ' ', text)
        
        # Satır başı ve sonundaki boşlukları temizle
        text = text.strip()
        
        # Çok kısa metinleri filtrele
        if len(text) < 10:
            return ""
        
        return text
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Metni parçalara böl"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Chunk sonunu bul
            end = start + self.chunk_size
            
            if end >= len(text):
                # Son chunk
                chunk = text[start:]
            else:
                # Kelime ortasında kesilmesin
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
                
                chunk = text[start:end]
            
            chunks.append(chunk.strip())
            
            # Overlap ile bir sonraki chunk'a geç
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]


# Test fonksiyonu
def test_document_processor():
    """DocumentProcessor test fonksiyonu"""
    print("🧪 DocumentProcessor Testi Başlıyor...")
    
    try:
        # Processor oluştur
        processor = DocumentProcessor()
        
        # Test dizini oluştur
        test_dir = Path("test_documents")
        test_dir.mkdir(exist_ok=True)
        
        # Test dosyası oluştur
        test_file = test_dir / "test_hukuk.txt"
        test_content = """
        Türk Ceza Kanunu
        Madde 1 - Amaç
        Bu Kanunun amacı, suç teşkil eden fiilleri ve bunlara uygulanacak cezaları göstermektir.
        
        Madde 2 - Zaman Bakımından Uygulama
        Suçun işlendiği zaman yürürlükte bulunan kanun uygulanır.
        
        Bu kanun, suçun işlendiği zaman yürürlükte bulunanı daha hafif ise, bu kanun uygulanır.
        """
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Dosyayı işle
        documents = processor.process_file(str(test_file))
        
        print(f"✅ Test dosyası işlendi: {len(documents)} chunk oluşturuldu")
        
        if documents:
            print(f"📄 İlk chunk: {documents[0]['content'][:100]}...")
            print(f"📊 Chunk boyutu: {len(documents[0]['content'])} karakter")
        
        # Test dizinini temizle
        test_file.unlink()
        test_dir.rmdir()
        
        print("✅ DocumentProcessor testi başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return False

if __name__ == "__main__":
    test_document_processor()