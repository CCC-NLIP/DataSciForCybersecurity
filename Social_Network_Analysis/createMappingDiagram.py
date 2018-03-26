# -*- coding: utf-8 -*-


# This script can be used to build a mapping diagram for visualizing the evolution of interestes of forum members (See visualizeMappingDiagram.r)
# It relies on the CrimeBB dataset.  The dataset can be obtained under legal agreement with the Cambridge Cybercrime Centre. 
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
import pickle
import os
import operator
from operator import itemgetter 
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as pyplot
from matplotlib.font_manager import FontProperties
import colorsys
from collections import defaultdict
import sys
from datetime import datetime
from getInterests import getInterests,plotPieChart

pyplot.style.use('ggplot')


tsFormat='%Y%m%d_%H%M%S'

# COMMON VARIABLES
DB_USER='dbhunter'
DB_SERVER='192.168.56.101'
DB_NAME='crimebb'

SITE=0


# Add here a list of the actors you want to consider for the visualization (key=ID, value=username)
keyActors={}

INPUT_DIR="./"
OUTPUT_DIR_INTEREST="./"

### LIST OF FORUMS PER CATEGORY ##
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

## HACKFORUMS CATEGORIES ##
HF_CATEGORIES={'common':hackforums_common,'hack':hackforums_hack,'tech':hackforums_tech,'coding':hackforums_coding,'web':hackforums_web,'gaming':hackforums_games,'market':hackforums_market,'money':hackforums_money,'graphics':hackforums_graphics}


# Obtains the data to calculate the evolution of the idMember given as parameter
def memberEvolution(idMember,TOP_CAT=3):
	global mappingDict
	initial=[]
	middle=[]
	last=[]
	connector = psycopg2.connect(user=DB_USER, host=socket.gethostbyname(DB_SERVER),database=DB_NAME)
	query=('SELECT "FirstPostDate","LastPostDate" FROM "Member" WHERE "IdMember"=%s AND "Site"=%s')
	cursor = connector.cursor()
	data=(idMember,SITE)
	cursor.execute(query,data)
	row=cursor.fetchone()
	if not row:
		print "%s ERROR Member %s not found in Site %s "%(datetime.now().strftime(tsFormat), idMember,SITE)
		return initial,middle,last
	firstPostDate=row[0]
	lastPostDate=row[1]
	initYear=int(firstPostDate.strftime("%Y"))
	lastYear=int(lastPostDate.strftime("%Y"))
	# 2018 is still not processed
	if lastYear==2018:
		lastYear=2017
	# If only one year, discard the user
	if initYear==lastYear:
		print "%s WARNING Member %s only was active one year (%s)"%(datetime.now().strftime(tsFormat), idMember,initYear)
		return initial,middle,last
	elif initYear+1==lastYear:
		print "%s WARNING Member %s has not middle year (%s-%s)"%(datetime.now().strftime(tsFormat), idMember,initYear,lastYear)
		middleYear=initYear
		initYear=-1
	else:
		middleYear=int((lastYear-initYear)/2)+initYear
		print "%s Member %s. Init:%s, Middle:%s, End:%s"%(datetime.now().strftime(tsFormat), idMember,initYear,middleYear,lastYear)
	print "%s Processing Member %s. Reading personal interests"%(datetime.now().strftime(tsFormat), idMember)

	selfInterestsF,selfInterestsC=getInterests(idMember,0,OUTPUT_DIR_INTEREST,verbose=False,calculateCategories=True)
	if initYear in selfInterestsC.keys():
		overallScore=sum(num for num in selfInterestsC[initYear].values())
		sortedCategories=sorted([(cat,(num*1.0/overallScore)) for cat,num in selfInterestsC[initYear].items() if num>0],key=operator.itemgetter(1),reverse=True)
		if len(sortedCategories)>TOP_CAT:
			top=TOP_CAT
		else:
			top=len(sortedCategories)
		#print "Init year. TOP is %s"%top
		if top>0:	
			print "\t Init year:%s"%initYear,
			for i in range(0,top):
				print "%s (%s)"%(sortedCategories[i]),
				initial.append((sortedCategories[i][0]+"  ",sortedCategories[i][1]))
			print
			
	if middleYear in selfInterestsC.keys():		
		overallScore=sum(num for num in selfInterestsC[middleYear].values())		
		sortedCategories=sorted([(cat,(num*1.0/overallScore)) for cat,num in selfInterestsC[middleYear].items() if num>0],key=operator.itemgetter(1),reverse=True)
		if len(sortedCategories)>TOP_CAT:
			top=TOP_CAT
		else:
			top=len(sortedCategories)
		#print "Middle year. TOP is %s"%top			
		if top>0:	
			print "\t Middle year:%s"%middleYear,
			for i in range(0,top):
				print "%s (%s) "%(sortedCategories[i]),
				middle.append((sortedCategories[i][0]+" ",sortedCategories[i][1]))
			print 
			
	if lastYear in selfInterestsC.keys():
		overallScore=sum(num for num in selfInterestsC[lastYear].values())
		sortedCategories=sorted([(cat,(num*1.0/overallScore)) for cat,num in selfInterestsC[lastYear].items() if num>0],key=operator.itemgetter(1),reverse=True)
		if len(sortedCategories)>TOP_CAT:
			top=TOP_CAT
		else:
			top=len(sortedCategories)
		#print "End year. TOP is %s"%top						
		if top>0:
			print "\t End year:%s"%lastYear,
			for i in range(0,top):
				print "%s (%s) "%(sortedCategories[i]),
				last.append((sortedCategories[i][0],sortedCategories[i][1]))
			print 
			
	return initial,middle,last

mappingDictInitMid=defaultdict(lambda:0)
mappingDictMidLast=defaultdict(lambda:0)
TOP=10


for k in keyActors.keys():
	initial,middle,last=memberEvolution(k,TOP_CAT=TOP)
	acum_i=0

	for posI,(cat_i,num_i) in enumerate(initial):
		print "I",acum_i
		if acum_i>0.8:
			break
		acum_i+=num_i			
		acum_m=0
		for posM,(cat_m,num_m) in enumerate(middle):
			print "m",acum_m
			if acum_m>0.8:
				break
			acum_m+=num_m
			mappingDictInitMid[(cat_i,cat_m)]+=10*(TOP-posI)*num_i+10*(TOP-posM)*num_m
			print cat_i,cat_m
	acum_m=0
	for posM,(cat_m,num_m) in enumerate(middle):	
		print "M",acum_m
		if acum_m>0.8:
			break
		acum_m+=num_m			
		acum_l=0		
		for posL,(cat_l,num_l) in enumerate(last):
			if acum_l>0.8:
				break			
			acum_l+=num_l	
			mappingDictMidLast[(cat_m,cat_l)]+=10*(TOP-posM)*num_m+10*(TOP-posL)*num_l
print mappingDictInitMid
print mappingDictMidLast

fd=open('mapping.csv','wb')
fd.write("source,target,value\n")
i=0
for (source,target),value in mappingDictInitMid.items():
	source=source.replace('hack','HHacking')
	source=source.replace('tech',"TTech")
	source=source.replace('gaming',"GGaming")
	source=source.replace('coding',"CCoding")
	source=source.replace('money',"EMoney")
	source=source.replace('graphics',"XGraphics")
	source=source.replace('market',"MMarket")
	source=source.replace('common',"YCommon")
	source=source.replace('web',"BWeb")
	target=target.replace('hack','HHacking')
	target=target.replace('tech',"TTech")
	target=target.replace('gaming',"GGaming")
	target=target.replace('coding',"CCoding")
	target=target.replace('money',"EMoney")
	target=target.replace('graphics',"XGraphics")
	target=target.replace('market',"MMarket")
	target=target.replace('common',"YCommon")
	target=target.replace('web',"BWeb")	
	fd.write("%s,%s,%s\n"%(source,target,value))
for (source,target),value in mappingDictMidLast.items():
	source=source.replace('hack','HHacking')
	source=source.replace('tech',"TTech")
	source=source.replace('gaming',"GGaming")
	source=source.replace('coding',"CCoding")
	source=source.replace('money',"EMoney")
	source=source.replace('graphics',"XGraphics")
	source=source.replace('market',"MMarket")
	source=source.replace('common',"YCommon")
	source=source.replace('web',"BWeb")
	target=target.replace('hack','HHacking')
	target=target.replace('tech',"TTech")
	target=target.replace('gaming',"GGaming")
	target=target.replace('coding',"CCoding")
	target=target.replace('money',"EMoney")
	target=target.replace('graphics',"XGraphics")
	target=target.replace('market',"MMarket")
	target=target.replace('common',"YCommon")
	target=target.replace('web',"BWeb")	
	fd.write("%s,%s,%s\n"%(source,target,value))	
fd.close()
