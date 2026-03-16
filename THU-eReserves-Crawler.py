import re
import sys
import json
import random
import requests
from fpdf import FPDF
from PIL import Image
from tqdm import tqdm
from io import BytesIO
from time import sleep
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# initialize
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config   = json.load(f)
        jcclient = config["jcclient"]
        bookList = config["bookList"]
        threads  = config["threads"]
except:
    print("Failed to load config.json. Please check the file.")
    sys.exit()
    
for bookId in bookList:
    num     = 0
    flag    = False
    url     = "https://ereserves.lib.tsinghua.edu.cn"
    headers = {
        "jcclient"   : jcclient,
        "user-agent" : "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    }
    session = requests.Session()
    session.headers.update(headers)

    # get book detail
    response = json.loads(session.get(f"{url}/userapi/MyBook/getBookDetail?bookId={bookId}").text)["data"]["jc_ebook_vo"]
    sources  = response["urls"]
    title    = response["EBOOKNAME"]
    for source in sources:
        if source["SOURCE_NAME"] == "数字资源平台":
            flag = True
            break
    if not flag:
        print(f"The source of {title} is not 数字资源平台.")
        sys.exit()
    print(f"Downloading {title}...")

    # get BotuReadKernel
    readurl  = source["READURL"]
    response = session.post("https://ereserves.lib.tsinghua.edu.cn/userapi/ReadBook/GetResourcesUrl", json={"id": readurl})
    response = session.get(response.json()["data"], allow_redirects=False)
    BotuReadKernel = response.cookies.get("BotuReadKernel")
    session.headers["botureadkernel"] = BotuReadKernel
    session.cookies.set("BotuReadKernel", BotuReadKernel)

    # selectJgpBookChapters
    url      = url + "/readkernel"
    title    = re.sub(r"[\\/:*?\"<>|]", ".", title)
    data     = {"SCANID": BeautifulSoup(session.get(f"{url}/ReadJPG/JPGJsNetPage/{readurl}").text, "lxml").find("input", {"name": "scanid"}).get("value")}
    chapters = json.loads(session.post(f"{url}/KernelAPI/BookInfo/selectJgpBookChapters", data=data).text)["data"]
    pdf      = FPDF()

    # selectJgpBookChapter
    all_pages_tasks   = []
    chapter_bookmarks = []
    current_total_idx = 0
    for chapter in chapters:
        data = {"EMID": chapter["EMID"], "BOOKID": readurl}
        resp = session.post(f"{url}/KernelAPI/BookInfo/selectJgpBookChapter", data=data).json()
        jgps = resp["data"]["JGPS"]
        chapter_bookmarks.append((current_total_idx, chapter["EFRAGMENTNAME"]))
        for item in jgps:
            all_pages_tasks.append((current_total_idx, item["hfsKey"]))
            current_total_idx += 1

    # download pages
    def download_page(page_info):
        idx, hfs_key = page_info
        for _ in range(4):
            try:
                page_res = session.get(f"{url}/JPGFile/DownJPGJsNetPage?filePath={hfs_key}", timeout=10)
                if page_res.status_code == 200:
                    img = Image.open(BytesIO(page_res.content))
                    output_buffer = BytesIO()
                    img.save(output_buffer, format="JPEG", quality=80, optimize=True)
                    return idx, output_buffer.getvalue(), img.size
            except:
                pass
            sleep(random.uniform(1, 2))
        return idx, None, (210, 297)

    results = [None] * len(all_pages_tasks)
    print(f"Starting concurrent download with {threads} threads...")
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for res in tqdm(executor.map(download_page, all_pages_tasks), total=len(all_pages_tasks), unit="page"):
            results[res[0]] = res

    # write pages to pdf
    pdf = FPDF()
    bookmark_map = dict(chapter_bookmarks)
    
    for i, data, size in results:
        if i in bookmark_map:
            pdf.add_page(format=(size[0]*25.4/72, size[1]*25.4/72))
            pdf.start_section(name=bookmark_map[i], level=0)
        else:
            pdf.add_page(format=(size[0]*25.4/72, size[1]*25.4/72))
        if data:
            pdf.image(BytesIO(data), x=0, y=0, w=pdf.w, h=pdf.h)
        else:
            print(f"Page {i} is empty due to download failure.")

    pdf.output(f"{title}.pdf")
    print(f"Finished downloading {title}.pdf.")