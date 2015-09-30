
# coding: utf-8

# In[ ]:

# Main function for getting data and computing the model

from pandas.io import sql
import pymysql as mdb
from datetime import datetime
import random
import numpy as np
import pandas
from brickset import *
from amazonproduct import API
from bs4 import BeautifulSoup
# from html5lib import *
import lxml
# import matplotlib.pyplot
import urllib2
from bs4 import BeautifulSoup
# import matplotlib.pyplot as plt
import itertools
import time
from time import mktime
import re

########### DATA PANDA SETUP ############

cols = ['SetNumber','SetName','Theme','ASIN','retailPrice','currentPrice_A',
    'highPrice_A','lowPrice_A','avgPrice_A','highPrice_3','lowPrice_3','avgPrice_3',
    'introDate','introYear','selloutDate','highPriceDate_A','pieces','minifigs','rating_B',
       'want_it','have_it']

legoSets = pandas.DataFrame(data=np.zeros((0,len(cols))), columns=cols)

########## GET DATA METHODS #############

amazon_api = API(locale='us') # setup amazon API
brickset_client = brickset() # setup the brickset API client

#### ALL ITEM SEARCH
def am_search(SetName):
    # get only LEGO model number
    search_result = amazon_api.item_search('Toys', Keywords=SetName)
    try:
        for item in search_result:
            # use only the top result for now
            return item.ASIN.text
    except:
        return NaN


#### function call that searches & verifies the LEGO set and sets up the LEGO object
def amLookupASIN(iASIN,myPanda):
    p = re.compile(ur'[0-9]{3,10}')
    lookUP = amazon_api.item_lookup(iASIN)
    for item in lookUP.Items.Item:
        myPanda.loc[len(legoSets)-1,'ASIN']=np.squeeze(item.ASIN) # use only the top result for now
        myPanda.loc[len(legoSets)-1,'SetName']=item.ItemAttributes.Title.text
        myPanda.loc[len(legoSets)-1,'SetNumber']=re.search(p,item.ItemAttributes.Title.text).group(0)
    return myPanda

###### CamelCamelCamel Scraping Function


def getCamels(ASIN,myPanda):
    tryurl =  "http://www.camelcamelcamel.com/product/"+ASIN # setup the url
    # print tryurl
    response = urllib2.urlopen(tryurl)
    html = response.read()

    parsedHtml = BeautifulSoup(html,"lxml")     # parse with BeautifulSoup
    # print parsedHtml

    # get introduction date for set
    items = parsedHtml.find_all(attrs={"class": "smalltext grey"})
    for item in items:
        if 'since' in item.text:
            dt = item.text.lstrip().replace("* since", "").replace('+ of the last 50 price changes','')
            myPanda.loc[len(legoSets)-1,'introDate'] = pandas.to_datetime(dt)
            break
                
    divs = parsedHtml.find_all("div", {"class":"yui3-u-1-2"}) # find the divs with the price information
    for div in divs:
        if 'Amazon' in div.h3.text: # get amazon prices
            temp_text = div.text.split('\n') # split by line    # print div.text
            temp_text = filter(None, temp_text) # remove empty
            for I in range(0,len(temp_text)):
                if 'Highest' in temp_text[I]:
                    myPanda.loc[len(legoSets)-1,'highPrice_A'] = float(temp_text[I+1].replace("$", ""))
                    # print pandas.to_datetime(pandas.Series(temp_text[I+2].lstrip()))
                    # print temp_text[I+2]
                    # print time.strptime(temp_text[I+2].lstrip(), "%b %d, %Y")
                    myPanda.loc[len(legoSets)-1,'highPriceDate_A'] = pandas.to_datetime(temp_text[I+2].lstrip())
                    # time.strptime(temp_text[I+2].lstrip(), "%b %d, %Y")
                if 'Lowest' in temp_text[I]:
                    myPanda.loc[len(legoSets)-1,'lowPrice_A'] = float(temp_text[I+1].replace("$", ""))
                if 'Average' in temp_text[I]:
                    myPanda.loc[len(legoSets)-1,'avgPrice_A'] = float(temp_text[I+1].replace("$", ""))
                if 'Current' in temp_text[I]: # current price or not in stock
                    try:
                        myPanda.loc[len(legoSets)-1,'currentPrice_A'] = float(temp_text[I+1].replace("$", ""))
                    except ValueError:
                        myPanda.loc[len(legoSets)-1,'currentPrice_A'] = 'NaN' # means not in stock
                        temp_text2 = divs[1].text.split('\n') # split by line
                        temp_text2 = filter(None, temp_text2)# remove empty
                        for J in range(0,len(temp_text2)):
                            if 'Price' in temp_text[J]:
                                myPanda.loc[len(legoSets)-1,'selloutDate'] =  pandas.to_datetime(temp_text2[J+1].lstrip())

        # get 3rd party prices
        if '3rd' in div.h3.text:
            temp_text = div.text.split('\n') # split by line
            temp_text = filter(None, temp_text)# remove empty 
            for I in range(0,len(temp_text)):
                if 'Highest' in temp_text[I]:
                    myPanda.loc[len(legoSets)-1,'highPrice_3'] = float(temp_text[I+1].replace("$", ""))
                if 'Lowest' in temp_text[I]:
                    myPanda.loc[len(legoSets)-1,'lowPrice_3'] = float(temp_text[I+1].replace("$", ""))
                if 'Average' in temp_text[I]:
                    myPanda.loc[len(legoSets)-1,'avgPrice_3'] = float(temp_text[I+1].replace("$", ""))
                if 'Current' in temp_text[I]:
                    try: 
                        myPanda.loc[len(legoSets)-1,'currentPrice_3'] = float(temp_text[I+1].replace("$", ""))
                    except ValueError:
                        myPanda.loc[len(legoSets)-1,'currentPrice_3'] = 'NaN' # means not in stock
    return myPanda


def fillCamels(myPanda):
    # preprocess to clean up
    k,v = myPanda.shape
    price3 = np.empty((k,1))
    for I in range(0,k):
        price3[I] = float(myPanda.loc[I,"currentPrice_3"])
    myPanda["currentPrice_3"] = price3
    # get index
    missing = myPanda["currentPrice_3"].values
    li = np.squeeze(np.where(np.isnan(missing)))
    for I in li:
        time.sleep(8)
        print myPanda.loc[I,'SetName']
        print myPanda.loc[I,'ASIN']
        ASIN = myPanda.loc[I,'ASIN']
        print ASIN
        tryurl =  "http://www.camelcamelcamel.com/product/"+ASIN # setup the url
        # print tryurl
        response = urllib2.urlopen(tryurl)
        html = response.read()

        parsedHtml = BeautifulSoup(html,"lxml")     # parse with BeautifulSoup
        # print parsedHtml

        # get introduction date for set
        items = parsedHtml.find_all(attrs={"class": "smalltext grey"})
        for item in items:
            if 'since' in item.text:
                dt = item.text.lstrip().replace("* since", "").lstrip()[:12]
                print dt
                myPanda.loc[I,'introDate'] = pandas.to_datetime(dt)
                break
                    
        divs = parsedHtml.find_all("div", {"class":"yui3-u-1-2"}) # find the divs with the price information
        for div in divs:
            if 'Amazon' in div.h3.text: # get amazon prices
                temp_text = div.text.split('\n') # split by line    # print div.text
                temp_text = filter(None, temp_text) # remove empty
                for I in range(0,len(temp_text)):
                    if 'Highest' in temp_text[I]:
                        myPanda.loc[I,'highPrice_A'] = float(temp_text[I+1].replace("$", ""))
                        # print pandas.to_datetime(pandas.Series(temp_text[I+2].lstrip()))
                        # print temp_text[I+2]
                        # print time.strptime(temp_text[I+2].lstrip(), "%b %d, %Y")
                        myPanda.loc[I,'highPriceDate_A'] = pandas.to_datetime(temp_text[I+2].lstrip())
                        # time.strptime(temp_text[I+2].lstrip(), "%b %d, %Y")
                    if 'Lowest' in temp_text[I]:
                        myPanda.loc[I,'lowPrice_A'] = float(temp_text[I+1].replace("$", ""))
                    if 'Average' in temp_text[I]:
                        myPanda.loc[I,'avgPrice_A'] = float(temp_text[I+1].replace("$", ""))
                    if 'Current' in temp_text[I]: # current price or not in stock
                        try:
                            myPanda.loc[I,'currentPrice_A'] = float(temp_text[I+1].replace("$", ""))
                        except ValueError:
                            myPanda.loc[I,'currentPrice_A'] = 'NaN' # means not in stock
                            temp_text2 = divs[1].text.split('\n') # split by line
                            temp_text2 = filter(None, temp_text2)# remove empty
                            for J in range(0,len(temp_text2)):
                                if 'Price' in temp_text[J]:
                                    myPanda.loc[I,'selloutDate'] =  pandas.to_datetime(temp_text2[J+1].lstrip())

            # get 3rd party prices
            if '3rd' in div.h3.text:
                temp_text = div.text.split('\n') # split by line
                temp_text = filter(None, temp_text)# remove empty 
                for I in range(0,len(temp_text)):
                    if 'Highest' in temp_text[I]:
                        myPanda.loc[I,'highPrice_3'] = float(temp_text[I+1].replace("$", ""))
                    if 'Lowest' in temp_text[I]:
                        myPanda.loc[I,'lowPrice_3'] = float(temp_text[I+1].replace("$", ""))
                    if 'Average' in temp_text[I]:
                        myPanda.loc[I,'avgPrice_3'] = float(temp_text[I+1].replace("$", ""))
                    if 'Current' in temp_text[I]:
                        try: 
                            myPanda.loc[I,'currentPrice_3'] = float(temp_text[I+1].replace("$", ""))
                        except ValueError:
                            myPanda.loc[I,'currentPrice_3'] = 'NaN' # means not in stock
    return myPanda

#### Brickset Scraping Function

# brickset search

def getBrickSets(SetNumber,myPanda):
    p_dd = re.compile(ur'\d.\d')
    p_nn = re.compile(ur'^[0-9]*')
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
    


############## GET ALL SETS FOR CURRENT THEME ######################

def fillDB(Theme,myPanda):
    getMore = True
    N=0
    p_nn = re.compile(ur'^[0-9]*')
    while getMore:
        N=N+1; # increment page number
        # continue or not?
        tryurl =  "http://brickset.com/sets/theme-"+Theme+"/page-"+str(N) # setup the url
        print tryurl
        response = urllib2.urlopen(tryurl)
        html = response.read()
        parsedHtml = BeautifulSoup(html,'lxml')  # parse with BeautifulSoup
        # make sure page is valid
        items = parsedHtml.find_all("article", {"class":"set"}) # individual set name
        if items:
            divs = parsedHtml.find_all("div", {"class":"meta"}) # individual set name
            for div in divs: # for each item found
                print div.a.text
                SN = re.search(p_nn,div.a.text).group(0) # get set number
                if SN not in str(myPanda.SetNumber): # if we don't have the set, get it
                    try:
                        name = div.a.text
                        ASIN = am_search(name) # get ASIN
                        print ASIN
                        if (isinstance(ASIN, str)) or (ASIN is not None):
                            time.sleep(5)
                            # if its valid, add a new line
                            myPanda.loc[len(myPanda)] = np.nan
                            myPanda = amLookupASIN(ASIN,myPanda)
                            SetNumber=myPanda.loc[len(myPanda)-1,'SetNumber']
                            # fill in from camelcamelcamel
                            myPanda = getCamels(ASIN, myPanda)
                            # fill in from brickset
                            myPanda = getBrickSets(SetNumber,myPanda)
                    except: # if it doesnt work, move to the next item
                        pass
                else:
                    print 'Already in database'
        else: # if no more valid pages
            getMore = False
    # at the end of each theme, save the data
    fn = '/Users/sharathbennur/Insights/Project/legoSet.pkl'
    myPanda.to_pickle(fn)  # where to save it, usually as a .pkl
    print 'saved panda to '+fn


######## Brickset SET and THEME FILLER ###########
def getData():
    Done = ['Advanced-Models','Adventurers','Aquazone','Architecture','Atlantis','Baby','Basic',
         'Batman','Belville','Boats','Bionicle','Cars','Castle','City','Creator','DC-Comics-Super-Heroes',
         'Dino','Disney-Princess','Duplo','Elves','Explore','Friends','Games','Harry-Potter',
          'HERO-Factory','Ideas','Indiana-Jones','Island-Xtreme-Stunts','Jack-Stone','Juniors','Jurassic-World',
         'Legends-of-Chima','LEGOLAND','Make-and-Create','Marvel-Super-Heroes','Master-Builder-Academy',
         'Mindstorms','Minecraft','Mixels','Monster-Fighters','Ninjago','Pharaohs-Quest','Pirates',
          'Pirates-of-the-Caribbean','Power-Miners','Power-Functions','Prince-of-Persia','Quatro',
         'Racers','Rock-Raiders','Scooby-Doo','Seasonal','Serious-Play','Space','Speed-Champions','Spider-Man',
         'SpongeBob-SquarePants','Sports','Sports','Studios']
    Repeat = ['Education','Star-Wars']
    Themes = ['Technic','Teenage-Mutant-Ninja-Turtles',
             'The-Hobbit','The-LEGO-Movie','The-Lone-Ranger','The-Lord-of-the-Rings','The-Simpsons','Town',
             'Toy-Story','Trains','Ultra-Agents','Vikings','World-City','World-Racers']

    for theme in Themes:
        fillDB(theme,legoSets)
        fn = '/Users/sharathbennur/Insights/Project/legoSet2.pkl'
        legoSets.to_pickle(fn)  # where to save it, usually as a .pkl

    print legoSets.shape

################## C3 Scratch Pad Code

def C3_scratch():
    ASIN = 'B00C9X59UM'
    tryurl =  "http://www.camelcamelcamel.com/product/"+ASIN # setup the url
    # print tryurl
    #response = urllib2.urlopen(tryurl)
    #html = response.read()

    parsedHtml = BeautifulSoup(html,"lxml")  # parse with BeautifulSoup
    items = parsedHtml.find_all(attrs={"class": "smalltext grey"})
    for item in items:
        if 'since' in item.text:
            print pandas.to_datetime(item.text.lstrip().replace("* since", "").replace('+ of the last 50 price changes',''))
            #myPanda.loc[len(legoSets)-1,'introDate'] =  pandas.to_datetime(item.text.lstrip)
    # divs = parsedHtml.find_all("div", {"class":"yui3-u-1-2"}) # find the divs with the price information
    # temp_text = divs[0].text.split('\n') # split by line  # print div.text
    # temp_text = filter(None, temp_text) # remove empty
    # print temp_text
    # for J in range(0,len(temp_text)): 
    #    if 'Highest' in temp_text[J]:             # get the last time it was in stock
    #        print  time.strptime(temp_text[J+2].lstrip(), "%b %d, %Y")


############## Brickset Scraper Scratch Pad 

# In[ ]:
def BS_Scratch():
    SetNumber
    tryurl =  "http://brickset.com/sets/"+SetNumber # setup the url
    # print tryurl
    response = urllib2.urlopen(tryurl)
    html = response.read()
    p_dd = re.compile(ur'\d.\d')
    p_nn = re.compile(ur'^[0-9]*')
    parsedHtml = BeautifulSoup(html,'lxml')  # parse with BeautifulSoup
    # print parsedHtml.find("dt",text="Theme").find_next_sibling("dd").text
    # text = str(parsedHtml.find_all("div", {"class":"rating"})[0])
    # print float(re.search(p_dd,text).group(0))
    for item in parsedHtml.find_all("li"):
        if " people own this set" in item.text:
            print re.search(p_nn,item.text).group(0)
        if " want this set" in item.text:
            print re.search(p_nn,item.text).group(0)
    

    parsedHtml.find('rating').a.text
    print parsedHtml.find("dt",text="Theme").find_next_sibling("dd").text
    print parsedHtml.find("dt",text="Year released").find_next_sibling("dd").text
    print parsedHtml.find("dt",text="Pieces").find_next_sibling("dd").text
    usd = parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text.find('$')
    print parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text[usd+1:]


    tryurl =  "http://brickset.com/sets/"+SetNumber # setup the url
    print tryurl
    response = urllib2.urlopen(tryurl)
    html = response.read()
    parsedHtml = BeautifulSoup(html,'lxml')  # parse with BeautifulSoup

    print parsedHtml.find("dt",text="Theme").find_next_sibling("dd").text
    print parsedHtml.find("dt",text="Year released").find_next_sibling("dd").text
    print parsedHtml.find("dt",text="Pieces").find_next_sibling("dd").text
    usd = parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text.find('$')
    print parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text[usd+1:]


################ Ebay Scratch Pad

def eBay_scratch():
    import datetime
    from ebaysdk.finding import Connection

    api = Connection(appid='SubhashB-f237-485e-9a38-318aa7e72eee')
    response = api.execute('findItemsAdvanced', {'keywords': 'legos'})

    assert(response.reply.ack == 'Success')
    assert(type(response.reply.timestamp) == datetime.datetime)
    assert(type(response.reply.searchResult.item) == list)

    item = response.reply.searchResult.item[0]
    assert(type(item.listingInfo.endTime) == datetime.datetime)
    assert(type(response.dict()) == dict)

########### SQL DB SETUP ############

# 'SetNumber','SetName','Theme','ASIN','retailPrice','currentPrice_A',
#     'highPrice_A','lowPrice_A','avgPrice_A','highPrice_3','lowPrice_3','avgPrice_3',
#     'introDate','introYear','selloutDate','highPriceDate_A','pieces','minifigs','rating_B',
#        'want_it','have_it'

# CREATE TABLE legoSets 
# (SetNumber VARCHAR(10), 
# SetName TEXT, 
# Theme VARCHAR(25), 
# ASIN VARCHAR(25), 
# retailPrice FLOAT(8,2),
# highPrice_A FLOAT(8,2),
# lowPrice_A FLOAT(8,2),
# avgPrice_A FLOAT(8,2),
# highPrice_3 FLOAT(8,2),
# lowPrice_3 FLOAT(8,2),
# avgPrice_3 FLOAT(8,2),
# introDate  TEXT,
# introYear TEXT,
# selloutDate TEXT,
# highPriceDate_A TEXT,
# pieces SMALLINT,
# minifigs TINYINT,
# rating_B TINYINT,
# want_it SMALLINT,
# have_it SMALLINT);

# CREATE TABLE Themes (venue_id INT(12),  venue_name LONGTEXT, category MEDIUMTEXT, fsq_url MEDIUMTEXT, address MEDIUMTEXT, state TEXT, city TEXT, latitude DOUBLE(12,8) NOT NULL, longitude DOUBLE(12,8) NOT NULL, PRIMARY KEY (venue_id));
# CREATE TABLE untap_beer (beer_id INT(12), beer_name MEDIUMTEXT, brewery_name MEDIUMTEXT, brewery_id INT(12), brewery_slug MEDIUMTEXT, style MEDIUMTEXT, abv FLOAT(3,1), PRIMARY KEY (beer_ID))

def conMySQL():
    con = mdb.connect('localhost', 'root', '', 'legoSet',charset='utf8')
    legoSets.to_sql(con=con, name='legoSet', if_exists='replace', flavor='mysql', index=False)
    # legoSets.to_sql(con=con, name='legoSet', if_exists='replace', flavor='mysql', index=False)
    # df = pandas.read_sql('SELECT * FROM legoSet', con)
    # df
    # # test section to try sql
    # df = pandas.read_sql('SELECT * FROM legoSet', con, index_col=None)
    # df


    # GET SQL DATA SECTION
    # make connection
    conn = mdb.connect(host="localhost", user="root", passwd="", db="legoSets")
    # connect
    cursor = conn.cursor()
    # pick data
    cursor.execute('select Name, Continent, Population, LifeExpectancy, GNP from Country');
    # get data
    rows = cursor.fetchall()
    # put in panda
    df = pd.DataFrame( [[ij for ij in i] for i in rows] )

############## RANDOM CODE ################

# print parsedHtml.find("dt",text="Theme").find_next_sibling("dd").text
# print parsedHtml.find("dt",text="Year released").find_next_sibling("dd").text
# print parsedHtml.find("dt",text="Pieces").find_next_sibling("dd").text
# usd = parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text.find('$')
# print parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text[usd+1:]


# tryurl =  "http://brickset.com/sets/"+SetNumber # setup the url
# print tryurl
# response = urllib2.urlopen(tryurl)
# html = response.read()
# parsedHtml = BeautifulSoup(html,'lxml')  # parse with BeautifulSoup

# print parsedHtml.find("dt",text="Theme").find_next_sibling("dd").text
# print parsedHtml.find("dt",text="Year released").find_next_sibling("dd").text
# print parsedHtml.find("dt",text="Pieces").find_next_sibling("dd").text
# usd = parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text.find('$')
# print parsedHtml.find("dt",text="RRP").find_next_sibling("dd").text[usd+1:]



