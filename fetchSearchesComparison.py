# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 00:50:03 2019

@author: Arthur
"""

import bs4
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from difflib import SequenceMatcher

chrome_options = Options()
chrome_options.add_argument("--window-size=1920,1080")

baseUrl_fr="https://www.autotrader.co.uk/car-search?sort=relevance&radius=1500&postcode=e148hl&onesearchad=Used&onesearchad=Nearly%20New&onesearchad=New&keywords=left%20hand%20drive%20lhd&page="
baseUrl_uk="https://www.autotrader.co.uk/car-search?sort=relevance&radius=1500&postcode=e148hl&onesearchad=Used&onesearchad=Nearly%20New&onesearchad=New&keywords=left%20hand%20drive%20lhd&page="

miles_to_km = 1.60934
epsilon_km = 50000
epsilon_years = 2
maxPrice_uk = 10000.0

path="C:/dev/carScraping/data"

autotrader = pd.DataFrame(columns=["title_uk","brand_uk","model_uk","price_uk (gbp)","year_uk","kilometrage_uk","fuelType_uk","bodyType_uk","gearBox_uk","link_uk","keep_uk"])
leparking = pd.DataFrame(columns=["brand_fr","model_fr","price_fr (eur)","year_fr","kilometrage_fr","fuelType_fr","gearBox_fr","link_fr"])
final_result = pd.DataFrame(columns=["title_uk","brand_uk","model_uk","price_uk (gbp)","year_uk","kilometrage_uk","fuelType_uk","bodyType_uk","gearBox_uk","link_uk","brand_fr","model_fr","price_fr (eur)","year_fr","kilometrage_fr","fuelType_fr","gearBox_fr","link_fr"])

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

#%%
k=0
l=0
print("Autotrader: starting")
for j in range(1,6):
    print("page ",j)
    url = baseUrl_uk + str(j)
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    li_box = soup.find_all("li", {"class":"search-page__result"})
    
    for i in range(len(li_box)):
        try:
            price = float(li_box[i].find_all("div",{'class':'vehicle-price'})[0].get_text().replace("£","").replace(",",""))
            title = li_box[i].find_all("h2",{'class':'listing-title title-wrap'})[0].get_text().replace("\n","")
            brand = title.split(" ")[0]
            model = title.split(" ")[1] + " " + title.split(" ")[2]
            listing = li_box[i].find_all("ul",{'class':"listing-key-specs "})[0].get_text().split("\n")
            for e in listing:
                if "miles" in e:
                    mileage = float(e.split(" ")[0].replace(",",""))
            year = int(listing[1][0:4])
            kilometrage = mileage * miles_to_km
            bodyType = listing[2]
            fuelType = listing[len(listing)-1]
            gearBox = listing[len(listing)-2]
            link = "https://www.autotrader.co.uk/classified/advert/"+li_box[i].find_all("a",{"class":"js-click-handler listing-fpa-link tracking-standard-link"})[0]["href"].split("/")[3].split("?")[0]
            autotrader.loc[l] = [title,brand,model,price,year,kilometrage,fuelType,bodyType,gearBox,link,False]
            l=l+1
        except:
            print("error ",i)
   
    links = autotrader["link_uk"]
    keywords = ["lhd","left hand drive", "left-hand drive", "left-hand-drive"]
    
    for i in range(len(links)):
        try:
            link = links[i]
            keep = False
            driver = webdriver.Chrome("C:/dev/chromedriver.exe",chrome_options=chrome_options)
            driver.get(link)
            html = driver.page_source
            soup = bs4.BeautifulSoup(html, 'lxml')
            description = soup.find_all("p", {"class":"truncated-text fpa__description atc-type-picanto"})[0].get_text()
            title = soup.find_all("h1",{"class":"advert-heading__title atc-type-insignia atc-type-insignia--medium"})[0].get_text()
            for word in keywords:
                if word in title or word in description:
                    keep = True
            autotrader["keep_uk"][k] = keep
            k=k+1
            time.sleep(10)
            #driver.close()
        except:
            print("Did not work for ",i)
    driver.close()

autotrader[autotrader["keep_uk"]==True].to_csv(path+'data/scrapedCarInfo.csv',sep=";")
autotraderToInvestigate = autotrader[autotrader["keep_uk"]==True]
print("Autotrader: finished")
print("leparking: starting")
n=0
for j in range(len(autotraderToInvestigate)):
    row = autotraderToInvestigate.iloc[j]
    keywords = row["brand_uk"] + " " +row["model_uk"]
    url = "http://www.leparking.fr/#!/voiture-occasion/"+keywords.replace(" ", "-") + \
        ".html%3Fid_pays%3D18%26slider_km%3D"+str(int(row["kilometrage_uk"]-epsilon_km))+"%7C"+str(int(row["kilometrage_uk"]+epsilon_km))+\
        "%26slider_millesime%3D"+str(row['year_uk']-epsilon_years)+"%7C"+str(row['year_uk']+epsilon_years)
    driver = webdriver.Chrome("C:/dev/chromedriver.exe",chrome_options=chrome_options)
    driver.get(url)
    html = driver.page_source
    soup = bs4.BeautifulSoup(html, 'lxml')
    k = 0
    li_box = soup.find_all("section", {"class":"clearfix"})
    for i in range(len(li_box)):
        try:
            title = li_box[i].find_all("div",{"class":"block-title-list"})[0]
            link = "http://www.leparking.fr/"+li_box[i].find_all("a",{"class":"external btn-plus no-partenaire-btn"})[0]['href']
            brand = title.find("span",{"class":"title-block brand"}).get_text()
            model = title.find("span",{"class":"sub-title title-block"}).get_text()
            price = li_box[i].find_all("p",{"class":"prix"})[0].get_text().split(' ')
            p=''
            for e in price:
                if e!=' ':
                    p+=e
            price = float(p.replace('\n', '').replace('€',''))
            bandeau = li_box[i].find_all("ul",{"class":"info clearfix"})[0].get_text().split("\n")
            l=[]
            for e in bandeau:
                if e != '':
                    l.append(e)
            year = l[2]
            kilometrage = l[1].split(" ")[:-1]
            kilometrage=int(kilometrage[0]+kilometrage[1])
            fuelType = l[0]
            gearBox = l[3]
            if similar(brand,row["brand_uk"])>0.5:
                leparking.loc[k] = [brand,model,price,year,kilometrage,fuelType,gearBox,link]
            k+=1
        except:
            print("error ",i)
    driver.close()
   
    for r in range(len(leparking)):
        c = pd.concat([row[:10], leparking.iloc[r]], axis=0).reset_index()
        c.columns=[0,1]
        final_result.loc[n] = c[1].tolist()
        n+=1
    
final_result = final_result.drop_duplicates()
final_result = final_result[final_result['price_uk (gbp)']<= maxPrice_uk]
final_result.to_csv(path+'data/final_comparison.csv',sep=";")

print("leparking: finished")
