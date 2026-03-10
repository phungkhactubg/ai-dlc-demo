import argparse
import json
import urllib.request
import urllib.parse
from datetime import datetime

# --- HuggingFace API ---
def search_huggingface_models(query, limit=5, sort="downloads"):
    """
    Search Hugging Face Hub for models.
    """
    base_url = "https://huggingface.co/api/models"
    params = {
        "search": query,
        "limit": limit,
        "sort": sort,
        "direction": "-1" # Descending
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    print(f"[*] Searching HuggingFace for: '{query}'...")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        print(f"\n--- Found {len(data)} Models ---")
        for model in data:
            model_id = model.get('modelId')
            likes = model.get('likes', 0)
            downloads = model.get('downloads', 0)
            print(f"- {model_id} (Likes: {likes}, Downloads: {downloads})")
            print(f"  URL: https://huggingface.co/{model_id}")
            
    except Exception as e:
        print(f"[!] Error searching HuggingFace: {e}")

# --- ArXiv API ---
def search_arxiv_papers(query, limit=5):
    """
    Search ArXiv for papers (using standard API).
    """
    base_url = "http://export.arxiv.org/api/query"
    # Simple query construction
    search_query = f"all:{query}"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": limit,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    print(f"\n[*] Searching ArXiv for: '{query}'...")
    try:
        with urllib.request.urlopen(url) as response:
            # ArXiv returns Atom XML. For simplicity in this script, we'll just print raw text or use a simple regex if really needed.
            # But let's just dump the titles if we can parsing simple XML string.
            xml_data = response.read().decode()
            
            # Simple manual parsing to avoid external dependencies like BeautifulSoup
            entries = xml_data.split('<entry>')
            print(f"\n--- Found {len(entries)-1} Papers ---")
            
            for i, entry in enumerate(entries[1:]): # Skip header
                title_start = entry.find('<title>') + 7
                title_end = entry.find('</title>')
                title = entry[title_start:title_end].strip().replace('\n', ' ')
                
                id_start = entry.find('<id>') + 4
                id_end = entry.find('</id>')
                link = entry[id_start:id_end].strip()
                
                print(f"{i+1}. {title}")
                print(f"   Link: {link}")
                
    except Exception as e:
        print(f"[!] Error searching ArXiv: {e}")

def main():
    parser = argparse.ArgumentParser(description="AI Research Tool: Search Models & Papers")
    parser.add_argument("query", help="Search term (e.g. 'text-to-speech', 'transformer')")
    parser.add_argument("--type", choices=['all', 'model', 'paper'], default='all', help="Type of research")
    parser.add_argument("--limit", type=int, default=5, help="Result limit")
    
    args = parser.parse_args()
    
    if args.type in ['all', 'model']:
        search_huggingface_models(args.query, args.limit)
    
    if args.type in ['all', 'paper']:
        search_arxiv_papers(args.query, args.limit)

if __name__ == "__main__":
    main()
