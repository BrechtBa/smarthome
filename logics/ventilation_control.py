###########################################################################
# control ventilation
###########################################################################
#
# execute every 30 mins
#

# shut down between 22h and 8h, unless the a zone indoor temperature is above T_set+4
# and the outside temperature is below T_set 
# ventilate every day between 11h and 15h at high speed
# when the average outdoor temperature is below 10degC only turn on from 11h to 15h at high speed
# when a user sets the speed maintain this for 1h, then return to normal operation

import pymysql

now = datetime.datetime.utcnow()
localtime = datetime.datetime.now()

# base setting	
ventilation_speed = 1

# connect to the mysql database
con = pymysql.connect('localhost', 'knxcontrol', sh.building.mysql.conf['password'], 'knxcontrol')
cur = con.cursor()

# average temperature too low
# calculate the average ambient temperature
try:	
	signal_id = 1
	timestamp = int( (now - datetime.datetime(1970,1,1)).total_seconds() )

	# get 2 day average from mysql
	timestamp_new = timestamp-2*24*60*60
	cur.execute("SELECT AVG(value) FROM measurements WHERE signal_id=%s  time>%s" %(signal_id,timestamp_new))
	for temp in cur:
		ambient_temperature_avg = temp[0]
except:
	logger.warning('average calculation failed')
	ambient_temperature_avg = 12
	
if ambient_temperature_avg < 10:
	logger.warning('average ambient temperature below 10 degC');
	ventilation_speed = 0

# ventilate in the middle of the day not on monday and tuesday	
if localtime.weekday()>=3 and localtime.hour >= 11 and localtime.hour < 13:
	ventilation_speed = 3

# shut down at night or try to cool the building at night
if localtime.hour >= 22 or localtime.hour < 7:
	ventilation_speed = 0
	for zone in sh.building.zones:
		if zone.T_operational() > zone.T_set()+4 and sh.building.ambient_temperature() < zone.T_set():
			ventilation_speed = 2

# set to high when showering		
if trigger['by'] == 'Item':
	if trigger['value']:
		ventilation_speed = 3;
		logger.warning('ventilation high active');

	
# find the ventilation speed item and set it
for item in sh.match_items('*.ventilation.speed'):

	# rescale based on min and max properties and write it to the item
	value = float(item.conf['min']) + ventilation_speed/3*(float(item.conf['max'])-float(item.conf['min']))
	item( value )
	
# set the flowrate item
flowrate = float(item.conf['flowrate_min']) + ventilation_speed/3*(float(item.conf['flowrate_max'])-float(item.conf['flowrate_min']))
sh.building.ventilation.flowrate(flowrate)