import requests


def get_links(keywords):
       #print("Given Promt: " + prompt)
       
       prompt = ""

       for word in keywords:
              prompt = prompt + "\"" + word + "\""
       prompt += "&"

       url = 'https://newsapi.org/v2/everything?' 

       parameters = {
              'q': prompt,
              'sortBy': 'popularity&',
              'language': 'en',
              'from': '2023-01-01&',
              'pageSize': 20,
              'apiKey': 'b9193754d63340e68e587962b953d3ac'
       }

       response = requests.get(url, params = parameters)

       response_json = response.json()
       for article in response_json['articles']:
              article_url = article["url"]
              print(f"{article_url}")

keywords = ["hamas", "hospital", "Israel"]
get_links(keywords)