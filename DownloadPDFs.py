import os
from urllib.request import urlopen
import requests
import re
from bs4 import BeautifulSoup
import json

DATE = 2017

url = 'https://law.resource.org/pub/in/bis/manifest.irc.html'
u = urlopen(url)
html = u.read().decode('utf-8')
soup = BeautifulSoup(html, "html.parser")
link_directory = {}

if not os.path.exists("./PDFs"):
    os.makedirs("./PDFs")

for row in soup.find_all("tr"):
    if row.find_all("td"):
        date = row.find_all("td")[1].text
        if int(date) >= DATE:
            link = row.find('a')
            pdf_url = f"https://law.resource.org/pub/in/bis/{link['href']}"
            filename = f'{link.text} {date}'
            link_directory[filename] = pdf_url
            with open(f'./PDFs/{filename}.pdf', 'wb') as f:
                f.write(requests.get(pdf_url).content)
            print("Downloaded ", filename)

with open('./link_directory.json', 'w', encoding ='utf8') as json_file:
    json.dump(link_directory, json_file, ensure_ascii = False)