
# coding: utf-8

# In[2]:

# SETUP

from pandas.io import sql
import pymysql as mdb
from datetime import datetime
import random
import numpy as np
import pandas as pd
from brickset import *
from scipy import stats, integrate
from amazonproduct import API
from bs4 import BeautifulSoup
import lxml
import matplotlib.pyplot as plt
import urllib2
from bs4 import BeautifulSoup
import itertools
import time
from time import mktime
import re
import seaborn


# In[3]:

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


# In[4]:

fn = '/Users/sharathbennur/Insights/Project/legoSet.pkl'
legos = pd.read_pickle(fn)
print legos.shape
legos.columns


# In[5]:

legos.dtypes


# In[6]:

legos.loc[0,"currentPrice_A"]


# In[7]:

legos.dtypes


# In[8]:

# print legos["currentPrice_3"].head(10)
# convert objects to numeric
k,v = legos.shape
priceA = np.empty((k,1))
price3 = np.empty((k,1))
wi = np.empty((k,1))
hi = np.empty((k,1))
HpriceA = np.empty((k,1))
pie = np.empty((k,1))

for I in range(0,k):
    price3[I] = float(legos.loc[I,"currentPrice_3"])
    priceA[I] = float(legos.loc[I,"currentPrice_A"])
    wi[I] = float(legos.loc[I,"want_it"])
    hi[I] = float(legos.loc[I,"have_it"])
    pie[I] = float(legos.loc[I,"pieces"])

legos["currentPrice_3"] = price3
legos["currentPrice_A"] = priceA
legos["want_it"] = wi
legos["have_it"] = hi
legos["pieces"] = pie
legos.dtypes


# In[9]:

# fixing the mess that is the retailPrice

# print legos.loc[40,"retailPrice"]

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


# In[10]:

# sanity check to make sure all the dates are the correct format

print legos.loc[1,"highPriceDate_A"]
print legos.loc[1,"introDate"]
print legos.loc[1,"highPriceDate_A"] - legos.loc[1,"introDate"]


# In[11]:

legos.dtypes


# In[12]:

legos.shape

# current prices
legos["price_increase_3"] = legos["currentPrice_3"]/legos["retailPrice"]
legos["price_increase_A"] = legos["currentPrice_A"]/legos["retailPrice"]

# high prices
legos["h_price_increase_3"] = legos["highPrice_3"]/legos["retailPrice"]
legos["h_price_increase_A"] = legos["highPrice_A"]/legos["retailPrice"]
get_ipython().magic(u'matplotlib inline')


# In[13]:

thirdP_LegoPrices = legos["price_increase_3"].values
highThirdP_LegoPrices = legos["h_price_increase_3"].values

amazon_LegoPrices = legos["price_increase_A"].values
highAmazon_LegoPrices = legos["h_price_increase_A"].values

plt.hist(thirdP_LegoPrices, bins=20, range=(-1, 5))


# In[14]:

plt.hist(thirdP_LegoPrices, bins=20, range=(-1, 5))
plt.hist(h_third_partyLegos, bins=20, range=(-1, 5),alpha=0.5)


# In[15]:

plt.hist(highAmazon_LegoPrices, bins=20, range=(-1, 5))


# In[16]:

plt.hist(amazon_LegoPrices, bins=20, range=(-1, 5))
plt.hist(highAmazon_LegoPrices, bins=20, range=(-1, 5),alpha=0.5)


# In[17]:

legos.plot(kind='scatter',x='pieces',y='h_price_increase_A')


# In[18]:

legos.plot(kind='scatter',x='pieces',y='h_price_increase_3')


# In[20]:

np.unique(legos["Theme"])


# In[21]:

Theme = legos["Theme"]
h_price_increase_3 = legos["h_price_increase_3"]
seaborn.stripplot(x="Theme", y="h_price_increase_3", data=legos);


# In[22]:

h_price_increase_A = legos["h_price_increase_A"]
seaborn.stripplot(x="Theme", y="h_price_increase_A", data=legos);


# In[23]:

legos['minifigs'].fillna(0, inplace=True)
legos['pieces'].fillna(0, inplace=True)

legos['pieces'].head()


# In[24]:

legos.plot(kind='scatter',x='minifigs',y='h_price_increase_A')



# In[25]:

legos.plot(kind='scatter',x='minifigs',y='h_price_increase_3')


# In[49]:

import statsmodels.formula.api as sm

legos_clean = legos[np.isfinite(legos['h_price_increase_A'])]

model = sm.ols(formula='h_price_increase_A ~ minifigs', data=legos_clean)
fitted = model.fit()
print fitted.summary()


# In[55]:

# NOT WORKING FOR NOW ###
import matplotlib as mpl
import matplotlib.pyplot as plt

seaborn.lmplot(x="h_price_increase_A", y="pieces", data=legos_clean);


# In[59]:

seaborn.lmplot(x="h_price_increase_3", y="pieces", data=legos_clean);


# In[58]:

seaborn.lmplot(x="h_price_increase_A", y="minifigs", data=legos_clean);


# In[60]:

seaborn.lmplot(x="h_price_increase_3", y="minifigs", data=legos_clean);


# In[66]:

legos_clean['resale_bump'] = legos_clean['h_price_increase_3']/legos_clean['h_price_increase_A']
# legos_clean['resale_bump'].head()

seaborn.lmplot(x="resale_bump", y="pieces", data=legos_clean);
seaborn.lmplot(x="resale_bump", y="minifigs", data=legos_clean);


# In[ ]:



