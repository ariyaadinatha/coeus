import requests
import json


def check():
    url = "https://api.osv.dev/v1/query"
    obj = {"version": "2.10.1", "package": 
            {"name": "jinja2", "ecosystem": "PyPI"}
        }
    res = requests.post(url, json=obj)
    print((res.text))
    # print(type(res.json()))
    # s = json.loads(res.text)
    # with open("b.json", 'w') as file:
    #     file.write(json.dumps(s, indent=4))

check()