
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

def am_search(SetName):
    # get only LEGO model number
    search_result = amazon_api.item_search('Toys', Keywords=SetName)
    try:
        for item in search_result:
            # use only the top result for now
            return item.ASIN.text
    except:
        return NaN


########### GET DATA PANDA ############

fn = '/Users/sharathbennur/Insights/Project/legoSet.pkl'
legos = pandas.read_pickle(fn)

########### GET DATA SQL ############

# con = mdb.connect('localhost', 'root', '', 'legoSet',charset='utf8')
# df = pandas.read_sql('SELECT * FROM legoSet', con)

########## GET DATA METHODS #############

legos.shape
cols = df.columns

# use only rows with current 3rd party prices
legos.head(10)
valid_3rdparty = legos[np.isfinite(legos.currentPrice_3)]
legos.head(10)



########### Set to compare for ############


## test case
name = raw_input('which LEGO set do you want?')
# get ASIN
ASIN = am_search(name)

# Fills ASIN,, SetNumber, SetName
legoSets = amLookupASIN(ASIN,legoSets)
# get data from c3.com
legoSets = getCamels(ASIN, legoSets)
# get data from BS
legoSets = getBrickSets(SetNumber,legoSets)
legoSets


fn = '/Users/sharathbennur/Insights/Project/legoSet.pkl'
legoSets.to_pickle(fn)  # where to save it, usually as a .pkl

## Then you can load it back using:
# df = pd.load(fn)

# new row
name = 'LEGO LOTR Battle at The Black Gate 79007'
ASIN = am_search(name) # get ASIN
# Add a new row to the data
legoSets.loc[len(legoSets)] = np.nan
legoSets = amLookupASIN(ASIN,legoSets) # fill in values from amazon
SetNumber=legoSets.loc[len(legoSets)-1,'SetNumber'] # get set number

# fill in from camelcamelcamel
legoSets = getCamels(ASIN, legoSets)
# fill in from brickset
legoSets = getBrickSets(SetNumber,legoSets)
# fill in from ebay
legoSets


######## Brickset SET and THEME FILLER ###########
Done = ['Advanced-Models','Adventurers','Aquazone','Architecture','Atlantis','Baby','Basic',
         'Batman','Belville','Boats','Bionicle','Cars','Castle','City','Creator','DC-Comics-Super-Heroes',
         'Dino','Disney-Princess','Duplo']
Repeat = ['Education','Star-Wars']
Themes = ['Elves','Explore','Friends','Games','Harry-Potter',
          'HERO-Factory','Ideas','Indiana-Jones','Island-Xtreme-Stunts','Jack-Stone','Juniors','Jurassic-World',
         'Legends-of-Chima','LEGOLAND','Make-and-Create','Marvel-Super-Heroes','Master-Builder-Academy',
         'Mindstorms','Minecraft','Mixels','Monster-Fighters','Ninjago','Pharaohs-Quest','Pirates',
          'Pirates-of-the-Caribbean','Power-Miners','Power-Functions','Prince-of-Persia','Quatro',
         'Racers','Rock-Raiders','Scooby-Doo','Seasonal','Serious-Play','Space','Speed-Champions','Spider-Man',
         'SpongeBob-SquarePants','Sports','Sports','Studios','Technic','Teenage-Mutant-Ninja-Turtles',
         'The-Hobbit','The-LEGO-Movie','The-Lone-Ranger','The-Lord-of-the-Rings','The-Simpsons','Town',
         'Toy-Story','Trains','Ultra-Agents','Vikings','World-City','World-Racers']

testTheme = 'Star-Wars'

for theme in Themes:
    fillDB(theme,legoSets)
    fn = '/Users/sharathbennur/Insights/Project/legoSet2.pkl'
    legoSets.to_pickle(fn)  # where to save it, usually as a .pkl


legoSets


################## C3 Scratch Pad Code

# In[ ]:

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

# SetNumber
# tryurl =  "http://brickset.com/sets/"+SetNumber # setup the url
# # print tryurl
# response = urllib2.urlopen(tryurl)
# html = response.read()
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
    

# parsedHtml.find('rating').a.text
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


################ Ebay Scratch Pad

# In[ ]:

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

con = mdb.connect('localhost', 'root', '', 'legoSet',charset='utf8')
legoSets.to_sql(con=con, name='legoSets', if_exists='replace', flavor='mysql', index=False)
# legoSets.to_sql(con=con, name='legoSet', if_exists='replace', flavor='mysql', index=False)
# df = pandas.read_sql('SELECT * FROM legoSet', con)
# df
# # test section to try sql
# df = pandas.read_sql('SELECT * FROM legoSet', con, index_col=None)
# df

########### To get data from SQL database

# In[ ]:

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



