from flask import render_template, request, redirect, url_for
from app import app
from a_Model import ModelIt
from methods_LEGO import am_search_toys
from amazonproduct import API
amazon = API(locale='us')
from lego_model import predictLegoRF
from Update_LEGO_app import *
import sys, os


@app.route('/')

@app.route('/input')
def legos_input():
  return render_template("input.html")

@app.route('/input_error')
def legos_input_error():
  return render_template("input_error.html")

@app.route('/contact')
def contact():
  return render_template("contact.html")

@app.route('/about')
def about():
  return render_template("about.html")

@app.route('/output1')
def legos_output1():
	#pull 'ID' from input field and store it
	lego_search = "Lego "+request.args.get('ID')
	print lego_search
	try:
		s_result = amazon.item_search('Toys', Keywords=lego_search, MerchantId='Amazon')
  	except:
	    return redirect('input_error')
  	
  	products = []
  	nresults = 0
  	for result in s_result:
  		nresults += 1
  		if nresults>3:
  			break
  		else:
			Title = result.ItemAttributes.Title
			ASIN = str(result.ASIN)
			print ASIN
			print Title
			# print etree.tostring(result, pretty_print=True)
			result = amazon.item_lookup(ASIN,ResponseGroup='Images,EditorialReview')
			try:
				imgurl = result.Items.Item.LargeImage.URL
			except:
				imgurl = []
			try:
				blurb = result.Items.Item.EditorialReviews.EditorialReview.Content
				blurb = str(blurb[0])[:200]+'...'
			except:
				blurb = []
			products.append(dict(name=Title, ASIN=ASIN, imgurl=imgurl, blurb=blurb))


  	return render_template('output1.html', products = products)

@app.route('/output2')
def legos_output2():
	ASIN2use = request.args.get('ID')
  	displayThis = []
  	# Lookup ASIN
	result = amazon.item_lookup(ASIN2use)
	Title = result.Items.Item.ItemAttributes.Title
	# print etree.tostring(result, pretty_print=True)
	result = amazon.item_lookup(ASIN2use,ResponseGroup='Images,EditorialReview')
	try:
		imgurl = result.Items.Item.LargeImage.URL
	except:
		imgurl = []
	
	try:
		blurb = result.Items.Item.EditorialReviews.EditorialReview.Content
		blurb = str(blurb[0])[:350]+'...'
	except:
		blurb = []

	displayThis.append(dict(name=Title, ASIN=ASIN2use, imgurl=imgurl, blurb=blurb))
  	
  	try:
	  	# get the price and sellout prediction
	  	predicted_price, nyears, predicted_sellout, pred_low, pred_upr = predictLegoRF(ASIN2use)
	except SetNumberError:
		out1err = url_for('output2error', ID=ASIN2use)
		# return results along with template to render
	  	return redirect(out1err)

	predicted_price = np.round(predicted_price,2)
	pred_low = np.round(pred_low,2)
	pred_upr = np.round(pred_upr,2)
	predicted_sellout = np.round(predicted_sellout,0)
	if predicted_sellout<0:
		print predicted_sellout
		predicted_sellout = "0"
  	# # test dummies
  	# predicted_price = [57.2,95.2]
  	# nyears = [1,5]
  	# preds = []
  	# predicted_sellout = 99 # in days
  	preds = []
  	# combine preds into a single dict
  	for P,N,L,U in zip(predicted_price,nyears, pred_low, pred_upr):
  		preds.append(dict(predicted_price=P,nyears=N, pred_low=L, pred_upr=U))

  	# return results along with template to render
  	return render_template("output2.html", displayThis = displayThis, 
  		preds=preds, predicted_sellout = predicted_sellout)

@app.route('/output1error')
def output1error():
	ASIN2use = request.args.get('ID')
  	displayThis = []
  	# Lookup ASIN
	result = amazon.item_lookup(ASIN2use)
	Title = result.Items.Item.ItemAttributes.Title
	# print etree.tostring(result, pretty_print=True)
	result = amazon.item_lookup(ASIN2use,ResponseGroup='Images,EditorialReview')
	imgurl = result.Items.Item.LargeImage.URL
	blurb = result.Items.Item.EditorialReviews.EditorialReview.Content
	blurb = str(blurb[0])[:200]+'...'
	displayThis.append(dict(name=Title, ASIN=ASIN2use, imgurl=imgurl, blurb=blurb))

   	return render_template("output1error.html", displayThis = displayThis)

@app.route('/output2error')
def output2error():
	ASIN2use = request.args.get('ID')
  	displayThis = []
  	# Lookup ASIN
	result = amazon.item_lookup(ASIN2use)
	Title = result.Items.Item.ItemAttributes.Title
	# print etree.tostring(result, pretty_print=True)
	result = amazon.item_lookup(ASIN2use,ResponseGroup='Images,EditorialReview')
	imgurl = result.Items.Item.LargeImage.URL
	blurb = result.Items.Item.EditorialReviews.EditorialReview.Content
	blurb = str(blurb[0])[:200]+'...'
	displayThis.append(dict(name=Title, ASIN=ASIN2use, imgurl=imgurl, blurb=blurb))

   	return render_template("output2error.html", displayThis = displayThis)

 #  	try:
	#   	# get the price and sellout prediction
	#   	predicted_price, nyears, predicted_sellout = predictLegoRF(ASIN2use)
	# except SetNumberError:
	# 	# return results along with template to render
	#   	return render_template("output1_error.html", displayThis = displayThis)
  	
 #  	preds=[]
 #  	# combine preds into a single dict
 #  	for P,N in zip(predicted_price,nyears):
 #  		preds.append(dict(predicted_price=P,nyears=N))

  	# return results along with template to render

	# test dummies
  	# predicted_price = [57.2,95.2]
  	# nyears = [1,5]
  	# preds = []
  	# predicted_sellout = 99 # in days
  	

# @app.route("/db_fancy")
# def cities_page_fancy():
#         db = mdb.connect(user="root", host="localhost", db="world",  charset='utf8')
# 	with db:
# 		cur = db.cursor()
# 		cur.execute("SELECT Name, CountryCode,Population FROM City ORDER BY Population LIMIT 15;")
# 		query_results = cur.fetchall()
# 	cities = []
# 	for result in query_results:
# 		cities.append(dict(name=result[0], country=result[1], population=result[2]))
# 	return render_template('cities.html', cities=cities)

