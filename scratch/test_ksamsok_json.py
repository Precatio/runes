import requests
import json

url = "https://kulturarvsdata.se/ksamsok/api"
params = {
    "method": "search",
    "hitsPerPage": "2",
    "query": 'text="runsten"'
}
headers = {'Accept': 'application/json'}
res = requests.get(url, params=params, headers=headers)
print("Status:", res.status_code)
if res.status_code == 200:
    data = res.json()
    with open("ksamsok_sample2.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Saved sample 2.")
else:
    print(res.text)
