#!/usr/bin/env python
'''
Based on multi_dmn.py

Written to determine if there are genes that have had multiple de novo events
across different studies.

KES. 10/08/12.
'''

import sys

all_genes = {}
multi_hits = {}
#print "hello world"
def runFile(genelist1):
	print "runningFile"
	for line in genelist1:
		line = line.strip().split()
		
		if line[0] in all_genes.keys():
			types = all_genes[line[0]]
			types.append(line[1])
			multi_hits[line[0]] = types 
		else:
			all_genes[line[0]] = [line[1]]
	print returnStuff()
	return returnStuff()

def returnStuff():
	returnString = ''
	for key, values in multi_hits.items():
		changes = '/'.join(values)
		returnString+=('\t'.join([key, changes]))
		returnString+='\n'
	return returnString
#geneList = open('exampleData.txt', 'r')
#runFile(geneList)
'''
with open(sys.argv[1], 'r') as genelist1:
    for line in genelist1:
        line = line.strip().split()

        if line[0] in all_genes.keys():
            types = all_genes[line[0]]
            types.append(line[1])
            multi_hits[line[0]] = types 
        else:
            all_genes[line[0]] = [line[1]]'''