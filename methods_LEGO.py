# all LEGO methods file
from pandas.io import sql
import pymysql as mdb
from datetime import datetime
import random
import numpy as np
import pandas
from brickset import *
from amazonproduct import API
from bs4 import BeautifulSoup
import lxml
import matplotlib.pyplot
import urllib2
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import itertools
import time
from time import mktime
import re

########## methods ###########
amazon_api = API(locale='us') # setup amazon API

def am_search_toys(SetName):
    # get only LEGO model number
    try:
    	search_result = amazon_api.item_search('Toys', Keywords=SetName)
    	return search_result
    except:
    	return 0

def am_search_item(ASIN):
    # search based on ASIN
    try:
		search_result = amazon_api.item_lookup(ASIN)
		return search_result
    except:
        return 0

def am_search(SetName):
    # get only LEGO model number
    search_result = amazon_api.item_search('Toys', Keywords=SetName)
    try:
        for item in search_result:
            # use only the top result for now
            return item.ASIN.text
    except:
        return NaN

def amLookupASIN(iASIN,myPanda):
    p = re.compile(ur'[0-9]{3,10}')
    lookUP = amazon_api.item_lookup(iASIN)
    for item in lookUP.Items.Item:
        myPanda.loc[len(legoSets)-1,'ASIN']=np.squeeze(item.ASIN) # use only the top result for now
        myPanda.loc[len(legoSets)-1,'SetName']=item.ItemAttributes.Title.text
        myPanda.loc[len(legoSets)-1,'SetNumber']=re.search(p,item.ItemAttributes.Title.text).group(0)
    return myPanda


########## brickset search
p_dd = re.compile(ur'\d.\d')
p_nn = re.compile(ur'^[0-9]*')

def getBrickSets(SetNumber,myPanda):
    tryurl =  "http://brickset.com/sets/"+SetNumber # setup the url
    # print tryurl
    response = urllib2.urlopen(tryurl)
    html = response.read()
    
    parsedHtml = BeautifulSoup(html,'lxml')  # parse with BeautifulSoup
    myPanda.loc[len(legoSets)-1,'Theme']=str(parsedHtml.find("dt",text="Theme").find_next_sibling("dd").text)
    myPanda.loc[len(legoSets)-1,'introYear']=str(parsedHtml.find("dt",text="Year released").find_next_sibling("dd").text)
    myPanda.loc[len(legoSets)-1,'pieces']=str(parsedHtml.find("dt",text="Pieces").find_next_sibling("dd").text)
    usd = parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text.find('$')
    myPanda.loc[len(legoSets)-1,'retailPrice']=parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text[usd+1:]
    try:
        myPanda.loc[len(legoSets)-1,'minifigs']=int(parsedHtml.find("dt",text="Minifigs").find_next_sibling("dd").text)
    except:
        pass
    
    # brickset rating
    try: 
        text = str(parsedHtml.find_all("div", {"class":"rating"})[0])
        myPanda.loc[len(legoSets)-1,'rating_B']=float(re.search(p_dd,text).group(0))
    except:
        pass
    
    # how many want, how many have it
    for item in parsedHtml.find_all("li"):
        if " people own this set" in item.text:
            myPanda.loc[len(legoSets)-1,'have_it']=re.search(p_nn,item.text).group(0)
        if " want this set" in item.text:
            myPanda.loc[len(legoSets)-1,'want_it']=re.search(p_nn,item.text).group(0)
        
    return myPanda



   