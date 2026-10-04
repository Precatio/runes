import requests
import urllib.parse
import xml.etree.ElementTree as ET

# Bounding box around Stockholm
lon_min, lat_min, lon_max, lat_max = 17.8, 59.2, 18.2, 59.4
cql = f'itemType="runinskrift" AND boundingBox=/WGS84_Decimal/"{lon_min} {lat_min} {lon_max} {lat_max}"'

url = f"https://kulturarvsdata.se/ksamsok/api?method=search&hitsPerPage=50&query={urllib.parse.quote(cql)}"
headers = {'Accept': 'application/json'}
res = requests.get(url, headers=headers)

if res.status_code == 200:
    print(res.json())
else:
    print("Failed", res.status_code, res.text)
