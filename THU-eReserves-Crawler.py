import re
import sys
import json
import random
import requests
from fpdf import FPDF
from PIL import Image
from io import BytesIO
from time import sleep
from bs4 import BeautifulSoup

# initialize
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config         = json.load(f)
        jcclient       = config['jcclient']
        bookList       = config['bookList']
        start          = config['start']
        end            = config['end']        
except:
    print('Failed to load config.json. Please check the file.')
    sys.exit()
    
for bookId in bookList:
    num     = 0
    flag    = False
    url     = 'https://ereserves.lib.tsinghua.edu.cn'
    headers = {
        'jcclient'      : jcclient,
        'user-agent'    : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    }

    # get book detail
    response = json.loads(requests.get(f'{url}/userapi/MyBook/getBookDetail?bookId={bookId}', headers=headers).text)['data']['jc_ebook_vo']
    sources  = response['urls']
    title    = response['EBOOKNAME']
    for source in sources:
        if source['SOURCE_NAME'] == '数字资源平台':
            flag = True
            break
    if not flag:
        print(f'The source of {title} is not 数字资源平台.')
        sys.exit()
    print(f'Downloading {title}...')

    # get BotuReadKernel
    readurl  = source['READURL']
    response = requests.post('https://ereserves.lib.tsinghua.edu.cn/userapi/ReadBook/GetResourcesUrl', headers=headers, json={'id': readurl})
    response = requests.get(response.json()['data'], allow_redirects=False)
    BotuReadKernel = response.cookies.get('BotuReadKernel')
    headers['botureadkernel'] = BotuReadKernel
    headers['cookie'] = 'BotuReadKernel=' + BotuReadKernel

    # selectJgpBookChapters
    url      = url + '/readkernel'
    title    = re.sub(r'[\\/:*?"<>|]', '.', title)
    data     = {'SCANID': BeautifulSoup(requests.get(f'{url}/ReadJPG/JPGJsNetPage/{readurl}', headers=headers).text, 'lxml').find('input', {'name': 'scanid'}).get('value')}
    chapters = json.loads(requests.post(f'{url}/KernelAPI/BookInfo/selectJgpBookChapters', headers=headers, data=data).text)['data']
    pdf      = FPDF()

    # selectJgpBookChapter
    for chapter in chapters:
        flag = False
        data = {'EMID': chapter['EMID'], 'BOOKID': readurl}
        # retry 3 times if failed
        for i in range(4):
            response = requests.post(f'{url}/KernelAPI/BookInfo/selectJgpBookChapter', headers=headers, data=data)
            if response.status_code == 200:
                response = response.json()
                if response['code'] != 1:
                    print(f'Failed to get chapter "{chapter["EFRAGMENTNAME"]}". Info: {response['info']}.')
                    sys.exit()
                flag = True
                break
            else:
                sleep(random.uniform(2*i+1, 4*i+2))
        if not flag:
            print(f'Failed to get chapter "{chapter['EFRAGMENTNAME']}". Please retry later.')
            sys.exit()
        response = response['data']['JGPS']
        # download JPG files and add to PDF
        for item in response:
            num += 1
            if num < start:
                continue
            if end != -1 and num > end:
                pdf.output(f'{title}.pdf')
                print(f'Finished downloading {title}.pdf.')
                sys.exit()
            sleep(random.uniform(0.2, 0.5))
            # retry 3 times if failed
            for i in range(4):
                page = requests.get(f'{url}/JPGFile/DownJPGJsNetPage?filePath={item['hfsKey']}', headers=headers)
                if page.status_code == 200:
                    img = Image.open(BytesIO(page.content))

                    output_buffer = BytesIO()
                    img.save(output_buffer, format='JPEG', quality=80, optimize=True, progressive=True)
                    page = output_buffer.getvalue()

                    width, height = img.size
                    pdf.add_page(format=(width*25.4/72, height*25.4/72))
                    pdf.image(BytesIO(page), x=0, y=0, w=width*25.4/72, h=height*25.4/72)
                    if flag:
                        pdf.start_section(name=chapter['EFRAGMENTNAME'], level=0)
                        flag = False
                    break
                else:
                    if i != 3:
                        sleep(random.uniform(2*i+1, 4*i+2))
                    else:
                        print(f'Failed to download page {num}.')
                        pdf.add_page(format=(width*25.4/72, height*25.4/72))

    pdf.output(f'{title}.pdf')
    print(f'Finished downloading {title}.pdf.')