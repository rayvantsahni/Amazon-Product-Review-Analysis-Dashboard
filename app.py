from flask import Flask, request, render_template, url_for, redirect, flash, Response
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pygal
from pygal.style import BlueStyle
from pygal.style import LightGreenStyle
from pygal.style import Style

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
product_dict = {}
product_links = []
reviews_list = []
img_dict = {}
totalRating = ''
avgRating = ''

@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		search_query = request.form['words']
		url = get_search_item(search_query)
		getProductdictionary(url)
		getProductLinks(url)
		return redirect(url_for('getProductList'))	
	return render_template("home.html")

@app.route('/ProductList',methods=['GET', 'POST'])
def getProductList():
	global product_dict
	global review_list
	global img_dict
	if request.method == 'POST':
		product_id = int(request.form['product_id'])
		asin = getAsin(product_links[product_id - 1])
		reviewList(reviewLink(str(asin)))	
		return redirect(url_for('getReviewAnalysis'))
	return render_template("productList.html",products=product_dict,images=img_dict)

@app.route('/ReviewAnalysis')
def getReviewAnalysis():
	reviews = sentiment_scores()


	custom_style = Style(
	background='transparent',
	plot_background='transparent',
	foreground='#53E89B',
	foreground_strong='#53A0E8',
	foreground_subtle='#630C0D',
	opacity='.7',
	opacity_hover='.99',
	transition='400ms ease-in',
	colors=('#ff1100', '#ffee00', '#0000ff'))
	
	# graph = pygal.Bar(fill = True, style=BlueStyle)
	graph = pygal.Bar(fill=True, interpolate='cubic', style=BlueStyle)
	graph.title = "Sentiment of the Users' Reviews"
	graph.x_labels = ["positive", "negative", "neutral"]
	graph.add("%age of Reviews",reviews)
	graph_data = graph.render_data_uri()





	pie = pygal.Pie(fill=True, interpolate='cubic', style=LightGreenStyle)
	pie.title = "Sentiment of the Users' Reviews"
	pie.add('positive', reviews[0])
	pie.add('negative', reviews[1])
	pie.add('neutral', reviews[2])
	pie_data = pie.render_data_uri()

	global totalRating
	global avgRating
	return render_template("ReviewAnalysis.html",graph_data=graph_data, pie_data=pie_data, total=totalRating, avg=avgRating)

def sentiment_scores(): 
	global reviews_list
	count, positive, negative, neutral = 0, 0, 0, 0
	for review in reviews_list:
	    sentiment_obj = SentimentIntensityAnalyzer()  
	    sentiment_dict = sentiment_obj.polarity_scores(review) 

	    if sentiment_dict['compound'] >= 0.05 : 
	        positive +=1
	        
	    elif sentiment_dict['compound'] <= - 0.05 : 
	        negative +=1
	        
	    else : 
	        neutral+=1    
	pos = (positive/len(reviews_list))*100
	neg = (negative/len(reviews_list))*100
	neu = (neutral/len(reviews_list))*100
	reviews = [pos,neg,neu]
	return reviews
    

def getAmazonSearch(url):
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
    page = requests.get(url, headers = header)
    if page.status_code == 200:
        return page
    else:
        return "Error"

def getAsin(selected_product_link): 
    x = selected_product_link.index("B0")
    asin = selected_product_link[x:x+10]
    return asin

def reviewLink(asin):
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
	asin_url = "https://www.amazon.in/dp/" + asin
	page = requests.get(asin_url, headers = header)
	page = page.text
	soup = BeautifulSoup(page)
	x = soup.find("a", {'class':'a-link-emphasis a-text-bold'})
	return 'https://www.amazon.in/' + str(x['href'])

def reviewList(url):
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
	global reviews_list
	global totalRating
	global avgRating
	page = requests.get(url, headers = header)
	page = page.text
	soup = BeautifulSoup(page)

	for i in soup.findAll("span", {'data-hook':"review-body"}):
	    reviews_list.append(i.text)

	y = soup.find("span", {"class": "a-size-base a-color-secondary"})
	totalRating =  y.text.split()[0]

	x = soup.find("span", {"data-hook": "rating-out-of-text"})
	avgRating = x.text

def get_search_item(search_query):
	search_query = search_query.replace(' ', '+')
	base_url = "https://www.amazon.in/s?k="
	url = base_url + search_query
	return (url)

def getProductdictionary(url):
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
	search_response = requests.get(url, headers=header)

	global product_dict
	product_names=[]
	response = getAmazonSearch(url)
	soup = BeautifulSoup(response.content)
	for i in soup.findAll("span", {'class':'a-size-base-plus a-color-base a-text-normal'}): 
	    product_names.append(i.text)
	    if len(product_names) == 6:
	        break

	for i, j in enumerate(product_names):
	    product_dict[i+1] = j

	image_info = soup.select('.s-image')
	for i, j in enumerate(image_info):
	    img_dict[i+1] = j['src']

def getProductLinks(url):
	header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
	search_response = requests.get(url, headers=header)

	global product_links
	global img_list
	page = requests.get(url)
	page = page.text
	soup = BeautifulSoup(search_response.content)

	for i in soup.findAll("a",{'class':'a-link-normal a-text-normal'}):
	    product_links.append(i['href'])

	# image_info = soup.select('.s-image')
	# for i, j in enumerate(image_info):
	#     img_dict[i+1] = j['src']

if __name__ == '__main__':
    app.run(host='127.0.0.1',debug=True)