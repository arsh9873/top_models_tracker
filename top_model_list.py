
# uses some jina.ai webpage to actually scrape, and the thing being scraped is artificialanalysis.ai/leaderbord/models page
# if anything breaks its most likely art analysis changed the structure of their page or maybe jina stopped working


import requests
import re

def get_top_30_ai_models():
    target_url = "https://artificialanalysis.ai/leaderboards/models"
    jina_url = f"https://r.jina.ai/{target_url}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    print("📡 Fetching live leaderboard data...")
    try:
        response = requests.get(jina_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch data: {e}")
        return

    lines = response.text.split('\n')
    models_data = []
    
    target_providers = ['kimi', 'z ai', 'google', 'alibaba', 'minimax', 'deepseek', 'tencent']
    
    # 1. DYNAMIC COLUMN DETECTION
    # We look for the header row to find the exact index of "Model" and "Intelligence"
    model_idx = 1      # Default fallback
    intel_idx = 4      # Default fallback
    creator_idx = 3    # Default fallback
    
    for line in lines:
        if line.startswith('|') and 'intelligence' in line.lower() and 'model' in line.lower():
            cols = [c.strip().lower() for c in line.split('|')]
            for i, col in enumerate(cols):
                if 'model' in col and 'name' not in col: # Avoid matching "Model Providers" link text
                    model_idx = i
                if 'intelligence' in col:
                    intel_idx = i
                if 'creator' in col or 'provider' in col or 'company' in col:
                    creator_idx = i
            break # Header found, stop searching

    # 2. PARSE DATA ROWS
    for line in lines:
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            cols = [c.strip() for c in line.split('|')]
            
            # Ensure the row has enough columns to safely access our dynamic indices
            max_idx = max(model_idx, intel_idx, creator_idx)
            if len(cols) > max_idx:
                model_name = cols[model_idx]
                creator_raw = cols[creator_idx]
                intel_score_str = cols[intel_idx]
                
                # Clean markdown images
                model_name = re.sub(r'!\[.*?\]\(.*?\)', '', model_name).strip()
                creator_clean = re.sub(r'!\[.*?\]\(.*?\)', '', creator_raw).strip().lower()
                
                # STRICT CHECK: Does the Intelligence column contain ONLY a number (and optional asterisk)?
                if re.match(r'^\d+(\s*\*)?$', intel_score_str):
                    score = int(re.sub(r'\D', '', intel_score_str))
                    
                    if model_name and len(model_name) > 3 and not model_name.lower().startswith('model'):
                        is_target = any(provider in creator_clean for provider in target_providers)
                        models_data.append({
                            "name": model_name,
                            "score": score,
                            "is_target": is_target
                        })
    
    # Sort by score descending
    models_data.sort(key=lambda x: x["score"], reverse=True)
    
    # Deduplicate
    seen = set()
    unique_models = []
    for m in models_data:
        if m["name"] not in seen:
            seen.add(m["name"])
            unique_models.append(m)
    
    # 3. THE CIRCUIT BREAKER (Sanity Checks)
    if len(unique_models) < 10:
        print("\n⚠️ ERROR: Page structure may have changed drastically!")
        print("💡 Recommendation: The website layout was updated and the script could not find enough valid models.")
        print("💡 Action: Please re-evaluate the page structure manually or use an LLM to parse the new format.\n")
        return
        
    if unique_models[0]['score'] < 20:
        print("\n⚠️ ERROR: Sanity check failed!")
        print(f"💡 Recommendation: The top model detected is '{unique_models[0]['name']}' with a score of {unique_models[0]['score']}.")
        print("💡 Action: This is abnormally low. The column mapping is likely misaligned due to a website update. Rethink with LLM.\n")
        return

    # 4. SUCCESS: Print Top 30
    top_30 = unique_models[:30]
    
    print("\n🏆 Top 30 Models by Artificial Analysis Intelligence Index 🏆")
    print("⭐ = Highlighted Provider (Kimi, Z AI, Google, Alibaba, MiniMax, DeepSeek, Tencent)\n")
    print(f"{'Rank':<6} | {'Model Name':<55} | {'Score'}")
    print("-" * 85)
    
    for rank, model in enumerate(top_30, 1):
        name_display = f"⭐ {model['name']}" if model['is_target'] else f"   {model['name']}"
        if len(name_display) > 55:
            name_display = name_display[:52] + "..."
        print(f"#{rank:<4} | {name_display:<55} | {model['score']}")
        
    print("-" * 85 + "\n")

if __name__ == "__main__":
    get_top_30_ai_models()
