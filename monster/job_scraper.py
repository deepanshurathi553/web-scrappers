"""A module for scraping SimplyHired for jobs. 

This module is the driver for a SimplyHired scraper. It controls the process of
issuing requests, parsing the contents of those requests, and storing the results. 
It also handles the threading and multiprocessing that is used to speed up the scraping process. 

Usage: 

    python job_scraper.py <job title> <job location> <radius>
"""

import sys
import os
wd = os.path.abspath('.')
sys.path.append(wd + '/../')
import multiprocessing
import datetime
import pytz
from functools import partial
from general_utilities.query_utilities import format_query, get_html
from general_utilities.storage_utilities import store_in_mongo
from general_utilities.parsing_utilities import parse_num
from request_threading import RequestInfoThread

# class Job():

#     def __init__(self, job_title, job_location_actual, job_desc_brief):
#         self.job_title_name=job_title_name
#         self.job_location_actual=job_location_actual
#         self.job_desc_brief = job_desc_brief

def multiprocess_pages(base_URL, job_title, job_location, page_number): 
    """Grab the URLS and other relevant info. from job postings on the page. 

    The Simply Hired URL used for job searching takes another parameter, `pn`, that
    allows you to start the job search at jobs 11-20, 21-30, etc. Use this to grab
    job results from multiple pages at once, and then feed the jobs from each page
    to threads for further parsing. 

    Args: 
    ----
        base_URL: str 
        job_title: str 
        job_location: str 
        page_number: int 
    """

    url = base_URL + '&pn=' + str(page_number)
    html = get_html(url)
    # Each row corresponds to a job. 
    #f = open("HTML Code 2", "w", encoding = "utf-8")
    #f.write(html.prettify())
    jobs = html.select('.summary')
    #print (jobs)
    threads = []
    mongo_update_lst = []
    for job in jobs: 
        thread = RequestInfoThread(job, job_title, job_location)
        thread.start()
        threads.append(thread)
    for thread in threads: 
        thread.join()
        mongo_update_lst.append(thread.json_dct)
    
    store_in_mongo(mongo_update_lst, 'job_postings', 'monster')

if __name__ == '__main__':
    try: 
        job_title = sys.argv[1]
        job_location = sys.argv[2]
        radius = sys.argv[3]
    except IndexError: 
        raise Exception('Program needs a job title, job location, and radius inputted!')

    base_URL = 'http://jobs.monster.com/search/?'
    query_parameters = ['q={}'.format('-'.join(job_title.split())), 
            '&where={}'.format('-'.join(job_location.split())), '&sort=dt.rv.di', 
            '&rad={}'.format(radius)]

    query_URL = format_query(base_URL, query_parameters)
    print (query_URL)
    html = get_html(query_URL)
    #f = open("HTML Code 1", "w", encoding = "utf-8")
    #f.write(html.prettify())
    #file = open("simplyhired.csv", "w+")
    #print (html.prettify())
    try: 
        #print ("Here")
        #print (html.select(".posting-total")[0].text)
        #num_jobs_txt = str(html.select('.posting-total')[0].text)
        print ("Hey")
        num_jobs_txt = (html.find(class_='navigation-content').find(class_='figure')).text
        #print (num_jobs_txt)
        xy = (num_jobs_txt.split(" "))
        xy = xy[xy.index('Jobs') -1]
        cd = int(xy[1])*10000 + int(xy[2])*1000 +int(xy[3])*100 +int(xy[4])*10 + int(xy[5])
        #print (num_jobs_txt)
        num_jobs = int(cd)
        print (num_jobs)
    except: 
        print('No jobs for search {} in {}'.format(job_title, job_location))
        sys.exit(0)

    
    current_date = str(datetime.datetime.now(pytz.timezone('US/Mountain')))

    storage_dct = {'job_site': 'simplyhired', 'num_jobs': num_jobs, 
            'date': current_date, 'title': job_title, 'location': job_location}
    store_in_mongo([storage_dct], 'job_numbers', 'simplyhired')

    # All of the jobs should be available through the '.js-job-link' CSS class.
    max_pages = num_jobs // 50 + 1
    print (max_pages)
    page_numbers = range(1, max_pages + 1)
    execute_queries = partial(multiprocess_pages, query_URL, job_title, 
            job_location)
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(execute_queries, page_numbers)
