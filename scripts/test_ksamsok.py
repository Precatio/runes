import requests

def search(signum):
    url = "http://kulturarvsdata.se/ksamsok/api"
    params = {
        "method": "search",
        "query": f'text="{signum}"',
        "hitsPerPage": 20
    }
    response = requests.get(url, params=params, headers={"Accept": "application/json"})
    data = response.json()
    
    descriptions = []
    
    for record in data.get("result", {}).get("records", []):
        graph = record.get("record", {}).get("@graph", [])
        for node in graph:
            if "ksam:desc" in node:
                desc = node["ksam:desc"]
                if isinstance(desc, dict):
                    descriptions.append(desc.get("@value", ""))
                elif isinstance(desc, list):
                    for d in desc:
                        if isinstance(d, dict):
                            descriptions.append(d.get("@value", ""))
                        else:
                            descriptions.append(str(d))
                else:
                    descriptions.append(str(desc))
                    
    print(f"Found {len(descriptions)} descriptions.")
    for i, d in enumerate(descriptions[:5]):
        print(f"{i+1}: {d}")
        print("---")

search("Sö 112")
