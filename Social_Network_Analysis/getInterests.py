

# This script contains methods for analysing the evolution of interestes of forum members. It relies on the CrimeBB dataset. 
# The dataset can be obtained under legal agreement with the Cambridge Cybercrime Centre. 
# More info at www.cambridgecybercrime.uk

# Copyright (C) 2018 Sergio Pastrana (sp849@cam.ac.uk)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import psycopg2
import socket
from datetime import datetime;
import pickle
import pylab as plt
import pandas as pd
import matplotlib.pyplot as pyplot
from matplotlib.font_manager import FontProperties
import numpy as np
import operator
import os
import re
import sys
import random
import time
from subprocess import Popen,PIPE
from collections import defaultdict

reload(sys)
sys.setdefaultencoding('utf8')
tsFormat='%Y%m%d_%H%M%S'

DB_USER='dbhunter'
DB_SERVER='192.168.56.101'
DB_NAME='crimebb'

### ### ### ### ### ### ### ### ### ### ### ### ### ### 
#		CONFIGURATION VARIABLES 
### ### ### ### ### ### ### ### ### ### ### ### ### ### 

# Minimum number of responses for a member to another one to consider the first as follower of the second
THRESHOLD_FOLLOWER=10;

# Minimum number of reputations votes to be consider for a member to be friendship/rival of another member (depending on whether the votes are positive or negative) 
THRESHOLD_REPUTATION=5;

# The minimum question score (as defined in the function getQScore) to consider a thread as a question
THRESHOLD_QUESTION_SCORE=3



# Weight of the threads to compute the interest score. This weight is multiplied by the number of threads initiated by an author
SCORE_THREADS_INTEREST=3

# When computing the interest of a user, minimum of threads and post that he/she must have done in a forum to be considered as part of his/her interests
THRESHOLD_SCORE_INTERESTS=20;

# Number of forums to show per year 
TOP_FORUMS_INTEREST=3

# Minimum number of lines that a post must contain to be considered as a tutorial or guide
THRESHOLD_LINES_TUTORIAL=10




### LIST OF FORUMS PER CATEGORY. Hackforums ##
#COMMON
hackforums_common=[2,134,336,363,122,25,364,373,198,167,259,318,370,260,12,262,180,261,354,155,187,128,112,89,37,222,251,32,162,385]
#HACK
hackforums_hack=[4,170,287,322,92,231,126,339,229,10,113,114,47,223,67,43,103,48,91,104,46,193,232]
#TECH
hackforums_tech=[110,13,87,79,192,175,137,347,254,86,85,327,165,247,159,240,8]
#CODING
hackforums_coding=[5,161,150,130,300,149,288,340,118,208,117,154,49,131,350,129,375]
#GAMES
hackforums_games=[65,341,14,191,72,82,168,297,189,179,203,256,326,246,73,337,169,384,244,238,358,359,81,212,90,356,213,311,214,237,320,290,319,83]
#MARKET
hackforums_market=[163,186,205,111,107,374,182,299,176,218,206,108,291,309,195,136,44,145,226,227,106,263,219,171,308,217,255,225]
#MONEY
hackforums_money=[120,369,277,221,127,245,268,121,281]
#WEB
hackforums_web=[50,333,295,183,172,142,139,143,144]
#GRAPHICS
hackforums_graphics=[6,248,148,157,133,158,181,69,160,293]

HF_CATEGORIES={'common':hackforums_common,'hack':hackforums_hack,'tech':hackforums_tech,'coding':hackforums_coding,'web':hackforums_web,'gaming':hackforums_games,'market':hackforums_market,'money':hackforums_money,'graphics':hackforums_graphics}
### LIST OF FORUMS PER CATEGORY. MPGH (TODO) ##

## MPGH CATEGORIES (TODO) ##
MPGH_CATEGORIES={}

# Returns the category of the given forum id
def getCategoryHF (fid):
	for category in HF_CATEGORIES.keys():
		if int(fid) in HF_CATEGORIES[category]:
			return category;
	return 'non-categorized'

# Returns the category of the given forum id
def getCategoryMPGH (fid):
	for category in MPGH_CATEGORIES.keys():
		if int(fid) in MPGH_CATEGORIES[category]:
			return category;
	return 'non-categorized'

# Initializes a dictionary that contains, per year, the aggregated number of threads and posts per forum. Keys: year->'threads|posts'->forum_id
def initializePostsAndThreadsPerYearPerForum():
	global postsAndThreadsPerYearPerForum
	postsAndThreadsPerYearPerForum={}
	for year in range(2007,2019):
		postsAndThreadsPerYearPerForum[year]={}
		postsAndThreadsPerYearPerForum[year]['threads']={}
		postsAndThreadsPerYearPerForum[year]['posts']={}

# Updates the aggreagated data with the number of threads initiated by a member in a forum
def getNumThreads(forum,SITE,idMember):
	global postsAndThreadsPerYearPerForum
	for year in range(2007,2019):
		postsAndThreadsPerYearPerForum[year]['threads'][forum]=0
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)	
	if connector:
		cursor = connector.cursor()
		# Get all the threads initiated by this author in the forum
		query=('SELECT "IdThread","Heading" FROM "Thread" WHERE "Author"=%s AND "Forum"=%s AND "Site"=%s')
		data=(idMember,forum,SITE)
		cursor.execute(query,data)
		threads=cursor.fetchall()
		# Get the timestamp of the thread
		for thread in threads:
			query=('SELECT "Timestamp" FROM "Post" WHERE "Thread"=%s AND "Site"=%s ORDER BY "Timestamp" ASC LIMIT 1')
			data=(thread[0],SITE)
			cursor.execute(query,data)
			post=cursor.fetchone()
			if post:
				year=int(post[0].strftime("%Y"))
				postsAndThreadsPerYearPerForum[year]['threads'][forum]+=1
		cursor.close()
		connector.close()
	else:
		print "ERROR Could not connect to database"
		exit(-1)
# Updates the aggreagated data with the number of posts initiated by a member in a forum
def getNumPosts(forum,SITE,idMember):
	global postsAndThreadsPerYearPerForum
	for year in range(2007,2019):
		postsAndThreadsPerYearPerForum[year]['posts'][forum]=0
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
	if connector:
		cursor = connector.cursor()
		# Get all the threads initiated by this author in the forum
		query=('SELECT "Timestamp" FROM "Post" p,"Thread" t WHERE p."Author"=%s AND p."Thread"=t."IdThread" AND t."Forum"=%s AND t."Site"=%s AND p."Site"=%s')
		data=(idMember,forum,SITE,SITE)
		cursor.execute(query,data)
		timestamps=cursor.fetchall()
		for ts in timestamps:
			year=int(ts[0].strftime("%Y"))
			postsAndThreadsPerYearPerForum[year]['posts'][forum]+=1
		cursor.close()
		connector.close()
	else:
		print "ERROR Could not connect to database"
		exit(-1)

		
# Get the aggregated data and stores it in disk (using pickle)
def countPostsAndThreadsOfMemberPerYear(idMember,SITE,OUTPUT_DIR_INTEREST,continueFromPickle=False,forumList=None,verbose=False):
	global postsAndThreadsPerYearPerForum
	if continueFromPickle:
		postsAndThreadsPerYearPerForum=pickle.load(open(OUTPUT_DIR_INTEREST+"postsAndThreads_member_"+str(idMember)+".pickle", "r" ))
	else:
		initializePostsAndThreadsPerYearPerForum()
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
	forums=[]
	yearRegistration=0
	if connector:
		cursor = connector.cursor()
		query=('SELECT "RegistrationDate","LastVisitDue" FROM "Member" WHERE "IdMember"=%s AND "Site"=%s')
		data=(idMember,SITE)
		cursor.execute(query,data)
		row=cursor.fetchone()
		if not row:
			print "%s Member %s not found in Site %s "%(datetime.now().strftime(tsFormat), idMember,SITE)
			return None,0,0;
		regDate=row[0]
		lastVisit=row[1]
		if verbose: print "%s Member %s was registered on %s and last visit was %s"%(datetime.now().strftime(tsFormat), idMember,regDate.strftime("%d/%m/%y"),lastVisit.strftime("%d/%m/%y"))
		yearRegistration=int(regDate.strftime("%Y"))
		yearLastVisit=int(lastVisit.strftime("%Y"))
		if not os.path.exists(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle"):
			query=('SELECT Count(*),t."Forum" FROM "Post" p,"Thread" t WHERE t."IdThread"=p."Thread" AND p."Author"=%s AND p."Site"=%s AND t."Site"=0 GROUP BY "Forum" ORDER BY Count(*) DESC')
			data=(idMember,SITE)
			cursor.execute(query,data)
			forums=cursor.fetchall()
		else:
			forums=pickle.load(open(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle",'r'))
		cursor.close()
		connector.close()
		if verbose: print "%s Member contains posts in %s forums"%(datetime.now().strftime(tsFormat), len(forums))
		if forumList!=None:
			forumsToProcess = [f for f in forums if int(f[1]) in forumList]
		else:
			forumsToProcess=[f for f in forums]
		if verbose: print "%s Going to process %s forums"%(datetime.now().strftime(tsFormat), len(forumsToProcess))
		for f in forumsToProcess:
			forum=f[1]
			if verbose: print "%s Calculating data for forum %s and member %s..."%(datetime.now().strftime(tsFormat), forum,idMember),
			getNumThreads(forum,SITE,idMember)
			getNumPosts(forum,SITE,idMember)
			if verbose: print " Done"
		if continueFromPickle:
			now=datetime.now().strftime("%d%m%y%H%M")
			os.rename(OUTPUT_DIR_INTEREST+"postsAndThreads_member_"+str(idMember)+".pickle",OUTPUT_DIR_INTEREST+"postsAndThreads_member_"+str(idMember)+"_BACKUP_"+now+".pickle")
		fd=open(OUTPUT_DIR_INTEREST+"postsAndThreads_member_"+str(idMember)+".pickle","wb") 
		pickle.dump(postsAndThreadsPerYearPerForum,fd)		
		fd.close()
		connector.close()
	else:
		print "ERROR Could not connect to database"
		exit(-1)
	return forums,yearRegistration,yearLastVisit

# Get the interests of the given member
# If onlyThreads is True, do not consider the posts
# If showPlot is True, prints a table and shows an bar plot with the aggregated data
# If forumList is given, then it updates existing information with the interests on this list (used due to updates on CrimeBB)
# If calculateCategories is True, then the interests are aggregated per categories
def getInterests(idMember,SITE,OUTPUT_DIR_INTEREST,histogramPlot=False,pieChart=False,onlyThreads=False,forumList=None,verbose=False,calculateCategories=False):
	global postsAndThreadsPerYearPerForum
	forums=None
	yearRegistration=0
	lastYearVisit=0
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
	if verbose: print 'Processing member %s'%idMember
	
	# Must continue from previous file if there is a list of forums and an existing file
	continueFromPickle=(forumList!=None) and (os.path.exists(OUTPUT_DIR_INTEREST+"postsAndThreads_member_"+str(idMember)+".pickle"))

	if not os.path.exists(OUTPUT_DIR_INTEREST+"postsAndThreads_member_"+str(idMember)+".pickle"):
		if verbose: print 'File postsAndThreads_member_'+str(idMember)+'.pickle not found. Counting posts and threads...'
		forums,yearRegistration,lastYearVisit=countPostsAndThreadsOfMemberPerYear(idMember,SITE,OUTPUT_DIR_INTEREST,continueFromPickle=False,forumList=None,verbose=verbose);
		if yearRegistration==0:
			return
		if not os.path.exists(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle"):
			pickle.dump(forums,open(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle",'w'))
	elif continueFromPickle:
		if verbose: print 'Continuing from pickle. File: postsAndThreads_member_'+str(idMember)+'.pickle. Counting posts and threads of forumlist',forumList
		forums,yearRegistration,lastYearVisit=countPostsAndThreadsOfMemberPerYear(idMember,SITE,OUTPUT_DIR_INTEREST,continueFromPickle=True,forumList=forumList,verbose=verbose)
		pickle.dump(forums,open(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle",'w'))
		time.sleep(10)
	elif not os.path.exists(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle"):
		cursor = connector.cursor()
		query=('SELECT Count(*),t."Forum" FROM "Post" p,"Thread" t WHERE t."IdThread"=p."Thread" AND p."Author"=%s AND p."Site"=%s AND t."Site"=%s GROUP BY "Forum" ORDER BY Count(*) DESC')
		data=(idMember,SITE,SITE)
		cursor.execute(query,data)
		forums=cursor.fetchall()
		cursor.close()
		pickle.dump(forums,open(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle",'w'))
		time.sleep(10)
	else:
		forums=pickle.load(open(OUTPUT_DIR_INTEREST+"forums_member_"+str(idMember)+".pickle",'r'))

	if yearRegistration==0:
		cursor = connector.cursor()
		query=('SELECT "RegistrationDate","LastVisitDue" FROM "Member" WHERE "IdMember"=%s AND "Site"=%s')
		data=(idMember,SITE)
		cursor.execute(query,data)
		row=cursor.fetchone()
		regDate=row[0]
		lastVisit=row[1]
		if verbose: print "Member %s was registered on %s, and last Visit was on %s"%(idMember,regDate.strftime("%d/%m/%y"),lastVisit.strftime("%d/%m/%y"))
		yearRegistration=int(regDate.strftime("%Y"))
		lastYearVisit=int(lastVisit.strftime("%Y"))
		# If hidden, get all until today
		if lastYearVisit<=2000:
			lastYearVisit=2018
	
	
	postsAndThreadsPerYearPerForum=pickle.load(open(OUTPUT_DIR_INTEREST+"postsAndThreads_member_"+str(idMember)+".pickle", "r" ))		
	raw_data={}
	raw_data['Year']=[]
	top_category={}
	columns=['Year']
	allCats=defaultdict(lambda:0)
	interests={}
	categories={}
	for year in range(yearRegistration,lastYearVisit+1):
		if not year in postsAndThreadsPerYearPerForum.keys():
			break
		raw_data['Year'].append(str(year))
		if verbose: print str(year)+":"
		if verbose: print "--------"
		postsAndThreadsPerYearPerForum[year]['score']={}
		for f in forums:
			forum=f[1]
			try:
				postsAndThreadsPerYearPerForum[year]['posts'][forum]=postsAndThreadsPerYearPerForum[year]['posts'][forum]-postsAndThreadsPerYearPerForum[year]['threads'][forum]
			except KeyError:
				print "ERROR Forum %s not calculated for member %s"%(forum,idMember)
				return

			if onlyThreads:
				postsAndThreadsPerYearPerForum[year]['score'][forum]=postsAndThreadsPerYearPerForum[year]['threads'][forum]
			else:
				postsAndThreadsPerYearPerForum[year]['score'][forum]=postsAndThreadsPerYearPerForum[year]['threads'][forum]*SCORE_THREADS_INTEREST+postsAndThreadsPerYearPerForum[year]['posts'][forum]
		sorted_forums=sorted(postsAndThreadsPerYearPerForum[year]['score'].items(),key=operator.itemgetter(1),reverse=True)
		interests[year]=sorted_forums
		cursor = connector.cursor()
		if calculateCategories:
			categories[year]=defaultdict(lambda:0)
			for forum in sorted_forums:
				query=('SELECT "Title" FROM "Forum" WHERE "IdForum"=%s AND "Site"=%s')
				data=(forum[0],SITE)
				cursor.execute(query,data)
				title=cursor.fetchone()[0].replace(' ','_').replace(',','_')
				if SITE==0:
					category=getCategoryHF(forum[0])
				elif SITE==4:
					#category=getCategoryMPGH(forum[0])
					# FOR MPGH, CONSIDER EACH CATEGORY AS THE SUB-FORUM TITLE
					category=title
				allCats[category]+=forum[1]
				categories[year][category]+=forum[1]

				if verbose: print "\tForum: %s (ID=%s), Threads=%s, Posts=%s Score=%s"%(title,forum[0],postsAndThreadsPerYearPerForum[year]['threads'][forum[0]],postsAndThreadsPerYearPerForum[year]['posts'][forum[0]],forum[1])
				#if not ('F-'+str(forum[0])) in raw_data.keys():
				if not (title) in raw_data.keys():
					raw_data[title]=[]
					columns.append(title)
				raw_data[title].append(int(forum[1]))
			cursor.close()

	if calculateCategories and verbose: 
		print "TOP 10 CATEGORIES FOR MEMBER %s,"%idMember,
		sortedCategories=sorted(allCats.items(),key=operator.itemgetter(1),reverse=True)
		for cat,num in sortedCategories[:10]:
			print "%s-%s,"%(cat.replace(' ','_').replace(',','_'),num),
		print
		for forum in raw_data.keys():
			# Don't remove ewhoring
			if not 'Year' in forum and not "whoring" in forum.lower():
				if all(np.array(raw_data[forum]).astype(np.float)<THRESHOLD_SCORE_INTERESTS):
					del raw_data[forum]
					columns.remove(forum)
		print "CATEGORIES LIST"
		for cat,num in sortedCategories[:10]:
			print cat
	if histogramPlot:
		plotHistogram(raw_data,columns,idMember,onlyThreads)
	if pieChart:
		plotPieChart(allCats,OUTPUT_DIR_INTEREST_GRAPHS+"allCategories"+str(idMember)+".png",str(idMember)+"_ALL")
	connector.close()
	return interests,categories
def plotPieChart (categories,filename,title,N=5):
	colorMap ={'common':'khaki','hack':'red','tech':'purple','coding':'fuchsia','web':'gray','gaming':'mediumblue','market':'orange','money':'green','graphics':'saddlebrown','others':'black'}
	pyplot.title(title)
	# Data to plot
	sortedCategories=sorted(categories.items(),key=operator.itemgetter(1),reverse=True)
	labels = []
	sizes = []
	colors = []
	for c,q in sortedCategories[:N]:
		labels.append(c)
		sizes.append(q)
		colors.append(colorMap[c])
	labels.append('others')
	sizes.append(sum(q for c,q in sortedCategories[N:]))
	colors.append(colorMap['others'])
	#patches, texts = pyplot.pie(sizes, colors=colors, shadow=False, startangle=90)
	patches, texts,autoText = pyplot.pie(sizes, colors=colors,autopct='%1.1f%%',startangle=140)
	pyplot.legend(patches, labels, loc="best")
	pyplot.axis('equal')
	pyplot.tight_layout()
	pyplot.savefig(filename, bbox_inches="tight")
	pyplot.gcf().clear()
# Creates the aggregated bar plots of interests (i.e. score in each forum per year)
def plotHistogram(raw_data,columns,idMember,onlyThreads):

	df = pd.DataFrame(raw_data, columns = columns)
	df.name = 'Member id: %s'%idMember
	print df
	print columns
	numColors=len(columns)
	# Create the general blog and the "subplots" i.e. the bars
	f, ax1 = pyplot.subplots(1, figsize=(10,5))
	# Set the bar width
	bar_width = 0.75
	# positions of the left bar-boundaries
	bar_l = [i+1 for i in range(len(df['Year']))]
	cm = pyplot.get_cmap('gist_rainbow')
	ax1.set_color_cycle([cm(1.*i/numColors) for i in range(numColors)])
	# positions of the x-axis ticks (center of the bars as bar labels)
	tick_pos = [i for i in bar_l]
	
	accumulatedBottom=(0,) * len(df['Year'])
	#accumulatedBottom=(0)
	accumulatedBottomList=[]
	for i in range(0,len(df['Year'])):
		accumulatedBottomList.append(0)
	for i in range(1,len(columns)):
		column=columns[i]
		print df[column]
		print "BOTTOM:",accumulatedBottom
		if "whoring" in column.lower():
		 	ax1.bar(bar_l,df[column],width=bar_width,label=column,bottom=accumulatedBottom,alpha=0.5,color='black')
		else:
			# Create a bar plot, in position bar_1
			ax1.bar(bar_l,df[column],width=bar_width,label=column,bottom=accumulatedBottom)
		for i in range(0,len(df['Year'])):
			accumulatedBottomList[i]=accumulatedBottom[i]+int(df[column][i])
		accumulatedBottom=tuple(accumulatedBottomList)

	# set the x ticks with names
	pyplot.xticks(tick_pos, df['Year'])

	# Set the label and legends
	ax1.set_ylabel("Total Score")
	ax1.set_xlabel("Year")
	fontP = FontProperties()
	fontP.set_size('small')
	art = []

	lgd=pyplot.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.,prop = fontP)
	art.append(lgd)
	pyplot.title(df.name)

	# Set a buffer around the edge
	pyplot.xlim([min(tick_pos)-bar_width, max(tick_pos)+bar_width])
	if onlyThreads:
		filename=OUTPUT_DIR_INTEREST_GRAPHS+"evolutionInterestForumsOnlyThreads"+str(idMember)+".png"
	else:
		filename=OUTPUT_DIR_INTEREST_GRAPHS+"evolutionInterestForums"+str(idMember)+".png"
	pyplot.savefig(filename, additional_artists=art,bbox_inches="tight")

# COMMON VARIABLES

#### HACKFORUMS ####
SITE=0
FORUM_NAME='hackforums'
