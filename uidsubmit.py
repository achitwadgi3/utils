#!/usr/bin/python
"""
Author: Ashutosh Chitwadgi
#Date: 03/15/2015
#Description:Utility to submit batches of unique user-IP mappings periodically to userID Agent using XML API(max 64k mappings in one standalone execution)

version 1.0 initial commit
version 1.1 Fixed issue with generating mappings in same 3rd octet
version 1.2 Added check for 'ok' response from UID agent and break of if ok status not received
"""
# shortshelp: uidsubmit -h                    Generates and submits batches of unique user-IP mappings to userID Agent

import time, argparse
import sys
import pdb
import httplib
import socket
import logging


def makeParser():
	desc="""Utility to submit batches of unique user-IP mappings periodically to userID Agent (max 64k mappings in one standalone execution). The IP mappings needed are input as a range with a start IP & end IP.
The first two octets of the start and end IP have to be the same with flexibility in the 3rd and 4th octet(thus the maximum of 64k unique IP mappings possible by running one instance of the program)
The username is autogenerated based on the IP address. eg. for the IP 192.168.5.6 the username generated is user192-168-5-6\n
Here is a sample invoke of the tool to generate mappings from 192.168.10.1 to 192.168.12.20 and submit them in batches of 200 to agent 10.46.48.100 on port 25555:
$ ./uidsubmit -i 10.46.48.100 -p 25555 -b 200 -s 192.168.10.1 -e 192.168.12.20 -d domain \n"""
	"""Utility to submit batches of unique user-IP mappings periodically to userID Agent using XML API(max 64k mappings in one standalone execution)"""
	parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument("-i", "--IP", help="IP of UID Agent machine", required=True)
	parser.add_argument("-p", "--PORT", help="XML-API Port number on the agent", required=True)
	parser.add_argument("-b", "--BATCH", help="number of entries to submit in each batch", type=int, required=True)
	parser.add_argument("-s", "--START", help="starting IP for mapping range. e.g. 192.168.10.11", required=True)
	parser.add_argument("-e", "--END", help="ending IP for mapping range. e.g. 192.168.20.250", required=True)
	parser.add_argument("-d", "--DOMAIN", help="Domain prefix, default = domain", default='domain')
	parser.add_argument("-w", "--WAIT", help="Wait(secs) between running iterations of the batch submit to agent, default=5 sec",default=5, type=int)
	return parser



def submitPayload(toSubmit):
	"""Function takes a batch of userip mappings, generates full UID message and POSTs to the agent:port  """
	payfrnt = "<uid-message><version>1.0</version><type>update</type><payload><login>"
	payback = "</login><logout></logout></payload></uid-message>"
	fullData = '<uid-message><version>1.0</version><type>update</type><payload><login>{0}</login><logout></logout></payload></uid-message>'.format(toSubmit)
	connObject = httplib.HTTPSConnection(args.IP, args.PORT, timeout=10)
	#connObject.request("POST", fullData)
	try:
		connObject.request("POST", fullData)
		sockResponse= connObject.sock.read() # Read status response from UIDAgent after POST
		if sockResponse.find('ok') > 0:
			logging.info("Received 'ok' response from UIDAgent: {0}".format(sockResponse))  #<uid-response><version>1.0</version><code>0</code><message>ok</message></uid-response>
		else:
			logging.error("Did not receive 'ok' response from Agent, check & ensure that the connection is made on the 'XML API' Port")
			logging.info("Exiting")
			sys.exit(1) 
	except socket.timeout as e:
		logging.error(sys.exc_info()[1])
	 	logging.critical('Connection attempt to server timed out, please check connectivity')
	 	sys.exit(1)
	
	except socket.error:
		logging.error(sys.exc_info()[1])
		logging.critical('Received refusal from server, please check server port')
		sys.exit(1)
	
	return

def generateUsernamePrefix(domain,firstAndSecondOctet):
	"""Function takes in a domain name and the common first,second octet string and returns a username prefix to be added to each mapping  """
	#dom="domain\\"
	dom = '{0}\\'.format(domain)
	firstAndSecondOctetText='{0}-{1}-'.format(firstAndSecondOctet[0],firstAndSecondOctet[1])
	userNamePrefix = '{0}user{1}'.format(dom, firstAndSecondOctetText)	
	return userNamePrefix

def generateBulkPayload(currentPayload, firstAndSecondOctet, thirdOctetRange,):
	"""Function takes in the common first,second octet and range for 3rd octet and generates mappings for the 3rd octet range which needs full .1 - .255 mappings   """
	userNamePrefix = generateUsernamePrefix(args.DOMAIN, firstAndSecondOctet)
	
	fullPayload=currentPayload

	for third in range(thirdOctetRange[0],thirdOctetRange[1]+1):
		
		for fourth in range(1,255):
			currentEntry = '<entry name="{0}{1}-{2}" ip="{3}.{4}.{5}.{6}">'.format(userNamePrefix,third,fourth, firstAndSecondOctet[0], firstAndSecondOctet[1], third, fourth)
			
			#print currentEntry
			fullPayload = fullPayload + currentEntry
			
	return fullPayload


def generateTopBottomPayload(currentPayload, firstAndSecondOctet, thirdOctet, fourthOctetRange):
	"""Function takes in common first,second,third octet and then generates the mapping section needed for fourth octet where the fourth octet is a section such as .1 - .150   """
	userNamePrefix = generateUsernamePrefix(args.DOMAIN, firstAndSecondOctet)

	fullPayload = currentPayload
	for fourth in range(int(fourthOctetRange[0]), int(fourthOctetRange[1])+1):
		currentEntry = '<entry name="{0}{1}-{2}" ip="{3}.{4}.{5}.{6}">'.format(userNamePrefix,thirdOctet,fourth, firstAndSecondOctet[0], firstAndSecondOctet[1], thirdOctet, fourth)
		
		fullPayload = fullPayload + currentEntry

	return fullPayload






def main():
	logging.basicConfig(level=logging.DEBUG, filemode ='w', format = "[%(asctime)s %(levelname)s] %(message)s") 
	parser=makeParser()  
	global args
	args=parser.parse_args() # Get command line arguments
		
	x=args.START
	y=args.END
	xOctets = x.split('.')
	yOctets = y.split('.')

	currentPayload =''
	if (int(yOctets[0])-int(xOctets[0])==0 and int(yOctets[1])-int(xOctets[1])==0) and (int(xOctets[2]) <= int(yOctets[2])):
		logging.info('First two octets match and 3rd octet of input1 is less than or equal to 3rd octet of input2')
	
		if int(yOctets[2])-int(xOctets[2]) == 0:    #3rd octet is also same
			logging.info('Third octet is also the same')
			finalPayload = generateTopBottomPayload(currentPayload, (xOctets[0], xOctets[1]), xOctets[2], (xOctets[3], yOctets[3])  )
			#print finalPayload

		elif int(yOctets[2])-int(xOctets[2]) == 1:  #3rd octet differ by 1
			logging.info('Third octet differs by 1')
			finalPayload1 = generateTopBottomPayload(currentPayload,(xOctets[0], xOctets[1]), xOctets[2], (xOctets[3], '254'))
			finalPayload = generateTopBottomPayload(finalPayload1, (yOctets[0], yOctets[1]), yOctets[2], (1, yOctets[3]) )
			#print finalPayload

		elif int(yOctets[2])-int(xOctets[2]) >= 2:  # 3rd Octet differs by 2
			logging.info('Third octet differs by greater than or equal to 2')
			finalPayload1 = generateTopBottomPayload(currentPayload,(xOctets[0], xOctets[1]), xOctets[2], (xOctets[3], '254'))
			finalPayload2 = generateBulkPayload(finalPayload1, (xOctets[0], xOctets[1]), (int(xOctets[2])+1, int(yOctets[2])-1) )
			finalPayload = generateTopBottomPayload(finalPayload2, (yOctets[0], yOctets[1]), yOctets[2], (1, yOctets[3]) )
			#print finalPayload
			logging.info('Done generating FINAL PAYLOAD')


	else:
		logging.error('Bad IP input range specified: Either first two octets of the inputs are not equal or 3rd octet of input1 is not less than 3rd octet of input2')
		sys.exit(1)

	lim="/>"
	splitPayloadList = [entry+lim for entry in finalPayload.split('>')] #Take the full generated XML payload and convert to list containing each IP-user entry
	
	splitPayloadList.pop()  #Drop last '\n'
	logging.info('Done making list of Entries')
	logging.info("Total number of mappings: {0}".format(len(splitPayloadList)))
	
	toSubmit =''
	count =1
	#logic to submit mappings in configured batch size
	for i in splitPayloadList:
		toSubmit = toSubmit+i
		if count % int(args.BATCH) == 0: 
			submitPayload(toSubmit)
			toSubmit=''
			logging.info('SUBMITTED BATCH')
			time.sleep(int(args.WAIT))
		count = count+1
		
	#print toSubmit
	# There are some remainder IP-user mappings that were smaller than the configured batch size that need one final POST
	submitPayload(toSubmit) #Submit last batch of mappings which were not divisible by mod operator and pending
	logging.info("SUBMITTED LAST BATCH of mappings smaller than the configured batch size")

if __name__ == "__main__": main()
