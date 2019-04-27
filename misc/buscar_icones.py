import re
import urllib.request

from smashLadder import settings


URL = 'https://www.ssbwiki.com/Category:Head_icons_(SSBU)'

fp = urllib.request.urlopen(URL)
url_bytes = fp.read()

html = url_bytes.decode("utf8")
fp.close()

icones_url = re.findall(r'src="/images/thumb/[^"]+Website\.png"', html)
print(icones_url)

for icone_url in icones_url:
    url_formatada = icone_url.replace('src=', '').replace('"', '')
    print(url_formatada)
    
    nome_arquivo = url_formatada[url_formatada.find('120px-')+6:]
    nome_arquivo_formatado = nome_arquivo.replace('HeadSSBUWebsite', 'Icone')
    
    urllib.request.urlretrieve('https://www.ssbwiki.com' + url_formatada, settings.BASE_DIR + '/smashLadder/static/' + nome_arquivo_formatado)
