#!/usr/bin/env python
# encoding: utf-8

import sys
import MySQLdb
import clouddns
import time

# Rackspace
rackspace_api_user = 'xxxxxx'
rackspace_api_key = 'xxxxxxxxxxxxxxxx'
rackspace_api_url = 'https://lon.identity.api.rackspacecloud.com/v1.0/' # UK url

# domain comment
domain_comment = 'Domain comment'
domain_admin_email = 'admin@example.com'

# PowerDNS MySQL

powerdns_mysql_host = 'xxxxxxxxxxxx'
powerdns_mysql_user = 'xxxxxxxxx'
powerdns_mysql_password = 'xxxxxxxxx'
powerdns_mysql_db = 'xxxxxxxxxxxx'

# Connext Rackspace API
dns = clouddns.connection.Connection(rackspace_api_user,rackspace_api_key,authurl=rackspace_api_url)

# records
data = []

# domains
domains = []

try:
	conn = MySQLdb.connect (host = powerdns_mysql_host,
							user = powerdns_mysql_user,
							passwd = powerdns_mysql_password,
							db = powerdns_mysql_db)
except MySQLdb.Error, e:
	print "Error %d: %s" % (e.args[0], e.args[1])
	sys.exit (1)

try:
	cursor = conn.cursor ()
	cursor.execute("SELECT * FROM  `domains` ORDER BY name") 
	rows = cursor.fetchall ()
	
	for row in rows:
		 domains.append(row[0])
	cursor.close ()

except MySQLdb.Error, e:
	print "Error %d: %s" % (e.args[0], e.args[1])
	sys.exit (1)

for domain in domains:
	try:
		cursor = conn.cursor ()
		cursor.execute("SELECT * FROM  `records` LEFT JOIN domains ON domains.id = records.domain_id WHERE records.domain_id = %s ORDER BY records.type DESC ", domain) 
		rows = cursor.fetchall ()
		for row in rows:
			domain_id = row[1]
			domain_record = row[2]
			record_type = row[3]
			record_content = row[4]
			domain_name = row[9]

			print domain_name + " " + domain_record + " " + record_type

			#if not domain_name in ddict:
			if record_type == 'SOA':
					print "SOA " + domain_record
					dns.create_domain(name=domain_record, ttl=300, emailAddress=domain_admin_email, comment=domain_comment)
			else:
				if record_type == 'MX':
					domain = dns.get_domain(name=str(domain_name))
					domain.create_record(domain_record, record_content, record_type, ttl=None, priority='10', comment='')

					time.sleep(1)
				elif record_type == 'NS':
					domain = dns.get_domain(name=str(domain_name))
					
					# rackspace NS1 delete
					record_ns1 = domain.get_record(type='NS',data='dns1.stabletransit.com')
					domain.delete_record(record_ns1.id)

					# rackspace NS2 delete
					record_ns2 = domain.get_record(type='NS',data='dns2.stabletransit.com')
					domain.delete_record(record_ns2.id)

					domain = dns.get_domain(name=str(domain_name))
					domain.create_record(domain_record, record_content, record_type, ttl=None, priority=None, comment='')

					time.sleep(1)
				else:	
					domain = dns.get_domain(name=str(domain_name))
					domain.create_record(domain_record, record_content, record_type, ttl=None, priority=None, comment='')

					time.sleep(1)
			time.sleep(1)

		cursor.close ()
	except MySQLdb.Error, e:
		print "Error %d: %s" % (e.args[0], e.args[1])
		sys.exit (1)

conn.commit ()
conn.close ()