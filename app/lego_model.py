# from pandas.io import sql
# import pymysql as mdb
from datetime import datetime
import random
import numpy as np
import pandas as pd
# from brickset import *
from scipy import stats, integrate
from amazonproduct import API
from bs4 import BeautifulSoup
import lxml
# import matplotlib.pyplot as plt
import urllib2
from bs4 import BeautifulSoup
import itertools
import time
from time import mktime
import re
import math
import shelve
from Update_LEGO_app import *
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestRegressor
from patsy import dmatrices
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestRegressor

def pred_int1(model, featX, percentile=90):
    err_down = []
    err_up = []
    preds = []
    for pred in model.estimators_:
    	# modelRF.estimators_[999].predict(predictX)
        preds.append(pred.predict(featX))
    err_down = np.percentile(preds, (100 - percentile))
    err_up = np.percentile(preds, 100 - (100 - percentile))
	# returns single err_up and err_down values
    return err_down, err_up

def predictLegoRF(ASIN):
	fn = '/Users/sharathbennur/Insights/Project/legoSet.pkl'
	model_shelf = shelve.open('lego_shelf.db')
	# def modelLego(ASIN = 'B00WHZ6WOO'):

	legos = pd.read_pickle(fn)
	try:
		modelRF = model_shelf['RF']
		ASINs = model_shelf['ASINs']
		time_to_sellout = model_shelf['time_to_sellout']
		legos_clean = model_shelf['legos_clean']
		print "Loaded from shelf"
	except: # if they are not in the shelf, make them all
		##### Load and clean up the data
		k,v = legos.shape
		priceA = np.empty((k,1))
		price3 = np.empty((k,1))
		wi = np.empty((k,1))
		hi = np.empty((k,1))
		HpriceA = np.empty((k,1))
		pie = np.empty((k,1))
		ASINs = []
		introD = []
		sellOD = []
		hpDA = []
		introY = []

		for I in range(0,k):
		    price3[I] = float(legos.loc[I,"currentPrice_3"])
		    priceA[I] = float(legos.loc[I,"currentPrice_A"])
		    wi[I] = float(legos.loc[I,"want_it"])
		    hi[I] = float(legos.loc[I,"have_it"])
		    pie[I] = float(legos.loc[I,"pieces"])
		    ASINs.append(str(legos.loc[I,"ASIN"]))
		    introD.append(str(legos.loc[I,"introDate"]))
		    hpDA.append(str(legos.loc[I,"highPriceDate_A"]))
		    sellOD.append(str(legos.loc[I,"selloutDate"]))
		    introY.append(str(legos.loc[I,"introYear"]))

		legos["ASIN"] = ASINs
		legos["currentPrice_3"] = price3
		legos["currentPrice_A"] = priceA
		legos["want_it"] = wi
		legos["have_it"] = hi
		legos["pieces"] = pie
		legos["introDate_S"] = introD
		legos["highPriceDate_A_S"] = hpDA
		legos["selloutDate_S"] = sellOD
		legos["introYear_S"] = introY
		legos["minifigs"] = legos["minifigs"].fillna(0)


		detectSlash = re.compile(ur'^\d*\.?\d*')
		rp = np.empty((k,1))
		for I in range(0,k):
		    try:
		        rp[I] = float(legos.loc[I,"retailPrice"])
		    except (UnicodeEncodeError, ValueError):
		        price = legos.loc[I,"retailPrice"]
		        price = price.encode("utf-8")
		        price1 = re.search(detectSlash,price)
		        price2 = price1.group(0)
		        price3 = re.sub('[^a-zA-Z0-9-_*.]', '', price2)
		        try:
		            rp[I] = float(price3)
		        except ValueError : # if there is a value error due to the GBP symbol
		            print "passing"

		legos["retailPrice"] = rp

		# Setting up the time variables
		from sklearn.preprocessing import Imputer

		# First "time to now", to get total appreciation in price
		legos["time_to_now"]=""
		legos["time_to_sellout"]=""
		k,v = legos.shape
		time_to_now = np.empty((k,1))
		time_to_sellout = np.empty((k,1))
		today=datetime.today()

		# sanity check to make sure all the dates are the correct format
		for I in legos.index:
		    try:
		        time_to_now[I] = (today - legos.loc[I,"introDate"]).days
		    except:
		        pass

		legos["time_to_now"] = time_to_now

		# Then "time_to_sellout" with imputing missing values
		for I in legos.index:
		    if isinstance(legos.loc[I,"selloutDate"], datetime):
		        try:
		            time_to_sellout[I] = (legos.loc[I,"selloutDate"] - legos.loc[I,"introDate"]).days
		        except:
		            pass
		    elif math.isnan(legos.loc[I,"selloutDate"]):
		        time_to_sellout[I] = 0

		imp = Imputer(missing_values=0,strategy='median')
		time_to_sellout = imp.fit_transform(time_to_sellout)

		legos["time_to_sellout"] = time_to_sellout
		legos["desirability"] = legos["want_it"]/legos["have_it"]

		# Compute Price Increase per day
		# Maximum Price Increase Prediction
		legos["maxPredictedRise_3"] = legos["highPrice_3"]/legos["retailPrice"]
		legos["maxPredictedRise_A"] = legos["highPrice_A"]/legos["retailPrice"]

		# Average Price Increase Prediction
		legos["avgPredictedRise_3"] = legos["avgPrice_3"]/legos["retailPrice"]
		legos["avgPredictedRise_A"] = legos["avgPrice_A"]/legos["retailPrice"]

		# convert maxPredictedRise_3 into a perday measure
		legos["maxPredictedRise_3perDay"] = legos["maxPredictedRise_3"]/legos["time_to_now"]
		legos["avgPredictedRise_3perDay"] = legos["avgPredictedRise_3"]/legos["time_to_now"]

		# Crude removal of outliers, ideally remove +/- 3 sd's - code later
		maxPredictedRise_3_Filter = legos['maxPredictedRise_3']<100

		legos = legos[maxPredictedRise_3_Filter]
		legos_clean = legos.reset_index() # make backup copy of the cleaned copy

		### at this point dataset is complete for model building
		# split data into testing and training sets
		cols_to_retain = ['maxPredictedRise_3perDay','desirability','minifigs','pieces',
		                  'Theme','rating_B','lowPrice_3','avgPrice_3','retailPrice',
		                  'time_to_now', 'want_it']

		# Setup all data
		legoData = legos_clean[cols_to_retain]

		model_target,model_features = dmatrices('maxPredictedRise_3perDay ~ desirability+minifigs+pieces+lowPrice_3+avgPrice_3+retailPrice+time_to_now + C(Theme)',legoData, return_type='dataframe')
		####### FITTING RF
		modelRF = RandomForestRegressor(n_estimators=1000) #, min_samples_leaf=1)
		modelRF.fit(model_features, np.ravel(model_target))

		print "Model Created"
		try:
			model_shelf['RF'] = modelRF
			model_shelf['ASINs'] = ASINs
			model_shelf['time_to_sellout'] = time_to_sellout
			model_shelf['legos_clean'] = legos_clean
			print "Saved to shelf"
		except:
			pass

	finally:
		# close the shelf you opened
		model_shelf.close()
		print "Closed Shelf"

	# At this point modelRF, ASINs and time_to_sellout are all in local memory,
	# either by loading from the shelf or by creating them

	######## PREDICTION
	cols_to_retain = ['maxPredictedRise_3perDay','desirability','minifigs',
							'pieces','lowPrice_3','avgPrice_3','time_to_now',
							'retailPrice','Theme']

	# ASINs - indexed list of all ASINs
	# legos_clean - current filtered panda
	# ASIN - current ASIN that we are making a prediction for
	# parse the incoming ASIN
	# ASIN = 'B00IANTQDQ'
	try:
		# ASIN_row = ASINs.index(ASIN)
		ASIN_row = legos_clean[legos_clean['ASIN'] == ASIN].index[0]
		tryMe = legos_clean.loc[ASIN_row,cols_to_retain] # make sure its not imcomplete
		if sum(tryMe.isnull()) > 0: # if there are any nans
			try:
				ASIN_row, legos_clean = getLegoSet(ASIN,legos_clean)
			except SetNumberError:
				raise SetNumberError('No SetNumber found')
	except IndexError:
		# if you didnt find it get all the info and add it to the db
		try:
			ASIN_row, legos_clean = getLegoSet(ASIN, legos_clean)
		except SetNumberError:
			raise SetNumberError('No SetNumber found')

	# print "legos_clean.shape"
	# print legos_clean.shape
	# print "ASIN row"
	# print legos_clean.loc[ASIN_row]

	##############################
	##### Clean up the data AGAIN
	k,v = legos_clean.shape
	priceA = np.empty((k,1))
	price3 = np.empty((k,1))
	wi = np.empty((k,1))
	hi = np.empty((k,1))
	HpriceA = np.empty((k,1))
	pie = np.empty((k,1))
	ASINs = []
	introD = []
	sellOD = []
	hpDA = []
	introY = []

	for I in legos_clean.index:
	    price3[I] = float(legos_clean.loc[I,"currentPrice_3"])
	    priceA[I] = float(legos_clean.loc[I,"currentPrice_A"])
	    wi[I] = float(legos_clean.loc[I,"want_it"])
	    hi[I] = float(legos_clean.loc[I,"have_it"])
	    pie[I] = float(legos_clean.loc[I,"pieces"])
	    ASINs.append(str(legos_clean.loc[I,"ASIN"]))
	    introD.append(str(legos_clean.loc[I,"introDate"]))
	    hpDA.append(str(legos_clean.loc[I,"highPriceDate_A"]))
	    sellOD.append(str(legos_clean.loc[I,"selloutDate"]))
	    introY.append(str(legos_clean.loc[I,"introYear"]))

	legos_clean["ASIN"] = ASINs
	legos_clean["currentPrice_3"] = price3
	legos_clean["currentPrice_A"] = priceA
	legos_clean["want_it"] = wi
	legos_clean["have_it"] = hi
	legos_clean["pieces"] = pie
	legos_clean["introDate_S"] = introD
	legos_clean["highPriceDate_A_S"] = hpDA
	legos_clean["selloutDate_S"] = sellOD
	legos_clean["introYear_S"] = introY
	legos_clean["minifigs"] = legos_clean["minifigs"].fillna(0)


	detectSlash = re.compile(ur'^\d*\.?\d*')
	rp = np.empty((k,1))
	for I in legos_clean.index:
	    try:
	        rp[I] = float(legos_clean.loc[I,"retailPrice"])
	    except (UnicodeEncodeError, ValueError):
	        price = legos_clean.loc[I,"retailPrice"]
	        price = price.encode("utf-8")
	        price1 = re.search(detectSlash,price)
	        price2 = price1.group(0)
	        price3 = re.sub('[^a-zA-Z0-9-_*.]', '', price2)
	        try:
	            rp[I] = float(price3)
	        except ValueError : # if there is a value error due to the GBP symbol
	            print "passing"

	legos_clean["retailPrice"] = rp

	# Setting up the time variables
	from sklearn.preprocessing import Imputer

	# First "time to now", to get total appreciation in price
	legos_clean["time_to_now"]=""
	legos_clean["time_to_sellout"]=""
	k,v = legos_clean.shape
	time_to_now = np.empty((k,1))
	time_to_sellout = np.empty((k,1))
	today=datetime.today()

	# sanity check to make sure all the dates are the correct format
	for I in legos_clean.index:
	    try:
	        time_to_now[I] = (today - legos_clean.loc[I,"introDate"]).days
	    except:
	        pass

	legos_clean["time_to_now"] = time_to_now

	# Then "time_to_sellout" with imputing missing values
	for I in legos_clean.index:
	    if isinstance(legos_clean.loc[I,"selloutDate"], datetime):
	        try:
	            time_to_sellout[I] = (legos_clean.loc[I,"selloutDate"] - legos_clean.loc[I,"introDate"]).days
	        except:
	            pass
	    elif math.isnan(legos_clean.loc[I,"selloutDate"]):
	        time_to_sellout[I] = 0

	imp = Imputer(missing_values=0,strategy='median')
	time_to_sellout = imp.fit_transform(time_to_sellout)

	legos_clean["time_to_sellout"] = time_to_sellout
	legos_clean["desirability"] = legos_clean["want_it"]/legos_clean["have_it"]

	# Compute Price Increase per day
	# Maximum Price Increase Prediction
	legos_clean["maxPredictedRise_3"] = legos_clean["highPrice_3"]/legos_clean["retailPrice"]
	legos_clean["maxPredictedRise_A"] = legos_clean["highPrice_A"]/legos_clean["retailPrice"]

	# Average Price Increase Prediction
	legos_clean["avgPredictedRise_3"] = legos_clean["avgPrice_3"]/legos_clean["retailPrice"]
	legos_clean["avgPredictedRise_A"] = legos_clean["avgPrice_A"]/legos_clean["retailPrice"]

	# convert maxPredictedRise_3 into a perday measure
	legos_clean["maxPredictedRise_3perDay"] = legos_clean["maxPredictedRise_3"]/legos_clean["time_to_now"]
	legos_clean["avgPredictedRise_3perDay"] = legos_clean["avgPredictedRise_3"]/legos_clean["time_to_now"]

	# pick only columns with relevant features
	legoData = legos_clean[cols_to_retain]
	# print legoData.shape

	# split into target and features, while accounting for categorical themes
	target,features = dmatrices('maxPredictedRise_3perDay ~ desirability+minifigs+pieces+lowPrice_3+avgPrice_3+retailPrice+time_to_now + C(Theme)',legoData, return_type='dataframe')
	# remember that only the features.loc[asin_row] corresponds to the ASIN we are predicting
	# only panda.loc works as .loc is a label based index
	# print features.shape
	# print ASIN_row
	predictX = features.loc[ASIN_row]

	#### Predict
	# now that we have the model, predict
	pred = modelRF.predict(predictX)

	# # We assume that the base price is the current retail price
	# currentPrice_A = legos_clean.loc[ASIN_row,'currentPrice_A']
	# if np.isnan(currentPrice_A):
	# 	currentPrice_A = legos_clean.loc[ASIN_row,'highPrice_A']
	# nyears = [0,1,2]
	# predicted_price = (nyears*pred*365)+currentPrice_A

	# We assume that the base price is the current retail price
	currentPrice_A = legos_clean.loc[ASIN_row,'currentPrice_A']
	if np.isnan(currentPrice_A):
		currentPrice_A = legos_clean.loc[ASIN_row,'highPrice_A']

	# Calculate the residuals
	nyears = [0,1,2]
	predicted_price = (nyears*pred*365)+currentPrice_A
	pred_conf_low, pred_conf_upr = pred_int1(modelRF, predictX, 90)
	pred_low = (nyears*(pred-pred_conf_low)*365)+currentPrice_A
	pred_upr = (nyears*(pred+pred_conf_upr)*365)+currentPrice_A

	# Predicted Sellout date
	mean_sellout = time_to_sellout.mean()
	predicted_sellout = mean_sellout-float((today-legos_clean.loc[ASIN_row,'introDate']).days)

	# # Save updated Dataset
	# now = datetime.now()
	# timestr = str(now.date().day)+'-'+str(now.hour)+'-'+str(now.minute)
	# # save a new pickle file with todays date
	# fn_new = '/Users/sharathbennur/Insights/Project/legos_clean'+'-'+timestr+'.pkl'
	# legos_clean.to_pickle(fn_new)

	print "Opened Shelf"
	model_shelf = shelve.open('lego_shelf.db')
	model_shelf['legos_clean'] = legos_clean
	model_shelf.close()
	print "Closed Shelf"

	return predicted_price, nyears, predicted_sellout, pred_low, pred_upr


