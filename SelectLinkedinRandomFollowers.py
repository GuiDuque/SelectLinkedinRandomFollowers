import asyncio
from pyppeteer import launch
import pandas as pd
import requests
from json import loads
import time
import random
from datetime import datetime

random.seed(datetime.now())

# ============

global headers

async def get_headers():
    global headers
    headers = {}

    browser = await launch(
            headless=False,
            args=['--no-sandbox'],
            autoClose=False
        )
    page = await browser.newPage()
    await page.goto("https://www.linkedin.com/login")

    input("continue?")


    await page.goto("https://www.linkedin.com/feed/followers/")
    await page.setRequestInterception(True)
    async def intercept(request):
        if ("https://www.linkedin.com/voyager/api/feed/richRecommendedEntities" in request.url ):
            global headers
            headers = request.headers
            print(len(headers))
        await request.continue_()
    page.on('request', lambda req: asyncio.ensure_future(intercept(req)))
    await page.evaluate( "() => { window.scrollBy(0, window.innerHeight); }")
    await page.evaluate( "() => { window.scrollBy(0, window.innerHeight); }")
    time.sleep(5)
    cookie1 = await page.cookies()
    s = []
    for e in cookie1:
        s.append(f"{e['name']}={e['value']}")
    cookie1_str = "; ".join(s)
    headers = {key: str(value) for key, value in headers.items()}
    headers["cookie"] = cookie1_str


    return page

page = asyncio.run(get_headers())


# ============

def get_followers_data(countw, index_start, headers):
    try:
        url = "https://www.linkedin.com/voyager/api/feed/richRecommendedEntities?count={countw}&q=followerRecommendations&start={index_start}"
        resp = requests.get(url=url.format(countw=countw, index_start=index_start), headers=headers)
        if resp.status_code == 200:
            data = loads(resp.content.decode("utf-8"))
            return data
        else:
            raise Exception(f"not allowed. headers or coockies problems. Status: {resp.status_code}")
    except Exception as e:
        print(f"error: {e}")
        return []
    
def refine_follower_data(data):
    folowers = {}
    for element in data['data']['elements']:
        for inc in data['included']:
            ek = element.get("*recommendedEntity", "a").split(":member:")[-1]
            ik = inc.get('entityUrn',"b").split(":")[-1]
            if ek == ik:
                e = dict()
                e.update(element)
                e.update(inc)
                folowers[ek] = folowers.get(ek, {})
                folowers[ek].update(e)
    return folowers

def filter_follower_data(fl):
    return {
        "seguidores": fl["followerCount"],
        "nome": f"{fl['firstName']} {fl['lastName']}",
        "cargo": fl["occupation"],
        "link": f'https://www.linkedin.com/in/{fl["publicIdentifier"]}'
    }

def get_followers(count, index_start, headers):
    data = get_followers_data(count, index_start, headers)
    followers = refine_follower_data(data)
    filtered_followers = [filter_follower_data(fl) for fl in followers.values()]
    return pd.DataFrame.from_dict(filtered_followers)
    
url_api_seguidores = "https://www.linkedin.com/voyager/api/feed/richRecommendedEntities?count={quantidade}&q=followerRecommendations&start={index_escolhidos}"
quantidade = 2
total_aproximado_de_seguidores = 11500
index_escolhidos = random.randint(0, total_aproximado_de_seguidores)

fs = get_followers(quantidade, index_escolhidos, headers)

print(fs)
input("finished?")



