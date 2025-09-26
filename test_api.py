#!/usr/bin/env python3
"""
Hukuk RAG API Test Client
"""

import requests
import json
from pathlib import Path
import time

# API base URL
BASE_URL = "http://localhost:8000"

class HukukRAGClient:
    """API Test Client"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Health check"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def get_stats(self):
        """Get system stats"""
        response = self.session.get(f"{self.base_url}/stats")
        return response.json()
    
    def query(self, question: str, chat_history=None, max_sources=5):
        """Query the RAG system"""
        payload = {
            "question": question,
            "chat_history": chat_history,
            "max_sources": max_sources
        }
        
        response = self.session.post(
            f"{self.base_url}/query",
            json=payload
        )
        
        return response.json()
    
    def upload_file(self, file_path: str):
        """Upload a single file"""
        file_path = Path(file_path)
        
        with open(file_path, 'rb') as f:
            files = {'files': (file_path.name, f, 'application/octet-stream')}
            response = self.session.post(
                f"{self.base_url}/upload",
                files=files
            )
        
        return response.json()
    
    def search_documents(self, query: str, limit=5):
        """Search documents directly"""
        params = {
            "query": query,
            "limit": limit
        }
        
        response = self.session.get(
            f"{self.base_url}/documents/search",
            params=params
        )
        
        return response.json()
    
    def clear_documents(self):
        """Clear all documents"""
        response = self.session.delete(f"{self.base_url}/documents")
        return response.json()

def test_api():
    """Comprehensive API test"""
    print("🧪 HUKUK RAG API TEST")
    print("=" * 40)
    
    client = HukukRAGClient()
    
    # 1. Health Check
    print("\n1. Health Check...")
    try:
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Components: {len(health['components'])}")
        if health['status'] == 'healthy':
            print("   ✅ API is healthy")
        else:
            print("   ⚠️ API has issues")
            print(f"   Details: {health['components']}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    # 2. System Stats
    print("\n2. System Stats...")
    try:
        stats = client.get_stats()
        print(f"   Total Documents: {stats['total_documents']}")
        print(f"   LLM Model: {stats['llm_model']}")
        print(f"   Uptime: {stats['uptime']}")
        print("   ✅ Stats retrieved")
    except Exception as e:
        print(f"   ❌ Stats failed: {e}")
    
    # 3. Query Test (if documents exist)
    print("\n3. Query Test...")
    try:
        result = client.query("Türk Ceza Kanunu'nun amacı nedir?")
        
        print(f"   Question: {result['query']}")
        print(f"   Answer: {result['answer'][:100]}...")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Sources: {len(result['sources'])}")
        
        if result['confidence'] > 0.5:
            print("   ✅ Query successful")
        else:
            print("   ⚠️ Low confidence answer")
            
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    # 4. Document Search Test
    print("\n4. Document Search Test...")
    try:
        search_result = client.search_documents("ceza kanunu")
        
        print(f"   Query: {search_result['query']}")
        print(f"   Results: {search_result['count']}")
        
        if search_result['count'] > 0:
            print("   ✅ Search successful")
            
            # Show first result
            first_result = search_result['results'][0]
            print(f"   Best match: {first_result['metadata']['filename']}")
            print(f"   Similarity: {first_result['similarity']:.3f}")
        else:
            print("   ⚠️ No search results")
            
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
    
    # 5. Chat History Test
    print("\n5. Chat History Test...")
    try:
        chat_history = [
            {"role": "user", "content": "Ceza kanunu nedir?"},
            {"role": "assistant", "content": "Türk Ceza Kanunu, suç teşkil eden fiilleri düzenler."}
        ]
        
        result = client.query(
            "Bu kanun ne zaman yürürlüğe girdi?", 
            chat_history=chat_history
        )
        
        print(f"   Follow-up answer: {result['answer'][:100]}...")
        print(f"   Confidence: {result['confidence']}")
        print("   ✅ Chat history test successful")
        
    except Exception as e:
        print(f"   ❌ Chat history test failed: {e}")
    
    print(f"\n🎯 API Test completed!")

def interactive_test():
    """Interactive API testing"""
    print("🎮 INTERACTIVE API TEST")
    print("Commands: query, stats, search, health, quit")
    print("=" * 40)
    
    client = HukukRAGClient()
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit":
                break
                
            elif command == "health":
                health = client.health_check()
                print(json.dumps(health, indent=2))
                
            elif command == "stats":
                stats = client.get_stats()
                print(json.dumps(stats, indent=2))
                
            elif command.startswith("query"):
                if len(command) > 6:
                    question = command[6:].strip()
                else:
                    question = input("Question: ")
                
                result = client.query(question)
                print(f"\nAnswer: {result['answer']}")
                print(f"Confidence: {result['confidence']}")
                print(f"Sources: {len(result['sources'])}")
                
            elif command.startswith("search"):
                if len(command) > 7:
                    query = command[7:].strip()
                else:
                    query = input("Search query: ")
                
                result = client.search_documents(query)
                print(f"\nResults: {result['count']}")
                for i, doc in enumerate(result['results'][:3]):
                    print(f"{i+1}. {doc['metadata']['filename']} (sim: {doc['similarity']:.3f})")
                    
            else:
                print("Unknown command. Use: query, stats, search, health, quit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        test_api()