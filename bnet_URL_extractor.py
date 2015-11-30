#!/usr/bin/env python
"""Script to take a botnet pdf file as input and extract all the URLs from the botnet report for 'repeatedly visited' or 'visited malware' lines
   Format: $ script <pdf file> """
__author__ = "Ashutosh Chitwadgi"
__version__ = 1.0


import re, subprocess, pdb, sys


def extract_URL(newline):
	matchobj=re.search(r"URL\s(.*)",newline)
	if matchobj:
		#print matchobj.group(1)
		return matchobj.group(1)
	#else:
	#	return None

def parse_PDF(pdfFile):
	x=subprocess.Popen('/usr/bin/pdf2txt.py {0}'.format(pdfFile), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	op,err=x.communicate()
	#pdb.set_trace()
	lines=op.split('\n')
	URLArray=[]
	for line in lines:
		if line.startswith('Repeatedly visited') or line.startswith('Visited malware'):
			URLArray.append(line)

	return URLArray

def main():
	
	if len(sys.argv) != 2:
		print "Input pdf file needed.\nUsage: $ python {0} <pdf file>".format(sys.argv[0])
		sys.exit(1)

	data = open('urls.txt').read()
	lines=data.split('\n')
	#for line in lines:
	#	print extract_URL(line)
	URLArray=parse_PDF(str(sys.argv[1]))
	#pdb.set_trace()
	if len(URLArray) > 0:
		finalArray=[extract_URL(line) for line in URLArray]

	print finalArray, "\n\n ********** UNIQUE SET ******** \n\n"
	uniqArray=set(finalArray)
	for line in uniqArray:
		print line
			


if __name__=="__main__":
	main()

