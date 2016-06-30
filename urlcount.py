# Quick and dirty URL allow/block list entry list counter for multi vsys
# Feed in a config and get a count of allow-list and block-list entries in each URL filtering profile in each vsys


from lxml import etree
import pdb

f = open('merged-running-config.xml')
root=etree.fromstring(f.read())

#pdb.set_trace()
all_vsys = root.findall('.//vsys/entry[@name]')  # list of all vsys xml objs
shared = root.xpath('shared')

all_vsys.extend(shared)

for single_vsys in all_vsys:
	print '\n******************\n'
	if len(single_vsys.attrib) == 0:
		print "{'CONTEXT': 'SHARED'}" 
	else: 
		print single_vsys.attrib
	#print single_vsys.attrib
	#url_profs_in_vsys = single_vsys.findall('.//profiles/url-filtering')[0].getchildren() #all url filtering profiles in vsys
	#url_profs_in_vsys = single_vsys.find('.//profiles/url-filtering').getchildren() #all url filtering profiles in vsys
	url_profs_in_vsys = single_vsys.xpath('profiles/url-filtering')[0].getchildren() #all url filtering profiles in vsys
	vsys_allow = 0
	vsys_block = 0
	for single_url in url_profs_in_vsys:
		print single_url.attrib

		try:
			allow_list = single_url.find('.//allow-list')
			vsys_allow += len(allow_list.getchildren())
			print 'allow list length: {0}'.format(len(allow_list.getchildren()))
		except AttributeError:
			print 'Allow list empty'

		try:
			block_list = single_url.find('.//block-list')
			vsys_block += len(block_list.getchildren())
			print 'block list length: {0}\n'.format(len(block_list.getchildren()))
		except AttributeError:
			print 'Block list empty\n'

	print 'PER VSYS ALLOW LIST FOR THIS VSYS: {0}'.format(vsys_allow)
	print 'PER VSYS BLOCK LIST FOR THIS VSYS: {0}\n'.format(vsys_block)

