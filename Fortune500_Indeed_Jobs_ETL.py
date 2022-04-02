# Written by Paul Aggarwal

# Dependencies
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
import datetime
from urllib.parse import quote


# Import Fortune 500 company name list from csv
fortune500=pd.read_csv("fortune500list.csv")

fortune500_list=list(fortune500['Company Name'][:500])

# What do you want to search for?
what="python,+sql,+etl"

# Indeed query by company only to get company id from Indeed then apply that to second query
jobs = []
for co in fortune500_list:
    costr=quote(co)
    #print(costr)
    first_url_step="https://www.indeed.com/jobs?q="+ costr +"&sort=date"
    #print(first_url_step)
    html = requests.get(first_url_step)
    soup = bs(html.text, 'html.parser')
    try:
        jcid = (soup.find('span', {'class':'company'}).a['onmousedown'].split('jcid=')[-1].split("'")[0])
        #print(soup.find('span', {'class':'company'}).a.text.replace("\n","").strip(), jcid)
    except:
        print("ERROR parsing jcid: ",jcid)
    
    # Current date time object
    now = datetime.datetime.now()
    second_url_step="https://www.indeed.com/jobs?q="+ what + "&rbc=" + costr + "&jcid=" + jcid + "&sort=date"
    #print(second_url_step)
    html2 = requests.get(second_url_step)
    #print(html2)
    next_soup = bs(html2.text, 'html.parser')
    all_jobs = next_soup.find_all('div', {'data-tn-component':"organicJob"})
    job_no = 0
    for result in all_jobs:
        #print(result)
        job_row = {}
        co_text = result.find('span', {'class':'company'})
        #print(co_text)
        try:
            job_row['jkid'] = result.h2.a['href'].split('?')[1].split('&')[0].split('jk=')[1]
            job_row['company'] = co_text.a.text.replace("\n","").strip()
            job_row['jcid'] = result.find('span', {'class':'company'}).a['onmousedown'].split('jcid=')[-1].split("'")[0]
            job_row['job_loc'] = result.find('span', {'class':'location'}).text
            job_row['job_no'] =  job_no + 1
            job_row['job_title'] = result.find('a', {'data-tn-element':'jobTitle'}).text
            job_row['job_desc'] = result.find('span', {'class':'summary'}).text.replace("\n","").strip()
            job_row['job_age'] = result.find('span', {'class':'date'}).text
            job_row['query_date'] = now.isoformat().split('T')[0]
            job_row['query_time'] = now.isoformat().split('T')[1].split('.')[0]
            jobs.append(job_row)
            job_no+=1
        except:
            print("skipped: ",co_text)
            print("skipped: ",co," quote: ",costr," jcid: ",jcid)


df = pd.DataFrame.from_dict(jobs)

df.to_csv("indeed.dat")

import mysql
import mysql_config
# create mysql connection
mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  passwd="atrium"
)

# Create Database
mycursor = mydb.cursor()
#mycursor.execute("CREATE DATABASE Indeed")

# Choose Database
mycursor.execute("USE Indeed")

# job_desc would not insert into mysql without ALTER DATABASE CHARACTER SET utf8 COLLATE utf8_general_ci
mycursor.execute("ALTER DATABASE Indeed CHARACTER SET utf8 COLLATE utf8_general_ci")

mycursor.execute("drop table jobs")

# Create Table
mycursor.execute(
    "CREATE TABLE jobs (job_age VARCHAR(15), company VARCHAR(255), job_desc VARCHAR(255), jcid VARCHAR(20), jkid VARCHAR(20), job_no INT, job_loc VARCHAR(255), query_date DATE, query_time VARCHAR(8), job_title VARCHAR(255))")

# job_desc would not insert into mysql without ALTER TABLE jobs CONVERT TO CHARACTER SET utf8
mycursor.execute("ALTER TABLE jobs CONVERT TO CHARACTER SET utf8")

# Check if table exists
mycursor.execute("SHOW TABLES")
for x in mycursor:
  print(x)

from sqlalchemy import create_engine
import pymysql
pymysql.install_as_MySQLdb()

# Create an engine to the census database
engine = create_engine('mysql://root:atrium@localhost/Indeed')

df.to_sql(name='jobs', con=engine, if_exists='append', index=False)
