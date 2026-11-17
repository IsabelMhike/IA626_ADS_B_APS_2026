import requests, json
from jsonschema import validate


url = 'http://127.0.0.1:5000/getData?key=1234&start=2022-11-23%2005:28:10&end=2022-11-23%2005:28:15'
r =requests.get(url)
resp = json.loads(r.text)
print(resp['msg'])


n=0
while n < 1:
    url = 'http://127.0.0.1:5000/getData?key=123&start=2022-11-23%2005:28:10&end=2022-11-23%2005:28:15'
    r =requests.get(url)
    resp = json.loads(r.text)
    print(resp['msg'])
    validate(instance=resp, schema=json.load(open("schemas.json"))["properties"]["getData"])
print("getData JSON schema validation: PASSED")
print(len(resp.get('results', [])), 'records')
n+=1
    
url = 'http://127.0.0.1:5000/countInPolygon'

params = {
    'key': '123',
    'polygon': '-74 42,-75 39,-74 41,-74 42'
}

r = requests.get(url, params=params)
resp = r.json()
validate(instance=resp, schema=json.load(open("schemas.json"))["properties"]["countInPolygon"])
print("countInPolygon JSON schema validation: PASSED")

print('Polygon test:', resp['msg'])
print('Count:', resp.get('count'))

url = 'http://127.0.0.1:5000/getAvgSpeedByFlight'

params = {
    'key': '123',
    'start': '2022-11-23 05:00:00',
    'end': '2022-11-23 08:00:00'
}

r = requests.get(url, params=params)
resp = r.json()

print('Average Speed test:', resp['msg'])
print('Number of flights:', resp.get('num_results'))


validate(instance=resp, schema=json.load(open("schemas.json"))["properties"]["getAvgSpeedByFlight"])
print("Average Speed JSON schema validation: PASSED")