import requests
import urllib.parse
import xml.etree.ElementTree as ET

def test_ksamsok_bbox(lat, lon):
    url = "https://kulturarvsdata.se/ksamsok/api"
    # K-samsök bbox: lonMin latMin lonMax latMax
    bbox = f"{lon-0.1} {lat-0.1} {lon+0.1} {lat+0.1}"
    cql = f'itemType="Fornlämning" AND text="runristning" AND boundingBox=/WGS84_BoundingBox/"{bbox}"'
    params = {
        "method": "search",
        "hitsPerPage": "10",
        "query": cql
    }
    # No headers, default is XML
    res = requests.get(url, params=params)
    print("Status:", res.status_code)
    if res.status_code == 200:
        root = ET.fromstring(res.content)
        # Find coordinates
        namespaces = {
            'gml': 'http://www.opengis.net/gml',
            'pres': 'http://kulturarvsdata.se/presentation#'
        }
        hits = root.findall('.//pres:item', namespaces)
        print(f"Found {len(hits)} hits")
        for item in hits:
            name = item.findtext('.//pres:itemLabel', namespaces=namespaces)
            coords = item.findtext('.//gml:coordinates', namespaces=namespaces)
            print(f"{name}: {coords}")

test_ksamsok_bbox(59.8586, 17.6389) # Uppsala
