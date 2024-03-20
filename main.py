import urllib.request
import re
import random
import requests
from flask import Flask, request, send_file, render_template, jsonify
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
import asyncio
import base64
import json
import articletextmanager

import users
from headlines import Headlines

print("Starting...")

load_dotenv()
client = OpenAI()
_headlines = Headlines()
hdr = {'User-Agent': 'Mozilla/5.0'}


# genai.configure(api_key="AIzaSyAgJK_XqImu5ulw2raEasMllxiCSC-MsiY")

# defaults = {
#     'model': 'models/text-bison-001',
#     'temperature': 0.7,
#     'candidate_count': 1,
#     'top_k': 40,
#     'top_p': 0.95,
#     'max_output_tokens': 1024,
#     'stop_sequences': [],
#     'safety_settings': [{"category":"HARM_CATEGORY_DEROGATORY","threshold":"BLOCK_LOW_AND_ABOVE"},  {"category":"HARM_CATEGORY_TOXICITY","threshold":"BLOCK_LOW_AND_ABOVE"},{"category":"HARM_CATEGORY_VIOLENCE",  "threshold":"BLOCK_MEDIUM_AND_ABOVE"},{"category":"HARM_CATEGORY_SEXUAL","threshold":"BLOCK_MEDIUM_AND_ABOVE"},  {"category":"HARM_CATEGORY_MEDICAL","threshold":"BLOCK_MEDIUM_AND_ABOVE"},  {"category":"HARM_CATEGORY_DANGEROUS","threshold":"BLOCK_MEDIUM_AND_ABOVE"}],
# }

# url = "https://www.foxnews.com/world/hamas-releases-more-israeli-hostages-6th-day-cease-fire"
# url = "https://www.newsmax.com/us/joe-biden-impeachment-house/2023/11/29/id/1144091/"
# url = "https://www.cnn.com/2023/11/29/politics/vivek-ramaswamy-aide-trump-campaign/index.html"

omitted_paragraph_keywords = ["all rights reserved", "subscribe", "newsletter", "@", "©", "(c)", "advertis", "cookie", "newsmax", "registered trademark"]

margin = 2

def extractText(url):
    html = urllib.request.urlopen(urllib.request.Request(url, headers=hdr))
    html_parse = BeautifulSoup(html, "html.parser")
    
    text = ""
    for para in html_parse.find_all("p"): 
        para_text = para.get_text()
        para_text_lower = para_text.lower()
        
        # Omit paragraphs with certain keywords
        omit = False
        for word in omitted_paragraph_keywords:
            if word in para_text_lower:
                omit = True
                break
        
        if omit: continue
        text += para_text + "[NEWPARA]"
    
    # Remove excess newlines
    text = text.replace("\n", "").replace("[NEWPARA]", "\n\n")
    # print(text)

    return text

def textToHTML(text):
    return text.replace("\n", "<br/>")

def corroborate(orig_url):
    #print("extracting content...")
    #text1 = extractText(url1)
    #print("text 1 extracted.")
    #text2 = extractText(url2)
    #print("text 2 extracted.")
    #prompt = f"summarize these two passages into a single news report:\n\"{text1}\"\n\"{text2}\""
    #print("content extracted.\ncorroborating...")
    # print(prompt)
    # print(f"{prompt}\n=============\n\n")
    text = articletextmanager.getText()
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You need to talk like you are a news article. Additionally, you need to avoid as much bias as possible and omit extreme opinions. Please leave your response in the form of multiple indented paragraphs. Note that every paragraph has to be started with \"<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\" without the quotes and end with \"</p>\" without the quotes."},

            {"role": "user", "content": text}


        ],
        temperature = 0,
    )

    print(completion.choices[0].message['content'])

    return completion.choices[0].message.content

def decode(encoded):
    return base64.b64decode(encoded.encode("ascii")).decode("ascii")

#print(extractText("https://abcnews.go.com/US/fbi-investigating-south-carolina-couple-accused-harassing-neighbors/story?id=105825286"))
# corroborate("https://www.newsmax.com/us/joe-biden-impeachment-house/2023/11/29/id/1144091/", "https://www.cnn.com/2023/11/29/politics/vivek-ramaswamy-aide-trump-campaign/index.html")




# ==========================================================

# ROUTING SHENANIGANS

app = Flask(__name__)

@app.route("/")
def index():
    return send_file("static/index.html")

@app.route("/signup/<redirect>")
def signup(redirect):
    return render_template("signup.html", redirect=decode(redirect), redirect_raw=redirect)

@app.route("/login/<redirect>")
def login(redirect):
    return render_template("login.html", redirect=decode(redirect), redirect_raw=redirect)

@app.route("/dashboard")
def dashboard():
    return send_file("static/dashboard.html")

@app.route("/information")
def information():
    return send_file("static/information.html")

@app.route("/corroborate/<url_encoded>/<settings_json_encoded>")
def _corroborate(url_encoded, settings_json_encoded):
    url1 = decode(url_encoded)
    html = urllib.request.urlopen(urllib.request.Request(url1, headers=hdr)) 
    html_parse = BeautifulSoup(html, "html.parser")

    settings = json.loads(decode(settings_json_encoded))

    # implementt a way to get the second link
    #url2 = "https://www.cnn.com/2023/11/29/politics/vivek-ramaswamy-aide-trump-campaign/index.html"


    content = corroborate(url1)
    print("done corroborating.")
    
    return render_template("corroborate.html",
        title=html_parse.title.string, source1=url1, source2=url2, content=content)

@app.route("/isitdown")
def ping():
    return "no it fucking isn't"

@app.route("/gimme", methods=["POST", "GET"])
def gimme():
    data = _headlines.getTopHeadlines()["entries"]
    print(type(data))

    # print(data)

    # print("==============\n\n\n")
    # print(response.json())
    # print("==============\n\n\n")

    return jsonify(data)

@app.route("/getuserdata/<username_encoded>/<password_encoded>", methods=["POST", "GET"])
def getUserData(username_encoded, password_encoded):
    data = users.authenticate(decode(username_encoded), decode(password_encoded))
    print(data)
    return jsonify(data)

@app.route("/createaccount/<username_encoded>/<password_encoded>", methods=["POST", "GET"])
def createAccount(username_encoded, password_encoded):
    data = users.createAccount(decode(username_encoded), decode(password_encoded))
    print(data)
    return jsonify(data)

@app.route("/savearticle/<username_encoded>/<password_encoded>/<id>/<title_encoded>", methods=["POST", "GET"])
def saveArticle(username_encoded, password_encoded, id, title_encoded):
    data = users.saveArticle(decode(username_encoded), decode(password_encoded), id, decode(title_encoded))
    print("ARTIFCLE SAVED")
    print(data)
    return jsonify(data)

@app.route("/<path>")
def eroughwoerug(path):
    try:
        return send_file(f"static/{path}")
    except:
        pass
    return send_file(f"static/404.html")

if __name__ == '__main__':
#    app.run(debug = True)
    async def load():
        from waitress import serve
        await _headlines.setTopHeadlines()
        print("Running...")
        serve(app, host="0.0.0.0", port=8000)
    asyncio.run(load())
    _headlines.startInterval()