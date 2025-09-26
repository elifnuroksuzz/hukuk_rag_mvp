#!/usr/bin/env python3
"""
Hukuk RAG MVP - Streamlit Web Interface
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import yaml

# src klasörünü path'e ekle
sys.path.append('src')

from retrieval.rag_pipeline import RAGPipeline
from processing.document_processor import DocumentProcessor
from database.chroma_manager import ChromaManager

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Hukuk RAG Asistanı",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stil
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f4e79;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #ddd;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #ffffff;
    }
    .source-box {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #007bff;
        margin-top: 0.5rem;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_rag_pipeline():
    """RAG Pipeline'ı başlat (cache ile)"""
    try:
        return RAGPipeline()
    except Exception as e:
        st.error(f"RAG Pipeline başlatılırken hata: {e}")
        return None

@st.cache_resource
def initialize_processors():
    """Processor'ları başlat"""
    try:
        doc_processor = DocumentProcessor()
        chroma_manager = ChromaManager()
        return doc_processor, chroma_manager
    except Exception as e:
        st.error(f"Processor başlatılırken hata: {e}")
        return None, None

def format_confidence(confidence):
    """Confidence skorunu formatla"""
    if confidence >= 0.7:
        return f'<span class="confidence-high">Yüksek ({confidence})</span>'
    elif confidence >= 0.5:
        return f'<span class="confidence-medium">Orta ({confidence})</span>'
    else:
        return f'<span class="confidence-low">Düşük ({confidence})</span>'

def display_sources(sources):
    """Kaynakları göster"""
    if not sources:
        return
    
    st.markdown("### 📚 Kaynaklar")
    for i, source in enumerate(sources, 1):
        filename = source['filename']
        similarity = source['similarity']
        preview = source['preview']
        
        with st.expander(f"📄 Kaynak {i}: {filename} (Benzerlik: {similarity})"):
            st.markdown(f"**Dosya:** {filename}")
            st.markdown(f"**Benzerlik Skoru:** {similarity}")
            st.markdown(f"**İçerik Önizleme:**")
            st.text(preview)

def main():
    """Ana uygulama"""
    
    # Header
    st.markdown('<div class="main-header">⚖️ Hukuk RAG Asistanı</div>', unsafe_allow_html=True)
    st.markdown("*Türk hukuk belgelerinizi analiz eden yapay zeka asistanı*")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Kontrol Paneli")
        
        # Pipeline durumu
        rag = initialize_rag_pipeline()
        doc_processor, chroma_manager = initialize_processors()
        
        if rag and chroma_manager:
            stats = rag.get_stats()
            st.success("✅ Sistem Aktif")
            
            st.markdown("### 📊 Sistem Bilgileri")
            st.metric("Toplam Belge", stats.get('total_documents', 0))
            st.metric("LLM Model", stats.get('llm_model', 'Unknown')[:20] + "...")
            st.metric("Embedding Model", "Multilingual-MiniLM")
            
        else:
            st.error("❌ Sistem Başlatılamadı")
            st.stop()
        
        st.divider()
        
        # Belge yükleme bölümü
        st.header("📂 Belge Yönetimi")
        
        uploaded_files = st.file_uploader(
            "Hukuk belgelerinizi yükleyin",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("📥 Belgeleri İşle"):
                with st.spinner("Belgeler işleniyor..."):
                    success_count = 0
                    
                    for uploaded_file in uploaded_files:
                        try:
                            # Geçici dosya oluştur
                            temp_dir = Path("temp_uploads")
                            temp_dir.mkdir(exist_ok=True)
                            
                            temp_file = temp_dir / uploaded_file.name
                            with open(temp_file, 'wb') as f:
                                f.write(uploaded_file.getvalue())
                            
                            # Dosyayı işle
                            documents = doc_processor.process_file(str(temp_file))
                            
                            if documents:
                                # Vektör veritabanına ekle
                                if chroma_manager.add_documents(documents):
                                    success_count += 1
                            
                            # Temp dosyayı sil
                            temp_file.unlink()
                            
                        except Exception as e:
                            st.error(f"Dosya işleme hatası ({uploaded_file.name}): {e}")
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count} dosya başarıyla eklendi!")
                        st.rerun()
                    else:
                        st.error("❌ Hiçbir dosya işlenemedi")
        
        # Veritabanı temizleme
        if st.button("🗑️ Veritabanını Temizle", type="secondary"):
            if st.confirm("Tüm belgeler silinecek. Emin misiniz?"):
                if chroma_manager.delete_all():
                    st.success("✅ Veritabanı temizlendi")
                    st.rerun()
    
    # Ana içerik alanı
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Sohbet")
        
        # Chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Mesajları göster
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Kaynak bilgilerini göster
                if message["role"] == "assistant" and "sources" in message:
                    display_sources(message["sources"])
        
        # Kullanıcı input
        if prompt := st.chat_input("Hukuki sorunuzu sorun..."):
            # Kullanıcı mesajını ekle
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # RAG sorgusu
            with st.chat_message("assistant"):
                with st.spinner("Cevap hazırlanıyor..."):
                    try:
                        # Chat history hazırla
                        chat_history = st.session_state.messages[-10:]  # Son 10 mesaj
                        
                        # RAG sorgusu
                        result = rag.query(prompt, chat_history)
                        
                        # Cevabı göster
                        st.markdown(result['answer'])
                        
                        # Confidence score
                        confidence_html = format_confidence(result['confidence'])
                        st.markdown(f"**Güven Skoru:** {confidence_html}", unsafe_allow_html=True)
                        
                        # Kaynakları göster
                        if result['sources']:
                            display_sources(result['sources'])
                        
                        # Session state'e ekle
                        assistant_message = {
                            "role": "assistant", 
                            "content": result['answer'],
                            "sources": result['sources'],
                            "confidence": result['confidence']
                        }
                        st.session_state.messages.append(assistant_message)
                        
                    except Exception as e:
                        error_msg = f"Üzgünüm, bir hata oluştu: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    with col2:
        st.header("🎯 Hızlı Sorular")
        
        # Önceden tanımlı sorular
        quick_questions = [
            "Türk Ceza Kanunu'nun amacı nedir?",
            "Hakim kanunda hüküm bulamazsa ne yapar?",
            "İcra takibi nasıl başlar?",
            "Ödeme emrine itiraz edilebilir mi?",
            "Bu kanunlar ne zaman yürürlüğe girdi?"
        ]
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{hash(question)}"):
                # Soruyu chat'e ekle
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()
        
        st.divider()
        
        # Sistem durumu
        st.header("📈 Performans")
        
        if st.session_state.messages:
            total_questions = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
            avg_confidence = sum([msg.get("confidence", 0) for msg in st.session_state.messages if msg["role"] == "assistant"]) / max(len([msg for msg in st.session_state.messages if msg["role"] == "assistant"]), 1)
            
            st.metric("Toplam Soru", total_questions)
            st.metric("Ortalama Güven", f"{avg_confidence:.2f}")
        else:
            st.info("Henüz soru sorulmadı")
        
        # Clear chat
        if st.button("🗑️ Sohbeti Temizle"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()