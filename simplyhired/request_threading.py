"""A module for threading requests and storing their results. 

This module currently provides one class - `RequestInfoThread`. It is meant to help
issue get requests using threading, but avoid creating a new connection to a db for
each thread. It does this by storing the results of the get request as an attribute
on the class. 
"""

import sys
import os
wd = os.path.abspath('.')
sys.path.append(wd + '/../')
import datetime
import re
import pytz
from threading import Thread
from requests import get
from bs4 import BeautifulSoup
from general_utilities.parsing_utilities import find_visible_texts

class RequestInfoThread(Thread): 
    """Threading based class to issue get requests and store the results.  
    
    RequestInfoThread issues a get request on the href from an inputted row (which
    represents a job), after grabbing all of its relevant information. The 
    motivation for using a class instead of simply passing a function to ThreadPool
    was to avoid creating a new connection with the database (here Mongo) for each
    get request (this would most likely overwhelm the comp with threads).

    Args: 
    ----
        job_result: bs4.BeautifulSoup object.
        job_title: str
        job_location: str
    """

    def __init__(self, job_result, job_title, job_location): 
        super(RequestInfoThread, self).__init__()
        self.job_result = job_result
        self.job_title = job_title
        self.job_location = job_location

    def run(self): 
        self.json_dct = self._request_info()

    def _request_info(self): 
        """Grab relevant information from the job result.

        Each job_result will contain a number of features to grab. Grab these, and
        then its href attribute. Use that href to actually issue a request for the
        job posting's text. 

        Return: 
        ------
            json_dct: dct
        """
        
        current_date = str(datetime.datetime.now(pytz.timezone('US/Mountain')))
        json_dct = {'search_title': self.job_title, \
                'search_location': self.job_location, \
                'search_date': current_date, 'job_site': 'simplyhired', 'job_title': ""}
        
        json_dct['job_title'] = self.job_result.select(".jobposting-title")[0].text

        try: 
            posting_company = self.job_result.find('span', 
                {'itemprop': 'name'}).text
        except: 
            posting_company = '' 
        try: 
            job_location = self.job_result.find('span', 
                {'itemprop': 'addressLocality'}).text
        except: 
            job_location = ''
        try: 
            job_region = self.job_result.find('span', 
                    {'itemprop': 'addressRegion'}).text
        except: 
            job_region = '' 
        
        json_dct['company'] = posting_company
        json_dct['location'] = job_location + ',' + job_region

        # Grab the href and pass that on to another function to get that info. 
        href = self.job_result.find('a').get('href')
        json_dct['href'] = href
        # try:
        #     json_dct['posting_txt'] = self.job_result.find('span',{'itemprop': 'description'}).text

        # except:
        #     json_dct['posting_txt'] = []            
       # print ("1")
        json_dct['posting_txt'] = self._query_href(href)
        #print ("2")
        return json_dct

    def _query_href(self, href): 
        """Grab the text from the href. 

        Args: 
        ----
            href: str 
                Holds the href to the job posting. 

        Return: str
        """
        #print ("Here")
        html = get('http://www.simplyhired.com' + href) if href.startswith('/') \
                    else get(href)
            #print ("Hola")        
        soup = BeautifulSoup(html.content, 'html.parser')
        if(len(soup.findAll(class_='viewjob-description'))>0):
            texts = soup.findAll(class_='viewjob-description')[0].text
            print ("Data Extracted")
        else:
            print ("error")

            ff = open("HTML Code Posting err", "w", encoding = "utf-8")
            ff.write(soup.prettify())    
            texts = ['SSLError', 'happened']
            # try:
        #     #print (soup.prettify())
        #     #texts = soup.findAll(text=True)
        #     #visible_texts = filter(find_visible_texts, texts)
        # except Exception as e: 
        #     print('Error in _query_href')
        #     print(e)
        #     visible_texts = ['SSLError', 'happened']

        return texts

