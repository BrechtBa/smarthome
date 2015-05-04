#!/usr/bin/python3

#import pyipopt
import numpy as np
import pymysql
import datetime

con = pymysql.connect('localhost', 'knxcontrol', sh.knxcontrol.mysql.conf['password'], 'knxcontrol')
cur = con.cursor()

# get measurement data ids
signal_id = {}

# building measurements
signal_id['zone'] = []
for child in sh.knxcontrol.building:
	cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" % (child.temperature.id()))
	for data in cur:
		signal_id['zone'].append(data[0])

signal_id['fanspeed'] = []
for child in sh.knxcontrol.ventilation:
	cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" %(child.fanspeed.id()))
	for data in cur:
			signal_id['fanspeed'].append(data[0])

signal_id['heatrecovery'] = []
for child in sh.knxcontrol.ventilation:
	cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" %(child.heatrecovery.id()))
	for data in cur:
			signal_id['heatrecovery'].append(data[0])

signal_id['heat_production'] = []
for child in sh.knxcontrol.heat.production:
	cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" %(child.power.id()))
	for data in cur:
		signal_id['heat_production'].append(data[0])
	
signal_id['heat_emission'] = []
for child in sh.knxcontrol.heat.emission:
	cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" %(child.power.id()))
	for data in cur:
		signal_id['heat_emission'].append(data[0])

# weather
signal_id['ambient_temperature'] = []
child = sh.knxcontrol.weather.current.temperature
cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" %(child.id()))
for data in cur:
	signal_id['ambient_temperature'].append(data[0])

signal_id['direct'] = []
child = sh.knxcontrol.weather.current.irradiation.direct
cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" %(child.id()))
for data in cur:
	signal_id['direct'].append(data[0])

signal_id['diffuse'] = []
child = sh.knxcontrol.weather.current.irradiation.diffuse
cur.execute("SELECT id FROM  measurement_legend WHERE item='%s'" %(child.id()))
for data in cur:
	signal_id['diffuse'].append(data[0])


# define time
dt = 900
t = np.arange(0,7*24*3600,dt)
N = t.shape[0]-1

now = datetime.datetime.utcnow();
timestamp = int( (now - datetime.datetime(1970,1,1)).total_seconds() )
timestamp_start = timestamp - 3600 - t[-1]




# load required measurements

temp = np.zeros((N+1,len(signal_id['zone'])))
for idx,val in enumerate(signal_id['zone']):
	try:
		cur.execute("SELECT time,value FROM  measurement_average_quarterhour WHERE signal_id=%s AND time>%s" %(val,timestamp_start))
		data = np.asarray(list(cur))
		temp[:,idx] = np.interp(t+timestamp_start,data[:,0],data[:,1],left=data[0,1],right=data[-1,1])
	except:
		logger.warning('Not enough data in quarter hour measurements')

T_zon_meas = temp


temp = np.zeros((N+1,len(signal_id['ambient_temperature'])))
for idx,val in enumerate(signal_id['ambient_temperature']):
	try:
		cur.execute("SELECT time,value FROM  measurement_average_quarterhour WHERE signal_id=%s AND time>%s" %(val,timestamp_start))
		data = np.asarray(list(cur))
		temp[:,idx] = np.interp(t+timestamp_start,data[:,0],data[:,1],left=data[0,1],right=data[-1,1])
	except:
		logger.warning('Not enough data in quarter hour measurements')

T_amb_meas = np.mean(temp,axis=1)


temp = np.zeros((N+1,len(signal_id['fanspeed'])))
for idx,val in enumerate(signal_id['fanspeed']):
	try:
		cur.execute("SELECT time,value FROM  measurement_average_quarterhour WHERE signal_id=%s AND time>%s" %(val,timestamp_start))
		data = np.asarray(list(cur))
		temp[:,idx] = np.interp(t+timestamp_start,data[:,0],data[:,1],left=data[0,1],right=data[-1,1])
	except:
		logger.warning('Not enough data in quarter hour measurements')

fanspeed_meas = temp


temp = np.zeros((N+1,len(signal_id['direct'])))
for idx,val in enumerate(signal_id['direct']):
	try:
		cur.execute("SELECT time,value FROM  measurement_average_quarterhour WHERE signal_id=%s AND time>%s" %(val,timestamp_start))
		data = np.asarray(list(cur))
		temp[:,idx] = np.interp(t+timestamp_start,data[:,0],data[:,1],left=data[0,1],right=data[-1,1])
	except:
		logger.warning('Not enough data in quarter hour measurements')

direct_meas = np.mean(temp,axis=1)


temp = np.zeros((N+1,len(signal_id['diffuse'])))
for idx,val in enumerate(signal_id['diffuse']):
	try:
		cur.execute("SELECT time,value FROM  measurement_average_quarterhour WHERE signal_id=%s AND time>%s" %(val,timestamp_start))
		data = np.asarray(list(cur))
		temp[:,idx] = np.interp(t+timestamp_start,data[:,0],data[:,1],left=data[0,1],right=data[-1,1])
	except:
		logger.warning('Not enough data in quarter hour measurements')

diffuse_meas = np.mean(temp,axis=1)


temp = np.zeros((N+1,len(signal_id['heat_emission'])))
for idx,val in enumerate(signal_id['heat_emission']):
	try:
		cur.execute("SELECT time,value FROM  measurement_average_quarterhour WHERE signal_id=%s AND time>%s" %(val,timestamp_start))
		data = np.asarray(list(cur))
		temp[:,idx] = np.interp(t+timestamp_start,data[:,0],data[:,1],left=data[0,1],right=data[-1,1])
	except:
		logger.warning('Not enough data in quarter hour measurements')

heat_emission = temp


temp = np.zeros((N+1,len(signal_id['heat_production'])))
for idx,val in enumerate(signal_id['heat_production']):
	try:
		cur.execute("SELECT time,value FROM  measurement_average_quarterhour WHERE signal_id=%s AND time>%s" %(val,timestamp_start))
		data = np.asarray(list(cur))
		temp[:,idx] = np.interp(t+timestamp_start,data[:,0],data[:,1],left=data[0,1],right=data[-1,1])
	except:
		logger.warning('Not enough data in quarter hour measurements')

heat_production = temp






#######################################################################################
# Model 1
#######################################################################################
if sh.knxcontrol.model()==1:

	# system equations:
	# C*dT_zon/dt = UA*(T_amb-T_zon) + n_ven*fanspeed*(T_amb-T_zon) + n_irr*P_irr + n_emi*P_emi
	# P_emi = sum( n_pro(i)*P_pro(i) )
	#
	# unknown parameters:
	# C, UA, n_ven, n_irr, n_emi, n_pro(i)

	
	# edit measurements to correct format
	T_zon_meas = np.mean(T_zon_meas,axis=1)
	fanspeed_meas = np.mean(fanspeed_meas,axis=1)
	heat_emission = np.sum(heat_emission,axis=1)


	# temporary plot for debugging
	#import matplotlib.pyplot as plt
	#fig1, (ax0, ax1, ax2)  = plt.subplots(nrows=3)

	#ax0.plot(t, T_zon_meas )
	#ax1.plot(t, fanspeed_meas )
	#ax2.plot(t, heat_emission )

	#plt.show()

	# define variable indices
	a = 0
	T_zon = np.arange(a,a+N+1)
	a = a+N+1
	T_abm = np.arange(a,a+N+1)
	a = a+N+1
	fanspeed = np.arange(a,a+N+1)
	a = a+N+1
	P_irr = np.arange(a,a+N+1)
	a = a+N+1
	P_emi = np.arange(a,a+N+1)

	P_pro = np.zeros((N+1,len(signal_id['heat_production'])))
	for idx,val in enumerate(signal_id['heat_production']):
		a = a+N+1
		P_pro[:,idx] = np.arange(a,a+N+1)

	nvars = a+N

	x = np.random.rand(nvars)



	# define required functions for ipopt
	def objective(x, user_data = None):
		global T_zon,T_zon_meas
		return sum(x[T_zon]**2 - 2*x[T_zon]*T_zon_meas + T_zon_meas**2)


		
# define signals
#===============================================================================
# signal_id = {'T_amb': 1, 'T_zon': 15, 'V_flow_ven': 17, 'W_flow_tot': 9, 'W_flow_ahp': 10, 'Q_flow_gas': 11, 'Q_flow_irr': 19 }
# signal_val = {}
# 
# now = datetime.datetime.utcnow()
# 
# # connect to the mysql database
# con = pymysql.connect('localhost', 'knxcontrol','admin' , 'knxcontrol')   #sh.building.mysql.conf['password']
# cur = con.cursor(pymysql.cursors.DictCursor)
# 
# timestamp = int( (now - datetime.datetime(1970,1,1)).total_seconds() )
# timestamp_start = timestamp - 3600 - t[-1]
# 
# for signal in signal_id:
# 	# get data from the database
# 	cur.execute("SELECT time,value FROM  measurements_quarterhouraverage WHERE signal_id=%s AND time>%s" %(signal_id[signal],timestamp_start))
# 	raw_time = []
# 	raw_value = []
# 	for data in cur:
# 		raw_time.append(data['time'])
# 		raw_value.append(data['value'])
# 	
# 	raw_time  = array(raw_time)
# 	raw_value = array(raw_value)
# 	
# 	avg_value = []
# 	# resample to the wanted timevector
# 	for i,tt in enumerate(t[:-1]):
# 		# average all values where timestamp_start+t[i] < raw_time < timestamp_start+t[i+1]
# 		avg_value.append(mean(  raw_value[where( (timestamp_start+t[i] < raw_time) & (raw_time <= timestamp_start+t[i+1]) )]  ))
# 		
# 	# add the values to a dictionary
# 	signal_val[signal] = array(avg_value)
# 	
# con.close()
# 	
# # condition signals for use in the optimisation
# t = t[:-1]
# signal_val['W_flow_int'] = signal_val['W_flow_tot'] - signal_val['W_flow_ahp']
# 
# ###################################################################################################################################
# 
# # define input signals
# T_zon = signal_val['T_zon']
# T_amb = signal_val['T_amb'] 
# T_set = 21*ones(t.shape[0])
# 
# Q_flow_irr = signal_val['Q_flow_irr'] 
# V_flow_ven = signal_val['V_flow_ven'] 
# W_flow_ahp = signal_val['W_flow_ahp'] 
# Q_flow_gas = signal_val['Q_flow_gas'] 
# W_flow_int = signal_val['W_flow_int'] 
# 
# 
# 
# # define constants
# rc = 1004*1.22
# n_gas = 0.90
# 
# 
# # Variable indexing
# S = 1               # number of states        j = 0..S-1
# N = t.shape[0]      # number of timesteps     i = 0..N-1
# M = 6               # number of parameters to be estimated   k=0..M-1
# 
# nvars = N*S + M     # number of variables
# ncons = N-1         # number of constraints
# 
# # state(j,i) = x(i*S+j)
# # param(k)   = x(S*N+k)
# 
# state_measurement = transpose(array([T_zon]));
# state_index       = array([0]);
# 
# 
# def combineintoarray(states,C,UA,n_ven,n_int,n_irr,n_ahp):
# 	x = concatenate((states.reshape((N*S)),array([C,UA,n_ven,n_int,n_irr,n_ahp])))
# 	return x
# 	
# def splitintovalues(x):
# 
# 	states = zeros((N,S))
# 	for j in arange(S):
# 		states[:,j] = x[j + arange(N)*S]
# 	
# 	C  = x[N*S + 0]
# 	UA = x[N*S + 1]
# 	n_ven = x[N*S + 2]
# 	n_int = x[N*S + 3]
# 	n_irr = x[N*S + 4]
# 	n_ahp = x[N*S + 5]
# 	
# 	return states,C,UA,n_ven,n_int,n_irr,n_ahp
# 
# 	
# # define weights for the objective function
# weights = ones((N,state_measurement.shape[0]))
# weights[0,:] = 10    # add larger weights to the initial timestep as it is assumed to be known
# 	
# 
# # define required function for ipopt
# def objective(x, user_data = None):
#     
# 	states,C,UA,n_ven,n_int,n_irr,n_ahp = splitintovalues(x)
# 	
# 	Res = zeros((N,state_measurement.shape[0]))
# 	for ind, j in enumerate(state_index):
# 		Res[:,ind] = power(states[:,j] - state_measurement[:,ind],2)
# 	
# 	return sum(Res*weights)
# 	
# def gradient(x, user_data = None):
# 
# 	states,C,UA,n_ven,n_int,n_irr,n_ahp = splitintovalues(x)
# 	T = states[:,0]
# 	
# 	Gra = zeros((nvars))
# 	for j in state_index:
# 		for i in arange(N):
# 			Gra[i*S+j] = (2*T[i]-2*T_zon[i])*weights[i,j]
# 
# 	
# 	return Gra
# 	
# def constraint(x, user_data = None):
# 
# 	states,C,UA,n_ven,n_int,n_irr,n_ahp = splitintovalues(x)
# 	T = states[:,0]
# 	
# 	Con = zeros((ncons))
# 
# 	for i in arange(N-1):
# 		Con[i] = -C*(T[i+1]-T[i])/dt  + UA*(T_amb[i]-T[i]) + n_ven*rc*V_flow_ven[i]/3600*(T_amb[i]-T_set[i]) + n_int*W_flow_int[i] + n_irr*Q_flow_irr[i] + n_ahp*W_flow_ahp[i] + n_gas*Q_flow_gas[i]
# 
# 	return Con
# 	
# nnzj = ncons*8
# def jacobian(x, flag, user_data = None):
# 	
# 
# 	states,C,UA,n_ven,n_int,n_irr,n_ahp = splitintovalues(x)
# 	T = states[:,0]
# 	
# 	row = []
# 	col = []	
# 	Jac = []	
# 	for i in arange(N-1):
# 		row.append(i)
# 		col.append(i)
# 		Jac.append(C/dt - UA)
# 		
# 		row.append(i)
# 		col.append(i+1)
# 		Jac.append(-C/dt)
# 		
# 		row.append(i)
# 		col.append(N*S+0)
# 		Jac.append(-(T[i+1]-T[i])/dt)
# 		
# 		row.append(i)
# 		col.append(N*S+1)
# 		Jac.append(T_amb[i]-T[i])
# 		
# 		row.append(i)
# 		col.append(N*S+2)
# 		Jac.append(rc*V_flow_ven[i]/3600*(T_amb[i]-T_set[i]))
# 		
# 		row.append(i)
# 		col.append(N*S+3)
# 		Jac.append(W_flow_int[i])
# 		
# 		row.append(i)
# 		col.append(N*S+4)
# 		Jac.append(Q_flow_irr[i])
# 		
# 		row.append(i)
# 		col.append(N*S+5)
# 		Jac.append(W_flow_ahp[i])
# 	
# 	if flag:
# 		return (array(row),array(col))
# 	else:
# 		return array(Jac)
# 	
# nnzh = 0	
# 	
# # variable bounds
# x_L = combineintoarray(array([ones((N))*15]),1e6  ,10  ,0,0,0,0)
# x_U = combineintoarray(array([ones((N))*30]),200e6,1000,1,1,2,5)	
# x0 = (x_L+x_U)/2
# 
# # constraint bounds
# c_L = zeros((ncons))
# c_U = zeros((ncons))
# 
# 
# # prepare ipopt
# nlp = pyipopt.create(nvars, x_L, x_U, ncons, c_L, c_U, nnzj, nnzh, objective, gradient, constraint, jacobian)
# 
# 
# x, zl, zu, constraint_multipliers, obj, status = nlp.solve(x0)
# print()
# print( 'solution: ' + str(x) )
# print()
# print()
# print()
# 
# states,C,UA,n_ven,n_int,n_irr,n_ahp = splitintovalues(x)
# T = states[:,0]
# res = T-T_zon
# print(res)
#===============================================================================
		
#logger.warning('Einde model parameter identificatie')
#sh.building.model.identify(False)
