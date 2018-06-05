# -*- coding: utf-8 -*-


# This script contains methods for social network analysis on the CrimeBB dataset. 
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
import sys
import pickle
import cPickle
from datetime import datetime,timedelta
import os
import networkx as nx
from multiprocessing import Pool
import community
import pylab as plt
import operator
import scipy.stats as stats
import numpy
import nltk
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
import string
import gensim
from gensim import corpora
from collections import defaultdict
import gc

from getInterests import getInterests,plotPieChart

DB_USER='dbhunter'
DB_SERVER='192.168.56.101'
DB_NAME='crimebb'

reload(sys)
sys.setdefaultencoding('utf8')
tsFormat='%Y%m%d_%H%M%S'

# CALCULATE THE TOTAL CITES, H INDEX AND H-10 INDEX FOR EACH AUTHOR
def calculateImpactMetrics(forum=-1,printMetrics=False):
	print "%s Getting impact metrics for forum %s"%(datetime.now().strftime(tsFormat),forum)
	if forum>0:
		filename=OUTPUT_DIR+'Forum'+str(forum)+'/impact_'+str(forum)+'.pickle'
	else:
		filename=OUTPUT_DIR+'/impact_ALL.pickle'
	if os.path.exists(filename): 
		print "%s Forum %s. Reading impact from disk"%(datetime.now().strftime(tsFormat),forum)
		impact=pickle.load(open(filename,'r'))
	else:
		connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
		
		cursor=connector.cursor()
		if forum>0:
			print "%s Forum %s. Querying DB for impact"%(datetime.now().strftime(tsFormat),forum)
			query=('SELECT "IdThread","Author" FROM "Thread" WHERE "Forum"=%s AND "Site"=%s');
			data=(forum,SITE) 
			cursor.execute(query,data)
		else:
			print "%s Querying DB for impact of ALL forums"%(datetime.now().strftime(tsFormat))
			query=('SELECT "IdThread","Author" FROM "Thread" WHERE "Site"=%s'%SITE);
			cursor.execute(query)
		threads=cursor.fetchall()
		print "%s Obtained %s threads"%(datetime.now().strftime(tsFormat),len(threads))
		impact={}
		count=0
		for thread,author in threads:
			count+=1
			# Be Verbose
			if count%100 == 0 or count==len(threads):
				progress = round(count*100.0/len(threads),2)
				sys.stdout.write("%s Processing thread %s (%s %s) \r"%(datetime.now().strftime(tsFormat), count,progress,'%'))
				sys.stdout.flush()

			if not author in impact.keys():
				impact[author]={}	
			query=('SELECT "IdPost","CitedPost","Author" FROM "Post" WHERE "Thread"=%s AND "Site"=%s ORDER BY "IdPost" ASC');
			data=(thread,SITE) 
			cursor.execute(query,data)
			posts=cursor.fetchall()
			if len(posts)>0:
				opID=long(posts[0][0])
				impact[author][thread]=0
				for post,cited,a in posts[1:]:
					if a!=author and (not cited or len(cited)==0 or cited[0]<0 or opID in cited):
						impact[author][thread]+=1;
		pickle.dump(impact,open(filename,'wb'))
	print
	print "%s Forum %s. Calculating impactMetrics"%(datetime.now().strftime(tsFormat),forum)
	metrics={}
	totalCites={}
	for author in impact.keys():
		verbose=False
		h=0
		h10=0
		h50=0
		h100=0
		totalCites[author]=0
		metrics[author]={}
		metrics[author]['numThreads']=0
		metrics[author]['totalCites']=0
		sortedCites=sorted(impact[author].items(),key=operator.itemgetter(1),reverse=True)
		count=0
		for thread,numCites in sortedCites:
			metrics[author]['numThreads']+=1
			totalCites[author]+=numCites
			metrics[author]['totalCites']+=numCites
			if h<numCites:
				h=h+1
			if numCites>=10:
				h10+=1
			if numCites>=50:
				h50+=1
			if numCites>=100:
				h100+=1
			if verbose:
				count+=1
				print "[%s] Thread %s NumCites %s H - %s h10 - %s"%(count,thread,numCites,h,h10)
		metrics[author]['h']=h
		metrics[author]['h10']=h10
		metrics[author]['h50']=h50
		metrics[author]['h100']=h100

	if printMetrics:
		#sortedCites=sorted(totalCites.items(),key=operator.itemgetter(1),reverse=True)
		sortedCites=sorted(metrics, key=lambda author:(metrics[author]['h'],metrics[author]['totalCites']),reverse=True)
		if os.path.exists(FILE_EARNINGS):
			print "Author\tThreads\tCites\tH\tEarnings\tRankEarnings\tH10\t\tH50\t\tH100"
			print "---------------------------------------------------------------------------------------------------"
			for author in sortedCites[:30]:
				position,earnings=getEarningsAndRelativePosition(author)	
				totalThreads=metrics[author]['numThreads']
				#print "Author:%s\tNumThreads=%s\tTotalCites:%s\tH:%s\tH10:%s(%.2f%%)\tH50:%s(%.2f%%)\tH100:%s(%.2f%%)"%(author,totalThreads,totalCites[author],metrics[author]['h'],metrics[author]['h10'],metrics[author]['h10']*100.0/totalThreads,metrics[author]['h50'],metrics[author]['h50']*100.0/totalThreads,metrics[author]['h100'],metrics[author]['h100']*100.0/totalThreads)
				print "%s\t   %s\t%s\t%s\t%.2f\t\t%s\t\t%s (%.2f%%)\t%s (%.2f%%)\t%s (%.2f%%)"%(author,totalThreads,metrics[author]['totalCites'],metrics[author]['h'],earnings,position,metrics[author]['h10'],metrics[author]['h10']*100.0/totalThreads,metrics[author]['h50'],metrics[author]['h50']*100.0/totalThreads,metrics[author]['h100'],metrics[author]['h100']*100.0/totalThreads)
		else:
			print "Author\tThreads\tCites\tH\tH10\t\tH50\t\tH100"
			print "-------------------------------------------------------------------------------"
			for author in sortedCites[:30]:
				totalThreads=metrics[author]['numThreads']
				#print "Author:%s\tNumThreads=%s\tTotalCites:%s\tH:%s\tH10:%s(%.2f%%)\tH50:%s(%.2f%%)\tH100:%s(%.2f%%)"%(author,totalThreads,totalCites[author],metrics[author]['h'],metrics[author]['h10'],metrics[author]['h10']*100.0/totalThreads,metrics[author]['h50'],metrics[author]['h50']*100.0/totalThreads,metrics[author]['h100'],metrics[author]['h100']*100.0/totalThreads)
				print "%s\t   %s\t%s\t%s\t%s (%.2f%%)\t%s (%.2f%%)\t%s (%.2f%%)"%(author,totalThreads,metrics[author]['totalCites'],metrics[author]['h'],metrics[author]['h10'],metrics[author]['h10']*100.0/totalThreads,metrics[author]['h50'],metrics[author]['h50']*100.0/totalThreads,metrics[author]['h100'],metrics[author]['h100']*100.0/totalThreads)				
	return metrics
def getZero():
	return 0
def dd():
    return defaultdict(getZero)

# Queries the database to get all the responses from users for each year. 
# A post is considered a response if either it does not contain cites, thus it responds to the first post of a thread or if it cites a post, thus it responds to the cited post
# If checkTutorialsAndQuestions is True, it also gets whether the response is to a question or a tutorial and whether it is the last one 
def getUsersResponsesYear(year,checkTutorialsAndQuestions=False):
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)

	print "%s Getting all user responses for year %s "%(datetime.now().strftime(tsFormat),year)
	# If there is already a this year responses file, load it again
	if os.path.exists(OUTPUT_DIR+'responses_'+str(year)+'.pickle'):
		print "%s Reading responses from file"%datetime.now().strftime(tsFormat)
		responses=pickle.load(open(OUTPUT_DIR+'responses_'+str(year)+'.pickle','r'))
		if not checkTutorialsAndQuestions:
			return responses
	else:
		responses=defaultdict(dd)	
	if checkTutorialsAndQuestions:	
		trainClassifierForTextClassification();
		if os.path.exists(OUTPUT_DIR+'tutorials_'+str(year)+'.pickle'):
			tutorials=pickle.load(open(OUTPUT_DIR+'tutorials_'+str(year)+'.pickle','r'))
		else:
			tutorials={}
		if os.path.exists(OUTPUT_DIR+'questionsAnswered_'+str(year)+'.pickle'):
			questionsAnswered=pickle.load(open(OUTPUT_DIR+'questionsAnswered_'+str(year)+'.pickle','r'))
		else:
			questionsAnswered={}	
		filename=OUTPUT_DIR+'userResponsesAndCites_'+str(year)+'.csv'

	
	if os.path.exists(OUTPUT_DIR+'raw_cites_'+str(year)+'.pickle'):
		print "%s Year %s. Reading cites from disk"%(datetime.now().strftime(tsFormat),year)
		cites=pickle.load(open(OUTPUT_DIR+'raw_cites_'+str(year)+'.pickle','r'))
	else:
		print "%s Year %s. Querying DB for cites"%(datetime.now().strftime(tsFormat),year)
		# Query to get all the citers
		query=('SELECT t."Forum",t."IdThread",p1."Author",p2."Author",p1."Content",p2."Timestamp" FROM "Post" p1, "Post" p2, "Thread" t WHERE t."parsed" AND p2."Timestamp">=date(\'%s-01-01\') AND p2."Timestamp"< date(\'%s-01-01\') AND p1."Thread"=p2."Thread" AND t."IdThread"=p1."Thread" AND p1."IdPost"=ANY(p2."CitedPost")  AND NOT p2."Author"=p1."Author"  AND  p1."Site"=%s AND p2."Site"=%s and t."Site"=%s');
		data=(year,year+1,SITE,SITE,SITE) 
		cursor = connector.cursor()
		cursor.execute(query,data)
		cites=cursor.fetchall()
		cursor.close()
		pickle.dump(cites,open(OUTPUT_DIR+'raw_cites_'+str(year)+'.pickle','wb'))

	print "%s Year %s. Fetched %s cites"%(datetime.now().strftime(tsFormat),year,len(cites))
	count=0
	for (fid,tid,author,replier,content,timestamp) in cites:
		count+=1
		# Be Verbose
		if count%100 == 0 or count==len(cites):
			progress = round(count*100.0/len(cites),2)
			sys.stdout.write("%s Processing cite %s (%s %s) \r"%(datetime.now().strftime(tsFormat), count,progress,'%'))
			sys.stdout.flush()
		
		
		responses[author][replier]+=1
		if checkTutorialsAndQuestions:
			# For the cites, we do not care whether the cited post is question or not, since it would bias the results
			# Also, we do not care whether this is the last or unique post. We are only interested in the link, not the type
			qScore=0
			unique=0
			last=0

			# Store in plain text format
			fd=open(filename,'a+');	
			fd.write("%s,%s,%s,%s,%s,%s,%s,C\n"%(fid,tid,author,replier,qScore,unique,last))
			fd.close()
	print
	if os.path.exists(OUTPUT_DIR+'Siteraw_responses_'+str(year)+'.pickle'):
		print "%s Year %s. Reading responses from disk"%(datetime.now().strftime(tsFormat),year)
		raw_responses=pickle.load(open(OUTPUT_DIR+'raw_responses_'+str(year)+'.pickle','r'))			
	else:
		print "%s Year %s. Querying DB for responses"%(datetime.now().strftime(tsFormat),year)
		# Query to get all the repliers that do not cite previous post
		query=('SELECT t."Forum",t."IdThread",t."NumPosts",t."Heading",t."Author", p."Author",p."IdPost" FROM "Thread" t, "Post" p   WHERE  t."parsed" AND p."Timestamp">=date(\'%s-01-01\') AND p."Timestamp"< date(\'%s-01-01\') AND -1=ALL(p."CitedPost")  AND p."Thread"=t."IdThread" AND NOT t."Author"=p."Author"  AND t."Site"=%s AND p."Site"=%s');
		data=(year,year+1,SITE,SITE)
		cursor=connector.cursor()
		cursor.execute(query,data)
		raw_responses=cursor.fetchall()
		pickle.dump(raw_responses,open(OUTPUT_DIR+'raw_responses_'+str(year)+'.pickle','wb'))
		cursor.close()			
	print "%s Year %s. Fetched %s responses"%(datetime.now().strftime(tsFormat),year,len(raw_responses))
	
	count=0
	threadIsTutorial={}
	qScores={}
	lastPost={}
	for (fid,tid,numPosts,heading,author,replier,idPost) in raw_responses:
		count+=1
		# Be Verbose
		if count%100 == 0 or count==len(raw_responses):
			progress = round(count*100.0/len(raw_responses),2)
			sys.stdout.write("%s Processing response %s (%s %s) \r"%(datetime.now().strftime(tsFormat), count,progress,'%'))
			sys.stdout.flush()
		responses[author][replier]+=1

		if checkTutorialsAndQuestions:
			# Next, it is checked whether a thread is a tutorial and the last post of the thread
			# If this thread has not been checked yet
			if not tid in threadIsTutorial.keys():
				# ASSUMES POST IDs ARE PROPERLY ORDERED WITHIN A THREAD, WHICH MIGHT NOT BE ALWAYS THE CASE!
				# Fetch the posts to check whether the thread is a tutorial or a question, and to get the lastPost
				cursor = connector.cursor()
				query=('SELECT "Content","IdPost","Author" FROM "Post"  WHERE  "Thread"=%s AND "Site"=%s ORDER BY "IdPost" ASC');
				data=(tid,SITE)
				cursor.execute(query,data)
				rows=cursor.fetchall()
				if len(rows)>0:
					i=0
					while i<len(rows) and rows[i][2]!=author:
						i+=1 
					content=rows[i][0]
				else:
					content=" "

				# Check if this response is the last on the thread
				i=-1
				if len(rows)>0:
					while i>0 and (rows[i][2]==author):
						i-=1
					lastPost[tid]=rows[i][1]
				else:
					lastPost[tid]=0
				cursor.close()
				
				# Gets the question score for this thread
				qScore=getQuestionScore(heading,content,tid);
				qScores[tid]=qScore
				# Check if this is a question.
				if qScore < THRESHOLD_QUESTION_SCORE:				
					# If it is not a question, check if this is a tutorial.
					threadIsTutorial[tid]=isTutorial(heading,content)
				else:
					threadIsTutorial[tid]=False

			# Check if this response is the only one in the thread or the last one
			last=0
			unique=0
			if numPosts==2:
				unique=1
			elif idPost==lastPost[tid]:	
				last=1

			# Check if this is a tutorial. If so, update the tutorial data
			if threadIsTutorial[tid]:
				if author in tutorials.keys():
					if fid in tutorials[author].keys():
						tutorials[author][fid]+=1
					else:
						tutorials[author][fid]=1
					tutorials[author]['total']+=1
				else:
					tutorials[author]={}
					tutorials[author]['total']=1
					tutorials[author][fid]=1

			# Check if this is a question. If so, update the questionAnswered data
			if qScores[tid] >= THRESHOLD_QUESTION_SCORE:				
				if replier in questionsAnswered.keys():
					if fid in questionsAnswered[replier].keys():
						questionsAnswered[replier][fid]+=1
					else:
						questionsAnswered[replier][fid]=1
					questionsAnswered[replier]['total']+=1
					questionsAnswered[replier]['unique']+=unique
					questionsAnswered[replier]['last']+=last
				else:
					questionsAnswered[replier]={}
					questionsAnswered[replier]['total']=1
					questionsAnswered[replier]['unique']=unique
					questionsAnswered[replier]['last']=last
					questionsAnswered[replier][fid]=1

			
			# Store in plain text format
			fd=open(filename,'a+');	
			fd.write("%s,%s,%s,%s,%s,%s,%s,R\n"%(fid,tid,author,replier,qScores[tid],unique,last))
			fd.close()
	print
	print "%s FINISHED PROCESSING YEAR %s"%(datetime.now().strftime(tsFormat),year)
	pickle.dump(responses, open(OUTPUT_DIR+"responses_"+str(year)+".pickle", "wb" ))
	if checkTutorialsAndQuestions:
		pickle.dump(tutorials,open(OUTPUT_DIR+'tutorials_'+str(year)+'.pickle','wb'))
		pickle.dump(questionsAnswered,open(OUTPUT_DIR+'responsesAnswered_'+str(year)+'.pickle','wb'))
	connector.close()

# Get all the user responses and cites for a given forum
def getUsersResponsesForum(forum):
	print "%s Connecting to Database."%(datetime.now().strftime(tsFormat))	
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)

	print "%s Getting all user responses for forum %s"%(datetime.now().strftime(tsFormat),forum)
	# If there is already a this forum responses file, load it again
	if os.path.exists(OUTPUT_DIR+'Forum'+str(forum)+'/responses_'+str(forum)+'.pickle'):
		responses=pickle.load(open(OUTPUT_DIR+'Forum'+str(forum)+'/responses_'+str(forum)+'.pickle','r'))
		return responses
	else:
		responses={}		
	filename=OUTPUT_DIR+'Forum'+str(forum)+'/userResponsesAndCites_'+str(forum)+'.csv'
	cursor = connector.cursor()

	if os.path.exists(OUTPUT_DIR+'Forum'+str(forum)+'/raw_cites_'+str(forum)+'.pickle'):
		print "%s Forum %s. Reading cites from disk"%(datetime.now().strftime(tsFormat),forum)
		cites=pickle.load(open(OUTPUT_DIR+'Forum'+str(forum)+'/raw_cites_'+str(forum)+'.pickle','r'))
	else:
		print "%s Forum %s. Querying DB for cites"%(datetime.now().strftime(tsFormat),forum)
		# Query to get all the citers
		query=('SELECT t."IdThread",p1."Author",p2."Author",p1."Content",p2."Timestamp" FROM "Post" p1, "Post" p2, "Thread" t WHERE t."parsed" AND t."Forum"=%s AND p1."Thread"=p2."Thread" AND t."IdThread"=p1."Thread" AND p1."IdPost"=ANY(p2."CitedPost") AND NOT p2."Author"=p1."Author"  AND  p1."Site"=%s AND p2."Site"=%s and t."Site"=%s');
		data=(forum,SITE,SITE,SITE) 
		cursor.execute(query,data)
		cites=cursor.fetchall()
		cursor.close()
		pickle.dump(cites,open(OUTPUT_DIR+'Forum'+str(forum)+'/raw_cites_'+str(forum)+'.pickle','wb'))

	print "%s Forum %s. Fetched %s cites"%(datetime.now().strftime(tsFormat),forum,len(cites))
	count=0
	for (tid,author,replier,content,timestamp) in cites:
		count+=1
		# Be Verbose
		if count%100 == 0 or count==len(cites):
			progress = round(count*100.0/len(cites),2)
			sys.stdout.write("%s Processing cite %s (%s %s) \r"%(datetime.now().strftime(tsFormat), count,progress,'%'))
			sys.stdout.flush()
		
		# Update the responses data
		if author in responses.keys():
			if replier in responses[author].keys():
				responses[author][replier]+=1
			else:
				responses[author][replier]=1
		else:
			responses[author]={}
			responses[author][replier]=1

	print
	if os.path.exists(OUTPUT_DIR+'Forum'+str(forum)+'/raw_responses_'+str(forum)+'.pickle'):
		print "%s Forum %s. Reading responses from disk"%(datetime.now().strftime(tsFormat),forum)
		raw_responses=pickle.load(open(OUTPUT_DIR+'Forum'+str(forum)+'/raw_responses_'+str(forum)+'.pickle','r'))			
	else:
		cursor=connector.cursor()
		print "%s Forum %s. Getting responses"%(datetime.now().strftime(tsFormat),forum)
		# Query to get all the repliers that do not cite a previous post
		query=('SELECT t."IdThread",t."NumPosts",t."Heading",t."Author", p."Author",p."IdPost" FROM "Thread" t, "Post" p   WHERE  t."parsed" AND t."Forum"=%s AND -1=ALL(p."CitedPost")  AND p."Thread"=t."IdThread" AND NOT t."Author"=p."Author"  AND t."Site"=%s AND p."Site"=%s');
		data=(forum,SITE,SITE)
		cursor.execute(query,data)
		raw_responses=cursor.fetchall()
		pickle.dump(raw_responses,open(OUTPUT_DIR+'Forum'+str(forum)+'/raw_responses_'+str(forum)+'.pickle','wb'))
		cursor.close()			
	print "%s Year %s. Fetched %s responses"%(datetime.now().strftime(tsFormat),forum,len(raw_responses))
	
	count=0
	
	for (tid,numPosts,heading,author,replier,idPost) in raw_responses:
		count+=1
		# Be Verbose
		if count%100 == 0 or count==len(raw_responses):
			progress = round(count*100.0/len(raw_responses),2)
			sys.stdout.write("%s Processing response %s (%s %s) \r"%(datetime.now().strftime(tsFormat), count,progress,'%'))
			sys.stdout.flush()
		
		# Update the responses data
		if author in responses.keys():
			if replier in responses[author].keys():
				responses[author][replier]+=1
			else:
				responses[author][replier]=1
		else:
			responses[author]={}
			responses[author][replier]=1
	print
	print "%s FINISHED PROCESSING FORUM %s"%(datetime.now().strftime(tsFormat),forum)
	pickle.dump(responses, open(OUTPUT_DIR+'Forum'+str(forum)+"/responses_"+str(forum)+".pickle", "wb" ))
	connector.close()
	return responses


def getUsersResponsesALL():
	allResponses=defaultdict(dd)
	for year in range(2008,2018):
		if os.path.exists(OUTPUT_DIR+'responses_'+str(year)+'.pickle'):
			print "%s Reading responses of year %s from file"%(datetime.now().strftime(tsFormat),year)
			responses=pickle.load(open(OUTPUT_DIR+'responses_'+str(year)+'.pickle','r'))
			print "%s Processing responses of year %s"%(datetime.now().strftime(tsFormat),year)
			for author in responses.keys():
				for replier in responses[author].keys():
					allResponses[author][replier]+=responses[author][replier]
		else:
			print "%s ERROR. Responses for year %s not found"%year
	pickle.dump(allResponses,open(OUTPUT_DIR+'allResponses.pickle','wb'))

# Generate the Digraph based on the user responses
def generateRelationshipGraphALL():
	print "%s Generating relationship graph for all the forum"%(datetime.now().strftime(tsFormat)) 
	if os.path.exists(OUTPUT_DIR+'allResponses.pickle'):
		print "%s Reading responses from file"%datetime.now().strftime(tsFormat)
		responses=cPickle.load(open(OUTPUT_DIR+'/allResponses.pickle','r'))
	else:
		print "%s Responses not found in disk. You should generate them first"%(datetime.now().strftime(tsFormat))	
	g=nx.DiGraph()
	nodes=set([])
	nReplies=[]
	print "%s Calculating nodes"%(datetime.now().strftime(tsFormat))
	for author in responses.keys():
		#if not author in nodes:
		nodes.add(author)
		for replier in responses[author].keys():
		#if not replier in nodes:
				nodes.add(replier)
	print "%s Adding %s nodes"%(datetime.now().strftime(tsFormat),len(nodes))
	g.add_nodes_from(list(nodes))
	for author in responses.keys():
		for replier in responses[author].keys():
			g.add_edge (replier,author,weight=responses[author][replier])
	print "%s Saving to disk"%(datetime.now().strftime(tsFormat))
	cPickle.dump(g,open(OUTPUT_DIR+"responsesGraphALL.pickle",'wb'))
	

# Generate the Digraph based on the user responses for a given year
def generateRelationshipGraphYear(year):
	print "%s Generating relationship graph of year %s"%(datetime.now().strftime(tsFormat),year) 
	if os.path.exists(OUTPUT_DIR+'/responses_'+str(year)+'.pickle'):
		print "%s Reading responses from file"%datetime.now().strftime(tsFormat)
		responses=pickle.load(open(OUTPUT_DIR+'/responses_'+str(year)+'.pickle','r'))
	else:
		print "%s Responses for year %s not found in disk. You should generate them first"%(datetime.now().strftime(tsFormat),year)	
	g=nx.DiGraph()
	nodes=[]
	nReplies=[]
	print "%s Generating graph of year %s"%(datetime.now().strftime(tsFormat),year)
	for author in responses.keys():
		if not author in nodes:
			nodes.append(author)
		for replier in responses[author].keys():
				if not replier in nodes:
					nodes.append(replier)
	print "%s Num nodes: %s"%(datetime.now().strftime(tsFormat),len(nodes))
	g.add_nodes_from(nodes)
						
	for author in responses.keys():
		for replier in responses[author].keys():
			g.add_edge (replier,author,weight=responses[author][replier])
	nx.write_gpickle(g, OUTPUT_DIR+"/responsesGraph_"+str(year)+".pickle")

# Generate the Digraph based on the user responses for a given forum
def generateRelationshipGraphForum(forum):
	print "%s Generating relationship graph of forum %s"%(datetime.now().strftime(tsFormat),forum) 
	if os.path.exists(OUTPUT_DIR+'Forum'+str(forum)+'/responses_'+str(forum)+'.pickle'):
		print "%s Reading responses from file"%datetime.now().strftime(tsFormat)
		responses=pickle.load(open(OUTPUT_DIR+'Forum'+str(forum)+'/responses_'+str(forum)+'.pickle','r'))
	else:
		print "%s Obtaining responses"%datetime.now().strftime(tsFormat)
		responses=getUsersResponsesForum(forum)		
	g=nx.DiGraph()
	nodes=[]
	nReplies=[]
	for author in responses.keys():
		if not author in nodes:
			nodes.append(author)
		for replier in responses[author].keys():
				if not replier in nodes:
					nodes.append(replier)
	print "%s Num nodes: %s"%(datetime.now().strftime(tsFormat),len(nodes))
	g.add_nodes_from(nodes)
						
	for author in responses.keys():
		for replier in responses[author].keys():
			g.add_edge (replier,author,weight=responses[author][replier])
	nx.write_gpickle(g, OUTPUT_DIR+'Forum'+str(forum)+"/responsesGraph_"+str(forum)+".pickle")

def computeMetricsGraphAll(verbose=False):
	print "%s Reading graph of all years"%(datetime.now().strftime(tsFormat))
	G=nx.read_gpickle(OUTPUT_DIR+"responsesGraphALL.pickle")
	G.remove_node(-1)
	if verbose:
		print 'Number of nodes: %s'%nx.number_of_nodes(G)
		print 'Number of edges: %s'%nx.number_of_edges(G)
	filename=OUTPUT_DIR+'degreeCentralityAll.pickle'
	if os.path.exists(filename):
		degree_centrality=pickle.load(open(filename))
	else:
		print "%s Calculating degree centrality"%(datetime.now().strftime(tsFormat))
		degree_centrality=nx.degree_centrality(G)
		pickle.dump(degree_centrality,open(filename,'wb'))

	filename=OUTPUT_DIR+'indegreeCentralityAll.pickle'
	if os.path.exists(filename):
		indegree_centrality=pickle.load(open(filename))
	else:
		print "%s Calculating indegree centrality"%(datetime.now().strftime(tsFormat))
		indegree_centrality=nx.in_degree_centrality(G)
		pickle.dump(indegree_centrality,open(filename,'wb'))		

	filename=OUTPUT_DIR+'outdegreeCentralityAll.pickle'
	if os.path.exists(filename):
		outdegree_centrality=pickle.load(open(filename))
	else:		
		print "%s Calculating outdegree centrality"%(datetime.now().strftime(tsFormat))
		outdegree_centrality=nx.out_degree_centrality(G)
		pickle.dump(outdegree_centrality,open(filename,'wb'))
	
	filename=OUTPUT_DIR+'eigenvectorCentralityAll.pickle'
	if os.path.exists(filename):
		eigenvector_centrality=pickle.load(open(filename))
	else:	
		print "%s Calculating eigenvector centrality"%(datetime.now().strftime(tsFormat))
		eigenvector_centrality=nx.eigenvector_centrality(G)
		pickle.dump(eigenvector_centrality,open(filename,'wb'))


# Analyze the graph to get centrality measures
def analyzeGraph(forum,N=10):
	if forum==-1:
		print "%s Reading graph of all years %s"%(datetime.now().strftime(tsFormat))
		G=nx.read_gpickle(OUTPUT_DIR+"responsesGraphALL.pickle")		
	else:
		G=nx.read_gpickle(OUTPUT_DIR+'Forum'+str(forum)+"/responsesGraph_"+str(forum)+".pickle")
	
	G.remove_node(-1)	

	
	degree_centrality=nx.degree_centrality(G)
	sorted_centrality=sorted(degree_centrality.items(),key=operator.itemgetter(1),reverse=True)
	if N>0:
		print "TOP %s MEMBERS BY DEGREE:"%N
		print "Author - Measure - Earnings - RankEarnings"
		print "Author,Degree,Eigenvector"
		for member,degree in sorted_centrality[:N]:
			#position,earnings=getEarningsAndRelativePosition(member)	
			print "%s - %s "%(member,degree)
		# for member,degree in sorted_centrality[:N]:	
		# 	print "%s,"%member,
		# print
	indegree_centrality=nx.in_degree_centrality(G)
	sorted_centrality=sorted(indegree_centrality.items(),key=operator.itemgetter(1),reverse=True)
	if N>0:
		print "TOP %s MEMBERS BY IN_DEGREE:"%N
		print "Author - Measure - Earnings - RankEarnings"
		for member,degree in sorted_centrality[:N]:
			print "%s - %s"%(member,degree)
	outdegree_centrality=nx.out_degree_centrality(G)
	sorted_centrality=sorted(outdegree_centrality.items(),key=operator.itemgetter(1),reverse=True)
	if N>0:
		print "TOP %s MEMBERS BY OUT_DEGREE:"%N
		print "Author - Measure - Earnings - RankEarnings"
		for member,degree in sorted_centrality[:N]:
			print "%s - %s"%(member,degree)
	eigenvector_centrality=nx.eigenvector_centrality(G)
	sorted_centrality=sorted(eigenvector_centrality.items(),key=operator.itemgetter(1),reverse=True)
	if N>0:
		print "TOP %s MEMBERS BY EIGENVECTOR:"%N
		print "Author - Measure - Earnings - RankEarnings"
		for member,degree in sorted_centrality[:N]:
			print "%s - %s"%(member,degree)

	return degree_centrality,indegree_centrality,outdegree_centrality,eigenvector_centrality,betweenness_centrality,closeseness_centrality



def getColorRelationship(quantity):
	if quantity>5:
		return 'green'
	if quantity>0:
		return 'yellow'
	if quantity==0:
		return 'black'
	if quantity<0:
		return 'orange'
	if quantity<-5:
		return 'red'


# Estimates the sentiment of a relationship based on the reputation votes given. This method calculates the sum of reputation given to a list of authors given as parameter
def getSentiments(actorList,positive=True):
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
	filename=OUTPUT_DIR+'sentimentRelationships.pickle'
	if os.path.exists(filename):
		relationship,processedActors=pickle.load(open(filename))
	else:
		relationship={}	
		processedActors=[]
	if len (actorList)==0:
		query=('SELECT "IdMember" FROM "Member" WHERE "Site"=%s'%SITE)
		cursor = connector.cursor()
		cursor.execute(query)
		rows=cursor.fetchall()
		actorList=[r[0] for r in rows]
	toProcess=[actor for actor in actorList if not actor in processedActors]
	for idMember in toProcess:
		print "%s Processing member %s. Querying DB for reputation votes received"%(datetime.now().strftime(tsFormat),idMember)
		query=('SELECT Sum("Quantity"),"Donor" FROM "ReputationVotes" WHERE "Receiver"=%s AND "Site"=%s GROUP BY "Donor" ORDER BY Sum("Quantity") DESC')
		cursor = connector.cursor()
		data=(idMember,SITE)
		cursor.execute(query,data)
		repVotes=cursor.fetchall()
		for (quantity,donor) in repVotes:
			if not donor in relationship.keys():
				relationship[donor]={}
			relationship[donor][idMember]=quantity
		print "%s Processing member %s. Querying DB for reputation votes given"%(datetime.now().strftime(tsFormat),idMember)	
		query=('SELECT Sum("Quantity"),"Receiver" FROM "ReputationVotes" WHERE "Donor"=%s AND "Site"=%s GROUP BY "Receiver" ORDER BY Sum("Quantity") DESC')
		data=(idMember,SITE)
		cursor.execute(query,data)
		repVotes=cursor.fetchall()
		if not idMember in relationship.keys():
			relationship[idMember]={}
		for (quantity,receiver) in repVotes:
			relationship[idMember][receiver]=quantity
		processedActors.append(idMember)
		cursor.close()
	print "%s Dumping relationship to file %s"%(datetime.now().strftime(tsFormat),filename)
	pickle.dump((relationship,processedActors),open(filename,'wb'))


# Obtains the data to calculate the evolution of the idMember given as parameter
def memberEvolution(idMember,networks):
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
	TOP_NEIGHBORS=5
	query=('SELECT "RegistrationDate","LastVisitDue","LastPostDate" FROM "Member" WHERE "IdMember"=%s AND "Site"=%s')
	cursor = connector.cursor()
	data=(idMember,SITE)
	cursor.execute(query,data)
	row=cursor.fetchone()
	if not row:
		print "%s Member %s not found in Site %s "%(datetime.now().strftime(tsFormat), idMember,SITE)
		return
	regDate=row[0]
	lastVisit=row[1]
	lastPost=row[2]
	# If last visit is hidden, then use the last post
	if lastVisit.strftime("%Y")[:2]=='19' or lastVisit<lastPost:
		lastVisit=lastPost
	initYear=int(regDate.strftime("%Y"))
	endYear=int(lastVisit.strftime("%Y"))
	# 2018 is still not processed
	if endYear==2018:
		endYear=2017
	print "%s Processing Member %s. Init year:%s, End year:%s"%(datetime.now().strftime(tsFormat), idMember,initYear,endYear)
	print "%s Processing Member %s. Reading personal interests"%(datetime.now().strftime(tsFormat), idMember)
	selfInterestsF,selfInterestsC=getInterests(idMember,0,OUTPUT_DIR_INTEREST,verbose=False,calculateCategories=True)
	interestsNeighborsCategories={}
	for year in range(initYear,endYear+1):
		addedNeighbors=[]
		networkName='network_'+str(year)+'_'+str(idMember)
		if os.path.exists(OUTPUT_DIR_LOCAL_NETWORKS+networkName+".pickle"):
			print "%s Processing Member %s. Year %s. Reading local network from file"%(datetime.now().strftime(tsFormat), idMember,year)
			localGraphUser=cPickle.load(open(OUTPUT_DIR_LOCAL_NETWORKS+networkName+".pickle"))
		else:
			G=networks[year]
			if not idMember in list(G):
				print "%s WARNING Processing Member %s. Year %s. Member has no interactions in this year"%(datetime.now().strftime(tsFormat), idMember,year)
				continue;
			localGraphUser=nx.DiGraph()		
			filename=OUTPUT_DIR_LOCAL_NETWORKS+"pieChart_"+str(year)+"_"+str(idMember)+".png"
			if not os.path.exists(filename):
				print "%s Processing Member %s. Year %s. Creating pieChart of self-interests"%(datetime.now().strftime(tsFormat), idMember,year)
				if year in selfInterestsC.keys():
					plotPieChart (selfInterestsC[year],filename,str(idMember)+"_"+str(year))
					localGraphUser.add_node(idMember,shape='None',label="",image=filename)
				else:
					print "%s WARNING Processing Member %s. Year %s. Member does not have self interests"%(datetime.now().strftime(tsFormat), idMember,year)
			else:
				print "%s Processing Member %s. Year %s. pieChart already present"%(datetime.now().strftime(tsFormat), idMember,year)
			print "%s Processing Member %s. Year %s. Reading interests of TOP %s successors"%(datetime.now().strftime(tsFormat), idMember,year,TOP_NEIGHBORS)
			aggregatedCats=defaultdict(lambda:0)
			successors=list(G.successors(idMember))
			successors=[(s,G.get_edge_data(idMember,s)['weight']) for s in successors if not s==1 and not s==-1]
			ordered=sorted(successors,key=operator.itemgetter(1),reverse=True)		
			for neighbor,weight in ordered[:TOP_NEIGHBORS]:
				filename=OUTPUT_DIR_LOCAL_NETWORKS+"pieChart_"+str(year)+"_"+str(neighbor)+".png"
				if not os.path.exists(filename):
					print "%s Processing Member %s. Reading interests of neighbor %s"%(datetime.now().strftime(tsFormat), idMember,neighbor)
					interestNeighborF,interestNeighborC=getInterests(neighbor,0,OUTPUT_DIR_INTEREST,verbose=False,calculateCategories=True)
					if year in interestNeighborC.keys():
						for cat in interestNeighborC[year]:
							aggregatedCats[cat]+=interestNeighborC[year][cat]
						print "%s Processing Member %s. Creating pieChart of neighbor %s"%(datetime.now().strftime(tsFormat), idMember,neighbor)
						
						plotPieChart (interestNeighborC[year],filename,str(neighbor)+"_"+str(year))
					else:
						print "%s WARNING Processing Member %s. Year %s. Neighbor %s does not have interests. Keys:%s"%(datetime.now().strftime(tsFormat), idMember,year,neighbor,interestNeighborC.keys())
				else:
					print "%s Processing Member %s. Year %s. pieChart of neighbor %s already present"%(datetime.now().strftime(tsFormat), idMember,year,neighbor)
				if not neighbor in addedNeighbors:
					localGraphUser.add_node(neighbor,shape='box',label="",image=filename)				
					addedNeighbors.append(neighbor)
				localGraphUser.add_edge(idMember,neighbor,weight=weight)
			print "%s Processing Member %s. Year %s. Reading interests of TOP %s predecessors"%(datetime.now().strftime(tsFormat), idMember,year,TOP_NEIGHBORS)
			predecessors=list(G.predecessors(idMember))
			predecessors=[(s,G.get_edge_data(s,idMember)['weight']) for s in predecessors if not s==1 and not s==-1]
			ordered=sorted(predecessors,key=operator.itemgetter(1),reverse=True)				
			for neighbor,weight in ordered[:TOP_NEIGHBORS]:
				filename=OUTPUT_DIR_LOCAL_NETWORKS+"pieChart_"+str(year)+"_"+str(neighbor)+".png"
				if not os.path.exists(filename):
					print "%s Processing Member %s. Reading interests of neighbor %s"%(datetime.now().strftime(tsFormat), idMember,neighbor)
					interestNeighborF,interestNeighborC=getInterests(neighbor,0,OUTPUT_DIR_INTEREST,verbose=False,calculateCategories=True)
					if year in interestNeighborC.keys():
						for cat in interestNeighborC[year]:
							aggregatedCats[cat]+=interestNeighborC[year][cat]
						print "%s Processing Member %s. Creating pieChart of neighbor %s"%(datetime.now().strftime(tsFormat), idMember,neighbor)
						plotPieChart (interestNeighborC[year],filename,str(neighbor)+"_"+str(year))					
					else:
						print "%s WARNING Processing Member %s. Year %s. Neighbor %s does not have interests"%(datetime.now().strftime(tsFormat), idMember,year,neighbor)
				else:
					print "%s Processing Member %s. Year %s. pieChart of neighbor %s already present"%(datetime.now().strftime(tsFormat), idMember,year,neighbor)				

				if not neighbor in addedNeighbors:
					localGraphUser.add_node(neighbor,shape='box',label="",image=filename)				
					addedNeighbors.append(neighbor)
				localGraphUser.add_edge(neighbor,idMember,weight=weight)
			filename=OUTPUT_DIR_LOCAL_NETWORKS+"pieChart_"+str(year)+"_neighborsMember_"+str(idMember)+".png"
			if not os.path.exists(filename):				
				plotPieChart (aggregatedCats,filename,"NeighborsMember_"+str(idMember)+"_"+str(year))					
			print "%s Processing Member %s. Year %s. Saving network to disk"%(datetime.now().strftime(tsFormat),idMember,year)
			cPickle.dump(localGraphUser,open(OUTPUT_DIR_LOCAL_NETWORKS+networkName+".pickle",'wb'))
		print "%s Processing Member %s. Year %s. Writing network to dot file"%(datetime.now().strftime(tsFormat),idMember,year)
		write_dot(localGraphUser, OUTPUT_DIR_LOCAL_NETWORKS+networkName+".dot")
		

# Calculates the correlation of different measures from the social graph of the given forum
def spearmanCorrelation(forum):
	metrics=calculateImpactMetrics(forun)
	degree_cent,indegree_cent,outdegree_cent,eigenvector_cent=analyzeGraph(forum)
	#numThreads,totalCites,h,h10,h50,h100,degree_cent,indegree_cent,outdegree_cent
	array=[]
	for author in metrics.keys():
		if author in degree_cent.keys():
			row=[metrics[author]['numThreads'],metrics[author]['totalCites'],metrics[author]['h'],metrics[author]['h10'],metrics[author]['h50'],metrics[author]['h100'],degree_cent[author],indegree_cent[author],outdegree_cent[author],eigenvector_cent[author]]
			array.append(row)
		else:
			"Author %s does not have centrality measure"%author
	rho, pval=stats.spearmanr(array)
	print "SPEARMAN RHO"
	print rho
	print "SPEARMAN pValue"
	print pval

# Given a string with the content of the post, removes LINKS, CITING, IFRAME,IMAGES and CODE AND ALSO PUTS EVERYTHING ON A SINGLE LINE
def removeRichDataFromContent(content):
	toClean=["***IMG***","***LINK***","***CITING***","***IFRAME***","***CODE***"]
	cleanedData=content
	for item in toClean:
		tmp=cleanedData
		if item in tmp:
			cleanedData=""
			n=0     
			for e in tmp.split(item):
				if n%2 == 0:
					cleanedData+=e+" "
				n+=1
	#cleanedData=cleanedData.replace('[','').replace(']','')
	return " ".join([s for s in cleanedData.splitlines() if s.strip()])

#Cleans a document: Get only nouns, remove stop words and punctuation characters and lemmatize the words using NLTK
def clean(doc):
	#print doc
	tags=nltk.pos_tag(nltk.word_tokenize(doc.decode('utf-8')))
	nouns=''
	for word,tag in tags:
		if 'NN' in tag:
			nouns+=word+" "
	stop_free = " ".join([i for i in nouns.lower().split() if i not in stop])
	punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
	normalized=""
	for word in punc_free.split():
		if not 'whore' in word and not 'whoring' in word and word!='e':
			try:
				normalized += " "+lemma.lemmatize(word)
			except:
				pass;
	return normalized


#Applies Louvain Method to find the optimal partition of subcommunities for the forum graph
def findSubcommunities(forum):
	G=nx.read_gpickle(OUTPUT_DIR+'Forum'+str(forum)+"/responsesGraph_"+str(forum)+".pickle").to_undirected()
	#metrics=calculateImpactMetrics(forum)
	degree_centrality=nx.degree_centrality(G)
	if os.path.exists(OUTPUT_DIR+'Forum'+str(forum)+'/subcommunities-'+str(forum)+'.pickle'):
		print "%s Forum %s. Reading Louvain subcommunities from disk"%(datetime.now().strftime(tsFormat),forum)
		partition=pickle.load(open(OUTPUT_DIR+'Forum'+str(forum)+'/subcommunities-'+str(forum)+'.pickle'))
	else:
		print "%s Forum %s. Calculating subcommunities using Louvain"%(datetime.now().strftime(tsFormat),forum)
		partition = community.best_partition(G)
		pickle.dump(partition,open(OUTPUT_DIR+'Forum'+str(forum)+'/subcommunities-'+str(forum)+'.pickle','wb'))
	print "%s Louvain Modularity: "%datetime.now().strftime(tsFormat), community.modularity(partition, G)
	communities=set(partition.values())
	print "%s Num communities: %s"%(datetime.now().strftime(tsFormat),len(communities))
	for com in set(partition.values()) :
		list_nodes = [nodes for nodes in partition.keys() if partition[nodes] == com]
		#print '\tSubcommunity %s  = %s members'%(com,len(list_nodes))
	return partition

# Given a list of members, returns the LDA model of the topics for this members in the headings only (if onlyThreads) or also in the contents of the posts
def topicModelling(members,forum,onlyThreads=False,verbose=True,numTopics=7):
	# List of all the documents for these members
	doc_complete=[]
	for member in members:
		if onlyThreads:
			fileName=OUTPUT_DIR+'Forum'+str(forum)+'/headingAndFirstPost_'+str(forum)+'_'+str(member)+'.pickle'
		else:
			fileName=OUTPUT_DIR+'Forum'+str(forum)+'/contentHeadings_'+str(forum)+'_'+str(member)+'.pickle'
		if os.path.exists(fileName):
			if verbose:
				print "%s Forum %s. Reading headings/posts of member %s from disk"%(datetime.now().strftime(tsFormat),forum,member)
			documents=pickle.load(open(fileName))
		else:
			connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
			documents=[]		
			cursor = connector.cursor()
			if verbose:
				print "%s Forum %s. Querying DB for thread headings of member %s"%(datetime.now().strftime(tsFormat),forum,member)
			# Query to get all the citers
			query=('SELECT "Heading" FROM "Thread" WHERE "Forum"=%s AND "Author"=%s AND "Site"=%s');
			data=(forum,member,SITE) 
			cursor.execute(query,data)
			threads=cursor.fetchall()
			for t in threads:
				documents.append(t[0])
			if verbose:
				print "%s Forum %s. Querying DB for post contents of member %s"%(datetime.now().strftime(tsFormat),forum,member)
			# Query to get all the citers
			query=('SELECT "Post"."Content","Post"."Author","Post"."IdPost" FROM "Post","Thread" WHERE "Thread"="IdThread" AND "Forum"=%s AND "Post"."Author"=%s AND "Post"."Site"=%s AND "Thread"."Site"=%s ORDER BY "IdPost" ASC');
			data=(forum,member,SITE,SITE) 
			cursor.execute(query,data)
			posts=cursor.fetchall()
			if not onlyThreads:
				for p in posts:
					documents.append(removeRichDataFromContent(p[0]))
			else:
				for p in posts:
					if int(p[1])==member:
						documents.append(removeRichDataFromContent(p[0]))
						break;		
			pickle.dump(documents,open(fileName,'wb'))
		doc_complete.extend(documents)

	if verbose:
		print "%s Forum %s. Preprocessing documents"%(datetime.now().strftime(tsFormat),forum)		
	
	doc_clean = [clean(doc).split() for doc in doc_complete] 

	dictionary = corpora.Dictionary(doc_clean)

	doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
	if verbose:
		print "%s Forum %s. Applying LDA modelling. Matrix size:%s"%(datetime.now().strftime(tsFormat),forum,len(doc_term_matrix))		
	LDA = gensim.models.ldamulticore.LdaMulticore
	ldamodel = LDA(doc_term_matrix, num_topics=numTopics, id2word = dictionary,workers=4,passes=20)
	return ldamodel

# Aggregates top users per sub-community and obtains the topics from their threads or threads and posts
def topicsPerCommunity(forum,onlyThreads=True):
	G=nx.read_gpickle(OUTPUT_DIR+'Forum'+str(forum)+"/responsesGraph_"+str(forum)+".pickle").to_undirected()
	partition=findSubcommunities(forum)
	metrics=calculateImpactMetrics(forum)
	degree_centrality=nx.degree_centrality(G)
	communities=set(partition.values())
	for com in communities:
		popularity={}
		# Get the list of nodes of this community and calculates their popularity
		list_nodes = [nodes for nodes in partition.keys() if partition[nodes] == com]
		if len(list_nodes)>10:
			for member in list_nodes:
				if member in metrics.keys():
					popularity[member]=metrics[member]['h']
				#if member in degree_centrality.keys():
					#popularity[member]=degree_centrality[member]
			sorted_popularity=sorted(popularity.items(), key=operator.itemgetter(1),reverse=True)
			if len(list_nodes)>50:
				N=50
			else: 
				N=len(list_nodes)
			topics_members=[]
			for member,h in sorted_popularity[:N]:
				#print "\tMember %s popularity %s:"%(member,h)
				topics_members.append(member)
			if onlyThreads:
				prefix='LDAModelThreads_Forum'
			else:
				prefix='LDAModel_Forum'
			if os.path.exists(OUTPUT_DIR+'Forum'+str(forum)+'/'+prefix+str(forum)+'_Community-'+str(com)+'.pickle'):
				LDA_model=pickle.load(open(OUTPUT_DIR+'Forum'+str(forum)+'/ldaModel_Forum-'+str(forum)+'_Community-'+str(com)+'.pickle'))
			else:
				LDA_model=topicModelling(topics_members,forum,onlyThreads=onlyThreads,verbose=True)
				pickle.dump(LDA_model,open(OUTPUT_DIR+'Forum'+str(forum)+'/'+prefix+str(forum)+'_Community-'+str(com)+'.pickle','wb'))
			
			allWords=[]
			print "\tCommunity %s (%s member). Topics: "%(com,len(list_nodes))
			for topic in LDA_model.show_topics(num_topics=-1, num_words=7):
				print topic
				for word,prob in LDA_model.show_topic(topic[0],topn=7):
					allWords.append(word)
			print
		
		#for word in set(allWords):
		#	print "%s,"%word,
		#print

	#print "Louvain Partition: ", partition

# Extracts the topics of a list of members using LDA and dumps the results in a pickle file
def getTopics(filename,memberList):
	forum=-1
	numTopics=4
	onlyThreads=True
	if os.path.exists(filename):
		topics=pickle.load(open(filename))
	else:
		topics={}
	for c,member in enumerate(memberList):
		print "%s Processing member %s (%s/%s)"%(datetime.now().strftime(tsFormat),member,c,len(memberList))
		if not member in topics.keys():
			topics[member]=[]
			LDA_model=topicModelling([member],forum,onlyThreads=onlyThreads,verbose=False,numTopics=numTopics)
			#print "Member %s. Topics: "%keyActorsOriginal[member]
			for topic in LDA_model.print_topics(num_topics=-1, num_words=7):
				for t in topic[1].split('+'):
					term=t.split("*")[1].replace('"','')
					topics[member].append(term)
		else:
			print "%s WARNING. Member %s already processed"%(datetime.now().strftime(tsFormat),member)
	pickle.dump(topics,open(filename,'wb'))
	return topics

# Compare the list of topics from the key actors to detect potential key actors involved in cybercrime activities
def showTopicsMembers(potentialSet,printTerms=False):
	MIN_TIMES_TO_PRINT=6
	THRESHOLD_NUM_CRIME_KEYWORDS=2
	THRESHOLD_DISTANCE=0.2

	# Write here the list of ids of identified key actors
	listKeyActors=[]

	# Put here the list of members identified by Clustering
	allMembersPotentialClusteringUnfiltered=[]

	# Put here the list of members identified by Logistic Regression
	allMembersPotentialLogisticRegressionUnfiltered=[]

	# Put here the list of members identified by Social Network Analysis
	allMembersPotentialSNAUnfiltered=[]

	# Remove those that are already identified as key actors
	allMembersPotentialClusteringUnfiltered=[f for f in allMembersPotentialClusteringUnfiltered if not f in listKeyActors]
 	allMembersPotentialLogisticRegressionUnfiltered=[f for f in allMembersPotentialLogisticRegressionUnfiltered if not f in listKeyActors]
 	allMembersPotentialSNAUnfiltered=[f for f in allMembersPotentialSNAUnfiltered if not f in listKeyActors]

 	# Get overlaps
 	allPotentialMembersCommon=[m for m in allMembersPotentialSNAUnfiltered if m in allMembersPotentialLogisticRegressionUnfiltered and m in allMembersPotentialSNAUnfiltered]
	allPotentialMembersCommon_LR_C=[m for m in allMembersPotentialClusteringUnfiltered if m in allMembersPotentialLogisticRegressionUnfiltered and not m in allPotentialMembersCommon]
	allPotentialMembersCommon_SNA_C=[m for m in allMembersPotentialClusteringUnfiltered if m in allMembersPotentialSNAUnfiltered and not m in allPotentialMembersCommon]
	allPotentialMembersCommon_LR_SNA=[m for m in allMembersPotentialSNAUnfiltered if m in allMembersPotentialLogisticRegressionUnfiltered and not m in allPotentialMembersCommon]

	# Get uniques 

	allMembersPotentialLogisticRegression=[f for f in allMembersPotentialLogisticRegressionUnfiltered if not f in allMembersPotentialSNAUnfiltered and not f in allMembersPotentialClusteringUnfiltered]
	allMembersPotentialSNA=[f for f in allMembersPotentialSNAUnfiltered if not f in allMembersPotentialLogisticRegressionUnfiltered and not f in allMembersPotentialClusteringUnfiltered]
	allMembersPotentialClustering=[f for f in allMembersPotentialClusteringUnfiltered if not f in allMembersPotentialLogisticRegressionUnfiltered and not f in allMembersPotentialSNAUnfiltered]

	# Print stats
	print "listKeyActors: %s"%len(listKeyActors)
	print "allMembersPotentialClusteringUnfiltered: %s"%len(allMembersPotentialClusteringUnfiltered)
	print "allMembersPotentialLogisticRegressionUnfiltered: %s"%len(allMembersPotentialLogisticRegressionUnfiltered)
	print "allMembersPotentialSNAUnfiltered: %s"%len(allMembersPotentialSNAUnfiltered)
	print "allMembersPotentialClustering: %s"%len(allMembersPotentialClustering)
	print "allMembersPotentialSNA: %s"%len(allMembersPotentialSNA)
	print "allMembersPotentialLogisticRegression: %s"%len(allMembersPotentialLogisticRegression)
	print "allPotentialMembersCommon_LR_C: %s"%len(allPotentialMembersCommon_LR_C)
	print "allPotentialMembersCommon_SNA_C: %s"%len(allPotentialMembersCommon_SNA_C)
	print "allPotentialMembersCommon_LR_SNA: %s"%len(allPotentialMembersCommon_LR_SNA)
	print "allPotentialMembersCommon: %s"%len(allPotentialMembersCommon)
	
	filename=OUTPUT_DIR+"topicsActors.pickle"
	if not os.path.exists(filename):
		topics=getTopics(filename,listKeyActors)
	else:
		topics=pickle.load(open(filename))

	# Define the set to analyse depending on the parameter
	if potentialSet=="LOGISTIC_REGRESSION":
		allPotentialMembers=allMembersPotentialLogisticRegression
	elif potentialSet=='SNA':
		allPotentialMembers=allMembersPotentialSNA		
	elif potentialSet=="CLUSTERING":
		allPotentialMembers=allMembersPotentialClustering
	elif potentialSet=='COMMON-LR-C':
		allPotentialMembers=allPotentialMembersCommon_LR_C
	elif potentialSet=='COMMON-SNA-C':
		allPotentialMembers=allPotentialMembersCommon_SNA_C		
	elif potentialSet=='COMMON-LR-SNA':
		allPotentialMembers=allPotentialMembersCommon_LR_SNA		
	elif potentialSet=='COMMON':		
		allPotentialMembers=allPotentialMembersCommon
	if len (allPotentialMembers)==0:
		print "%s has no common members"%potentialSet
		return
	


	# Get the topics for the set of key actors and the set of potential
	listTopicsKA=[]
	listTopicsPotential=[]
	for member in topics.keys():
		for topic in topics[member]:
			if len(topic.strip())>1 and not "★" in topic:
				if member in listKeyActors:
					if not topic in listTopicsKA:
						listTopicsKA.append(topic)
				elif member in allPotentialMembers:
					if not topic in listTopicsPotential:
						listTopicsPotential.append(topic)



	# Calculate the distances of each of the potential key actors by comparing with the topics of the key actors
	distances=defaultdict(lambda:0)
	for y in allPotentialMembers:
		distances[y]+=sum(1 for term in listTopicsKA if term in topics[y])/float(len(topics[y]))			

	# Oder distances and apply thresholds
	sortedDistances=sorted(distances.items(),key=operator.itemgetter(1),reverse=True)
	numPredicted=0
	totalDistance=0.0
	totalMatchesKeyTerm=0.0
	closest=0.0
	farthest=1.0
	predictedActors=[]
	for potentialActor,distance in sortedDistances:
		printMember=0
		toPrint="%s=%.2f\n["%(potentialActor,distance)
		totalDistance+=distance
		if distance>closest: closest=distance
		if distance<farthest: farthest=distance
		processedTerms=[]
		totalTerms=0
		keyTerms=0
		for term in topics[potentialActor]:
			if not term.strip() in processedTerms:
				totalTerms+=1
				processedTerms.append(term.strip())
				toPrint+= "%s "%term.strip()
				#if term.strip() in ['rat','bot','botnet','ddos','crypter','keylogger','bypass','hacking','hacker','hack','fud','account','shell','installs'] and not term.strip() in processedTerms:
				if term.strip() in ['rat','account','crypter','fud','bot','shell','booter','installs','ddos','darkcomet','keylogger','exploit','stealer','stresser','botnet','malware','spread']:
					keyTerms+=1 
		toPrint+= "]"
		totalMatchesKeyTerm+=keyTerms/float(totalTerms)
		
		if keyTerms>=THRESHOLD_NUM_CRIME_KEYWORDS and distance >= THRESHOLD_DISTANCE:
			numPredicted+=1
			predictedActors.append(str(potentialActor))
			if printTerms: print "******************************************************************************************************************"
		if printTerms: print toPrint
		if keyTerms>=THRESHOLD_NUM_CRIME_KEYWORDS and distance >= THRESHOLD_DISTANCE:
			if printTerms: print "******************************************************************************************************************"
		if printTerms: print
	print
	print "---------"
	print potentialSet
	print "---------"
	print "Predicted %s users out of %s (%.2f)"%(numPredicted,len(sortedDistances),(numPredicted*100.0/len(sortedDistances)))
	print "Average distance: %.2f"%(totalDistance/len(sortedDistances))
	print "Farthest distance: %.2f"%(farthest)
	print "Closest distance: %.2f"%(closest)
	print "Average matches of key terms: %.2f"%(totalMatchesKeyTerm/len(sortedDistances))
	print "%s/%s (%.2f) & %.2f & %.2f & %.2f "%(numPredicted,len(sortedDistances),(numPredicted*100.0/len(sortedDistances)),(totalDistance/len(sortedDistances)),farthest,closest)
	print "Predicted actors: \n\t%s"%(" - ".join(predictedActors))
	print



#### GLOBAL VARIABLES TO SET ###
SITE=0 # Id of the site from the CrimeBB Dataset
OUTPUT_DIR='.'
OUTPUT_DIR_LOCAL_NETWORKS=OUTPUT_DIR+'/localNetworks/'

