# from pandas.io import sql
# import pymysql as mdb
from datetime import datetime
import random
import numpy as np
import pandas
import pandas as pd
from brickset import *
from amazonproduct import API
from bs4 import BeautifulSoup
import lxml
import urllib2
from bs4 import BeautifulSoup
import itertools
import time
from time import mktime
import re
import mechanize
import cookielib
amazon_api = API(locale='us') # setup amazon API

class SetNumberError(Exception):
    def __init__(self, message):
        # # Call the base class constructor with the parameters it needs
        # super(ValidationError, self).__init__(message)
        # Now for your custom code...
        self.msg = message

# Browser
br = mechanize.Browser()

# Cookie Jar
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

# Browser options
br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)

# Follows refresh 0 but not hangs on refresh > 0
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

# Want debugging messages?
#br.set_debug_http(True)
#br.set_debug_redirects(True)
#br.set_debug_responses(True)
# User-Agent (this is cheating, ok?)
br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
# ASIN = 'B00WHZ6WOO'
# tryurl =  "http://www.camelcamelcamel.com/product/"+ASIN # setup the url

#### Top level function that will get all the data for a single set and update 
#### the panda as needed
## remember that myPanda here contains only valid rows, its not complete
def getLegoSet(ASIN, myPanda):
    # update from amazon
    try:
        myPanda,SN,ASIN_row = amLookupASIN2(myPanda,ASIN)
    except SetNumberError:
        raise SetNumberError('No SetNumber found')

    # update from camelcamelcamel
    try:
        myPanda = updateCamels(ASIN,myPanda,ASIN_row)
    except:
        pass

    # update from bricksets
    try:
        myPanda = updateBrickSets(SN,myPanda,ASIN_row)
    except:
        pass

    return ASIN_row, myPanda


# lookup using amazon's API
def amLookupASIN2(myPanda,ASIN):
    p = re.compile(ur'[0-9]{3,10}')
    # if it exists, update it, if not get it afresh
    try:
        ASIN_row = myPanda[myPanda['ASIN'] == ASIN].index[0]
        myPanda.loc[ASIN_row,'ASIN']=ASIN
        # if its incomplete, do the same as in the except statement
        tryMe = myPanda.loc[ASIN_row] # make sure its not imcomplete
        if sum(tryMe.isnull()) > 0: # if there are any nans
            lookUP = amazon_api.item_lookup(ASIN) # then lookUP and update myPanda
            for item in lookUP.Items.Item:
                myPanda.loc[ASIN_row,'SetName']=item.ItemAttributes.Title.text
                try:
                    myPanda.loc[ASIN_row,'SetNumber']=re.search(p,item.ItemAttributes.Title.text).group(0)
                except AttributeError: # if the set number isnt found, ask the user for it
                    raise SetNumberError('No SetNumber found')
                break # after the 1st one
        # if it exists and is valid, return the row number so its updated
        return myPanda,myPanda.loc[ASIN_row,'SetNumber'], ASIN_row

    except (TypeError, IndexError):
        ### if its new, add a new line
        newRow = myPanda.index.max()+1
        myPanda.loc[newRow] = np.nan
        myPanda.loc[newRow,'ASIN']=ASIN
        lookUP = amazon_api.item_lookup(ASIN) # then lookUP and update myPanda
        for item in lookUP.Items.Item:
            # myPanda.loc[newRow,'ASIN']=np.squeeze(item.ASIN) # use only the top result for now
            myPanda.loc[newRow,'SetName']=item.ItemAttributes.Title.text
            try:
                myPanda.loc[newRow,'SetNumber']=re.search(p,item.ItemAttributes.Title.text).group(0)
            except AttributeError:
                raise SetNumberError('No SetNumber found')
            break # after the 1st one
        return myPanda, myPanda.loc[newRow,'SetNumber'],newRow

# update from camelcamelcamel.com
def updateCamels(ASIN,myPanda,ASIN_row):

    today=datetime.today()
    tryurl =  "http://www.camelcamelcamel.com/product/"+ASIN # setup the url
    # print tryurl
    try:
        r = br.open(tryurl)
        print "Valid Response from camelcamelcamel" 
    except:
        print "exceptional camelcamelcamel"
        raise

    html = r.read()
    parsedHtml = BeautifulSoup(html,"lxml")     # parse with BeautifulSoup

    # get introduction date for set
    items = parsedHtml.find_all(attrs={"class": "smalltext grey"})
    for item in items:
        if 'since' in item.text:
            dt = item.text.lstrip().replace("* since", "").lstrip().replace('+ of the last 50 price changes','')
            myPanda.loc[ASIN_row,'introDate'] = pandas.to_datetime(dt[:12])

            # add time to now value
            try:
                myPanda.loc[ASIN_row,'time_to_now'] = (today - myPanda.loc[ASIN_row,"introDate"]).days
            except:
                pass
            break
                
    divs = parsedHtml.find_all("div", {"class":"yui3-u-1-2"}) # find the divs with the price information
    for div in divs:
        if 'Amazon' in div.h3.text: # get amazon prices
            temp_text = div.text.split('\n') # split by line    # print div.text
            temp_text = filter(None, temp_text) # remove empty
            for I in range(0,len(temp_text)):
                if 'Highest' in temp_text[I]:
                    myPanda.loc[ASIN_row,'highPrice_A'] = float(temp_text[I+1].replace("$", ""))
                    # print pandas.to_datetime(pandas.Series(temp_text[I+2].lstrip()))
                    # print temp_text[I+2]
                    # print time.strptime(temp_text[I+2].lstrip(), "%b %d, %Y")
                    myPanda.loc[ASIN_row,'highPriceDate_A'] = pandas.to_datetime(temp_text[I+2].lstrip())
                    # time.strptime(temp_text[I+2].lstrip(), "%b %d, %Y")
                if 'Lowest' in temp_text[I]:
                    myPanda.loc[ASIN_row,'lowPrice_A'] = float(temp_text[I+1].replace("$", ""))
                if 'Average' in temp_text[I]:
                    myPanda.loc[ASIN_row,'avgPrice_A'] = float(temp_text[I+1].replace("$", ""))
                if 'Current' in temp_text[I]: # current price or not in stock
                    try:
                        myPanda.loc[ASIN_row,'currentPrice_A'] = float(temp_text[I+1].replace("$", ""))
                    except ValueError:
                        myPanda.loc[ASIN_row,'currentPrice_A'] = np.nan # means not in stock
                        temp_text2 = divs[1].text.split('\n') # split by line
                        temp_text2 = filter(None, temp_text2)# remove empty
                        for J in range(0,len(temp_text2)):
                            if 'Price' in temp_text[J]:
                                myPanda.loc[ASIN_row,'selloutDate'] =  pandas.to_datetime(temp_text2[J+1].lstrip())

        # get 3rd party prices
        if '3rd Party New' in div.h3.text:
            temp_text = div.text.split('\n') # split by line
            temp_text = filter(None, temp_text)# remove empty 
            for I in range(0,len(temp_text)):
                if 'Highest' in temp_text[I]:
                    myPanda.loc[ASIN_row,'highPrice_3'] = float(temp_text[I+1].replace("$", ""))
                if 'Lowest' in temp_text[I]:
                    myPanda.loc[ASIN_row,'lowPrice_3'] = float(temp_text[I+1].replace("$", ""))
                if 'Average' in temp_text[I]:
                    myPanda.loc[ASIN_row,'avgPrice_3'] = float(temp_text[I+1].replace("$", ""))
                if 'Current' in temp_text[I]:
                    try: 
                        myPanda.loc[ASIN_row,'currentPrice_3'] = float(temp_text[I+1].replace("$", ""))
                    except ValueError:
                        myPanda.loc[ASIN_row,'currentPrice_3'] = np.nan # means not in stock
    return myPanda


def updateBrickSets(SetNumber,myPanda,ASIN_row):
    # compile regex's
    p_dd = re.compile(ur'\d.\d')
    p_nn = re.compile(ur'^[0-9]*')
    p_mm = re.compile(ur'\d minifigures')
    tryurl =  "http://brickset.com/sets/"+SetNumber # setup the url
    
    try:
        r = br.open(tryurl)
        print "Valid Response from brickset"
    except:
        print "exceptional brickset"
        raise

    html = r.read()
    
    parsedHtml = BeautifulSoup(html,'lxml')  # parse with BeautifulSoup
    myPanda.loc[ASIN_row,'Theme']=str(parsedHtml.find("dt",text="Theme").find_next_sibling("dd").text)
    myPanda.loc[ASIN_row,'introYear']=str(parsedHtml.find("dt",text="Year released").find_next_sibling("dd").text)
    myPanda.loc[ASIN_row,'pieces']=str(parsedHtml.find("dt",text="Pieces").find_next_sibling("dd").text)
    usd = parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text.find('$')
    myPanda.loc[ASIN_row,'retailPrice']=parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text[usd+1:]

    # how many want, how many have it
    for item in parsedHtml.find_all("li"):
        if " people own this set" in item.text:
            myPanda.loc[ASIN_row,'have_it']=re.search(p_nn,item.text).group(0)
        if " want this set" in item.text:
            myPanda.loc[ASIN_row,'want_it']=re.search(p_nn,item.text).group(0)

    try:
        myPanda.loc[ASIN_row,'minifigs']=int(parsedHtml.find("dt",text="Minifigs").find_next_sibling("dd").text)
    except:
        print "Couldn't find no. of minifigs"
    
    # brickset rating
    try: 
        text = str(parsedHtml.find_all("div", {"class":"rating"})[0])
        myPanda.loc[ASIN_row,'rating_B']=float(re.search(p_dd,text).group(0))
    except:
        # if this fails, lookup on amazon
        tryurl='http://www.amazon.com/exec/obidos/ASIN/'+ASIN
        r = br.open(tryurl)
        print "Getting rating from Amazon,Valid Response from Amazon"
        html = r.read()
        parsedHtml = BeautifulSoup(html,'lxml')  # parse with BeautifulSoup
        text = parsedHtml.find_all("span",{"class":"reviewCountTextLinkedHistogram"})
        splits = str(text[0]).split('\n')
        myPanda.loc[ASIN_row,'rating_B'] = float(re.search(p_dd,splits[0]).group(0))
        # also try to get minifigures #
        text = parsedHtml.find_all("div",{"id":"productDescription"})
        myPanda.loc[ASIN_row,'minifigs'] = float(re.search(p_mm,text[0].text).group(0)[:2])


    myPanda.loc[ASIN_row,'desirability']=float(myPanda.loc[ASIN_row,'want_it'])/float(myPanda.loc[ASIN_row,'have_it'])
    
    return myPanda


