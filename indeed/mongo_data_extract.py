import pymongo
from pymongo import MongoClient
import csv

#connect to Database
connection = MongoClient('localhost', 27017)
db = connection.job_postings


#handle to friends Collection
data = db.indeed_updated_final

rows = [["Search Title", "Search Location", "Job Title", "Company Name", "Job Location", "Date Posted", "Posting Text"]]
friendsList = data.find()

for item in friendsList:

	newrow = []
	newrow.append(item["search_title"].replace("\n", " "))
	newrow.append(item["search_location"].replace("\n", " "))
	newrow.append(item["job_title"].replace("\n", " "))
	newrow.append(item["company"].replace("\n", " "))
	newrow.append(item["location"].replace("\n", " "))
	newrow.append(item["date"].replace("\n", " "))
	posting = item["posting_txt"]
	for i in range(len(posting)):
		posting[i].replace("\n"," ")
	newrow.append(posting)
	rows.append(newrow)

with open("data_new_final.csv", 'w', encoding="utf-8") as csvFile:
    writer = csv.writer(csvFile)
    writer.writerows(rows)

csvFile.close()