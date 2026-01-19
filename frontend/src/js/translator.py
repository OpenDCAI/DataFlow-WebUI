# %%
import os
import re
import json
import html
from urllib import parse
import requests

GOOGLE_TRANSLATE_URL = 'http://translate.google.com/m?q=%s&tl=%s&sl=%s'

def translate(text, to_language="auto", text_language="auto"):

    text = parse.quote(text)
    url = GOOGLE_TRANSLATE_URL % (text,to_language,text_language)
    response = requests.get(url)
    data = response.text
    expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
    result = re.findall(expr, data)
    if (len(result) == 0):
        return ""

    return html.unescape(result[0])

# print(translate("about your situation", "zh-CN","en")) #英语转汉语

# %%


result = {}
pattern = r"local\([\"'`][\w\d ,-.\?\(\)\+]+[\"'`]\)"
prefix = '../'

with open('i18n.js', encoding='utf-8') as f:
    oriI18N = f.read().replace('export default', '')
result = json.loads(oriI18N)

fileData = os.walk(prefix)
for root, dirs, files in fileData:
    for file in files:
        file = os.path.join(root, file)
        match_ext = ['.js', '.vue', '.html']
        if not file.endswith(tuple(match_ext)):
            continue
        with open(file, encoding='utf-8') as f:
            ori_content = f.read()
        matches = re.findall(pattern, ori_content)
        for match in matches:
            match = match[7:-2]
            if match in result:
                continue
            zh = translate(match, "zh-CN", "en")
            zh = zh.replace('聊天', '会话')
            zh = zh.replace('改名', '重命名')
            zh = zh.replace('登出', '注销')
            zh = zh.replace('再生反应', '重新生成')
            result[match] = {
                "en": match,
                "cn": zh
            }

# %%
with open('i18n.js', 'w+', encoding='utf-8') as f:
    jsonContent = json.dumps(result, indent=4, ensure_ascii=False)
    f.write('export default ' + jsonContent)

# %%
