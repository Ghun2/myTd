import json
import requests

mykey = "KakaoAK b0f4fc82fe8374aa3e2b7de0d771570b"

def getLatLng(addr):
  # url = 'https://dapi.kakao.com/v2/local/search/address.json?query='+addr
  url = 'https://dapi.kakao.com/v2/local/search/keyword.json?query=' + addr
  headers = {"Authorization": mykey}

  result = json.loads(str(requests.get(url,headers=headers).text))
  # match_first = result['documents'][0]['address']
  # return float(match_first['y']),float(match_first['x'])
  # return result
  print(result['documents'])
  print(result['meta'])
  res = result['documents'][0]
  for ky,vl in res.items():
    print(ky,vl)

input_addr = "강남역"
# input_addr = "매헌로 24"

getLatLng(input_addr)