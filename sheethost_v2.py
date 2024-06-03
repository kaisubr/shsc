
from requests_html import HTMLSession
from datetime import datetime
from random import randint
import time
import sys
import os, os.path
from tqdm import tqdm

# os.system("clear") 
# https://pypi.org/project/requests-html/ 
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
REF = "links.out"
LOG = "debug.log"
SAMPLE = "https://python.org"
INI = "https://sheet.host/category/anime"
INIHOST = INI.split("//")[1].split("/")[0]
OVERWRITE = False 
 
sess = HTMLSession()


def getReference():
    print("Updating local list of available sheet music... \n > This may take some time.")
    res = sess.get(INI) # () 

    links = res.html.absolute_links
    print("Found", len(links), "links, downloading...")

    f = open(REF, "w")
    f.write("SIZE " + str(len(links)) + ", DATE " + str(datetime.now()) + ", GET " + str(INI) + "\n")
    
    for k in links:
        print("INDEX ", k, end="\r")
        f.write(k + "\n")
    print("Done", end="\r")
    
    f.close()

def readReference():
    lines = []
    print("...")
    with open(REF, "r") as rfile:
        # print(f.read())
        lines = [k for k in rfile]
            
    infoLine = lines[0].split(", ")
    info = {"size": infoLine[0].split(" ")[1], "date": infoLine[1].split(" ")[1], "get": infoLine[2].split(" ")[1]}
    
    print("Reference has size", info["size"], "updated on", info["date"])
    links = lines[1:]
    space = ''.join([' ']*100) 
    
    with HTMLSession() as entry: 
        import requests

        headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'https://sheet.host',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-GPC': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://sheet.host/account/login',
        'Accept-Language': 'en-US,en;q=0.9',
        }

        data = {
        'login': USERNAME,
        'password': PASSWORD,
        'remember': '1'
        }

        response = entry.post('https://sheet.host/account/login', headers=headers, cookies=None, data=data) 
        
        if response and "Invalid" in response.html.text:
            print(response.html.find(".alert-error", first=True).text)
            return 
        
        with open(LOG, "a") as logfile:
            count, actual = 0, 0
            for n in tqdm(range(len(links)), desc="Progress", colour="green"):
                k = links[n]
                link = k.split("\n")[0]
                count += 1
                if INIHOST not in link:
                    print("SKIP", INIHOST, "not in", link, file=logfile)
                    continue
                
                endl = link.split("sheet.host/")[-1] # sheet/Zn5BR7, don't want '/' prior to 'sheet'
                dldir = endl + "/"
                
                if not os.path.isdir(dldir) and "sheet" in endl:
                    os.makedirs(dldir) 
                elif os.path.isdir(dldir) and OVERWRITE and "sheet" in endl:
                    print("OVERWRITE", dldir, "as it exists", file=logfile)
                else:
                    print("SKIP", dldir, "exists or is unexpected", file=logfile)
                    continue
                # res = sess.get(link)
                 
                save_name = "???" 
                
                tqdm.write("From " + link) 
                try: 
                    response = entry.get(link) 
                    ul = response.html.find(".sheet-download > .nav-list", first=True) 
                    items = ul.find("li") 
                    cin = 0
                    from collections import defaultdict
                    retrieve = defaultdict(lambda: None) # retrieve = set()

                    for li in items:
                        name, where = li.find("a", first=True).text.split("\n")[0], list(li.find("a", first=True).absolute_links)
                        where = [k for k in where if "download" in k or "expires" in k or "signature" in k]
                        # "at", where[0:min(15, len(where))] + "..."
                        if len(where) > 0:
                            retrieve[name] = where[0] # retrieve.update(where)

                    for name, place in retrieve.items():
                        cin += 1
                        tqdm.write("> " + str(count) + "/" + str(info["size"]) + " pt. " + str(cin) + "/" + str(len(retrieve)) + "\t" + name)
                        save_name = name[0:name.rfind("(")].replace(" ", "")
                        with open(dldir + name[0:name.rfind("(")].replace(" ", ""), "wb") as save:
                            save.write(entry.get(place).content)
                except BaseException as e: 
                    print("Error,", e, file=logfile) 
                
                actual += 1
                time.sleep(randint(1, 2)) 
     
    print("Done", end="\r")
    print("\n")
    
    print(actual, " new (out of ", info["size"], " links) were downloaded, see ", LOG, " for more information. \n > If the reference is out-of-date, delete ", REF, sep="")

if os.path.isfile(REF):
    print("Database reference found, skipping initial download \n > To force an update, rename or delete", REF)
    readReference()
else:
    getReference()
    readReference()
  
