#!/usr/bin/python3

from __init__ import *
from pprint import pprint
from datetime import datetime

NUMBER_OF_RN = 6
NUMBER_OF_UE = 240
ITER_TIMES=10
SIMULATION_TIME=10000

def update_nested_dict(d1, d2):
	for k,v in d2.items():
		if type(v) is list:
			d1[k].extend(v)
		elif type(v) is dict:
			d1[k] and update_nested_dict(d1[k], v)
			not d1[k] and d1.update({k:v})

def transmission_scheduling(base_station, timeline):
	prefix = "transmissing_scheduling failed"

	try:
		simulation_time = len(timeline)-1
		round_para = len(str(int(simulation_time/10)))

		PERFORMANCE = {
			'RN-PSE':{
				'TD-aggr':[],'TD-split':[],'TD-merge':[],\
				'BU-aggr':[],'BU-split':[],'BU-merge':[]},
			'UE-PSE':{
				'TD-aggr':[],'TD-split':[],'TD-merge':[],\
				'BU-aggr':[],'BU-split':[],'BU-merge':[]},
			'DELAY':{
				'TD-aggr':[],'TD-split':[],'TD-merge':[],\
				'BU-aggr':[],'BU-split':[],'BU-merge':[]},
			'PSE-FAIRNESS':{
				'TD-aggr':[],'TD-split':[],'TD-merge':[],\
				'BU-aggr':[],'BU-split':[],'BU-merge':[]},
			'DELAY-FAIRNESS':{
				'TD-aggr':[],'TD-split':[],'TD-merge':[],\
				'BU-aggr':[],'BU-split':[],'BU-merge':[]}
		}

		# apply LBPS
		scheduling = {
			'TD-aggr': LBPS.top_down,
			'TD-split': LBPS.top_down,
			'TD-merge': LBPS.top_down,
			'BU-aggr': LBPS.bottom_up,
			'BU-split': LBPS.bottom_up,
			'BU-merge': LBPS.bottom_up
		}

		for (PS, lbps) in scheduling.items():

			msg_success("==========\t\t%s simulation with lambda %g Mbps start\t\t=========="%\
					(PS, base_station.lambd['backhaul']))
			lbps = lbps(PS[3:], base_station, simulation_time)

			base_station.clearQueue()
			status = {
				ue.name:{
					'sleep':0,
					'awake':0,
					'delay':0,
					'stuck':False,
					'force-awake':0
				} for rn in base_station.childs for ue in rn.childs}
			status.update({
				rn.name:{
					'sleep':0,
					'awake':{'backhaul':0, 'access':0},
					'transmission':{'backhaul':0, 'access':0},
					'stuck':{'backhaul':False, 'access':False},
					'force-awake':{'backhaul':0, 'access':0}
				} for rn in base_station.childs})

			for TTI in range(simulation_time):
				available_cap = base_station.capacity

				# check the arrival pkt from internet
				if timeline[TTI]:
					for arrPkt in timeline[TTI]:
						base_station.queue['backhaul'][arrPkt['device'].parent.name].append(arrPkt)

				for rn in base_station.childs:

					# case: subframe 'S' or 'U'
					if rn.tdd_config[TTI%10] != 'D':
						status[rn.name]['sleep'] += 1
						for ue in rn.childs:
							status[ue.name]['sleep'] += 1
						continue

					# backhaul transmission
					if base_station.tdd_config[TTI%10] and\
					base_station.queue['backhaul'][rn.name] and\
					(rn in lbps['backhaul'][TTI] or status[rn.name]['stuck']['backhaul']):
						interface = 'backhaul'
						status[rn.name]['awake'][interface] += 1
						status[rn.name]['transmission'][interface] += 1
						pass_pkt = []

						for i, pkt in enumerate(base_station.queue[interface][rn.name]):
							if available_cap < pkt['size']: break
							rn.queue[interface].append(pkt)
							pass_pkt.append(pkt)

						for pkt in pass_pkt:
							base_station.queue[interface][rn.name].remove(pkt)

						if base_station.queue[interface][rn.name]:
							status[rn.name]['stuck'][interface] = True
							status[rn.name]['force-awake'][interface] += 1

						for ue in rn.childs:
							status[ue.name]['sleep'] += 1

					# access transmission
					elif rn.queue['backhaul'] and\
					(rn in lbps['access'][TTI] or status[rn.name]['stuck']['access']):
						interface = 'access'
						status[rn.name]['awake'][interface] += 1
						available_cap = rn.capacity[interface]
						pass_pkt = []
						rcv_ue = []

						status[rn.name]['transmission'][interface] += 1

						for i, pkt in enumerate(rn.queue['backhaul']):
							ue = pkt['device']
							if available_cap < pkt['size']: break
							if ue in lbps[interface][TTI] or\
							status[ue.name]['force-awake']:
								rn.queue[interface][ue.name].append(pkt)
								status[ue.name]['delay'] += TTI-pkt['arrival_time']
								rcv_ue.append(ue)
								pass_pkt.append(pkt)
								available_cap -= pkt['size']

						for pkt in pass_pkt:
							rn.queue['backhaul'].remove(pkt)

						for ue in rn.childs:
							item = 'awake' if ue in rcv_ue else 'sleep'
							status[ue.name][item] += 1

						force_awake_ue = [pkt['device'] for pkt in rn.queue['backhaul']]

						for ue in rn.childs:
							if ue in force_awake_ue:
								status[ue.name]['stuck'] = True
								status[ue.name]['force-awake'] += 1
							else:
								status[ue.name]['stuck'] = False

						status[rn.name]['stuck'][interface] =\
						True if any([status[ue.name]['stuck'] for ue in rn.childs]) else False
						status[rn.name]['force-awake'][interface] += \
						1 if status[rn.name]['stuck'][interface] else 0

					# sleep
					else:
						status[rn.name]['sleep'] += 1
						for ue in rn.childs:
							status[ue.name]['sleep'] += 1

			# Device all awake for collecting pkt
			TTI = copy.deepcopy(simulation_time)
			while any([len(q_rn) for q_rn in base_station.queue['backhaul'].values()])\
			or any([len(rn.queue['backhaul']) for rn in base_station.childs]):
				available_cap = base_station.capacity
				for rn in base_station.childs:

					# case: subframe 'S' or 'U'
					if rn.tdd_config[TTI%10] != 'D':
						continue

					# backhaul transmission
					if base_station.tdd_config[TTI%10] and\
					base_station.queue['backhaul'][rn.name]:
						interface = 'backhaul'
						pass_pkt = []

						for i, pkt in enumerate(base_station.queue[interface][rn.name]):
							if available_cap < pkt['size']: break
							rn.queue[interface].append(pkt)
							pass_pkt.append(pkt)

						for pkt in pass_pkt:
							base_station.queue[interface][rn.name].remove(pkt)

					# access transmission
					elif rn.queue['backhaul']:
						interface = 'access'
						available_cap = rn.capacity[interface]
						pass_pkt = []
						for i, pkt in enumerate(rn.queue['backhaul']):
							ue = pkt['device']
							if available_cap < pkt['size']: break
							rn.queue[interface][ue.name].append(pkt)
							status[ue.name]['delay'] += TTI-pkt['arrival_time']
							pass_pkt.append(pkt)
							available_cap -= pkt['size']

						for pkt in pass_pkt:
							rn.queue['backhaul'].remove(pkt)

				TTI += 1

			# test
			print(base_station.name, end='\t')
			msg_execute("CQI= %d" % base_station.CQI)
			for i in base_station.childs:
				print(i.name, end='\t')
				msg_execute("CQI= %d" % i.CQI, end='\t\t')
				msg_execute("sleep: %d times" % status[i.name]['sleep'], end='\t')
				msg_warning("transmission in backhaul: %d times" % status[i.name]['transmission']['backhaul'], end='\t')
				msg_warning("transmission in access: %d times" % status[i.name]['transmission']['access'])
				# msg_warning("force awake in backhaul: %d times" % status[i.name]['force-awake']['backhaul'], end='\t')
				# msg_warning("force awake in access: %d times" % status[i.name]['force-awake']['access'])

			# performance
			rn_pse = [status[rn.name]['sleep']/simulation_time\
			for rn in base_station.childs]
			ue_pse = [status[ue.name]['sleep']/simulation_time\
			for rn in base_station.childs for ue in rn.childs]
			ue_delay = [status[ue.name]['delay']\
			for rn in base_station.childs for ue in rn.childs]
			deliver_pkt = [len(rn.queue['access'][ue.name])\
			for rn in base_station.childs for ue in rn.childs]

			PERFORMANCE['RN-PSE'][PS].append(round(sum(rn_pse)/NUMBER_OF_RN ,round_para))
			PERFORMANCE['UE-PSE'][PS].append(round(sum(ue_pse)/NUMBER_OF_UE, round_para))
			if sum(deliver_pkt):
				PERFORMANCE['DELAY'][PS].append(round(sum(ue_delay)/sum(deliver_pkt), round_para))
			else:
				PERFORMANCE['DELAY'][PS].append(0)
			if sum(ue_pse):
				PERFORMANCE['PSE-FAIRNESS'][PS].append(round(\
					sum(ue_pse)**2/(NUMBER_OF_UE*sum([i**2 for i in ue_pse])),\
					round_para))
			else:
				PERFORMANCE['PSE-FAIRNESS'][PS].append(1)
			if sum(ue_delay):
				PERFORMANCE['DELAY-FAIRNESS'][PS].append(round(\
					sum(ue_delay)**2/(NUMBER_OF_UE*sum([i**2 for i in ue_delay])),\
					round_para))
			else:
				PERFORMANCE['DELAY-FAIRNESS'][PS].append(1)

			msg_success("==========\t\t%s simulation with lambda %g Mbps end\t\t=========="%\
					(PS, base_station.lambd['backhaul']))

		return PERFORMANCE

	except Exception as e:
		msg_fail(str(e), pre=prefix)

def DRX(base_station,\
	timeline,\
	inactivity_timer=10,\
	short_cycle_count=1,\
	short_cycle=80,\
	long_cycle=320,\
	return_name='DRX'
	):
	def reset(device, status):
		status[device.name]['inactivity_time'] = inactivity_timer
		status[device.name]['short_cycle_count'] = short_cycle_count
		status[device.name]['short_cycle'] = short_cycle
		status[device.name]['long_cycle'] = long_cycle
		status[device.name]['off'] = False

	def drx_check(device, status):
		# awake, no data, count inactivity time
		if status[device.name]['inactivity_time'] and\
		not status[device.name]['off']:
			status[device.name]['inactivity_time'] -= 1
		# sleep
		else:
			# short cycle
			if status[device.name]['short_cycle_count']:
				status[device.name]['off'] = True
				if status[device.name]['short_cycle']:
					status[device.name]['short_cycle'] -= 1
					status[device.name]['sleep'] += 1
				else:
					status[device.name]['off'] = False
					status[device.name]['short_cycle_count'] -= 1
					status[device.name]['short_cycle'] = short_cycle
			# long cycle
			elif status[device.name]['long_cycle']:
				status[device.name]['off'] = True
				status[device.name]['long_cycle'] -= 1
				status[device.name]['sleep'] += 1
			else:
				status[device.name]['off'] = False
				status[device.name]['long_cycle'] = long_cycle

	base_station.clearQueue()
	simulation_time = len(timeline)-1
	round_para = len(str(int(simulation_time/10)))
	PERFORMANCE = {
			'RN-PSE':{return_name:[]},
			'UE-PSE':{return_name:[]},
			'DELAY':{return_name:[]},
			'PSE-FAIRNESS':{return_name:[]},
			'DELAY-FAIRNESS':{return_name:[]}
		}
	status = {
		rn.name:{
			'inactivity_time':inactivity_timer,
			'sleep':0,
			'off':False,
			'short_cycle_count': short_cycle_count,
			'short_cycle':short_cycle*short_cycle_count,
			'long_cycle':long_cycle}
		for rn in base_station.childs}
	status.update({
		ue.name:{
			'inactivity_time':inactivity_timer,
			'sleep':0,
			'off':False,
			'delay':0,
			'short_cycle_count': short_cycle_count,
			'short_cycle':short_cycle,
			'long_cycle':long_cycle}
		for rn in base_station.childs for ue in rn.childs})

	msg_success("==========\t\t%s simulation with lambda %g Mbps start\t\t=========="%\
					(return_name, base_station.lambd['backhaul']))

	for TTI in range(simulation_time):

		# check the arrival pkt from internet
		if timeline[TTI]:
			for arrPkt in timeline[TTI]:
				base_station.queue['backhaul'][arrPkt['device'].parent.name].append(arrPkt)

		for rn in base_station.childs:

			if rn.tdd_config[TTI%10] != 'D' or\
			status[rn.name]['off']:
				drx_check(rn, status)
				for ue in rn.childs:
					drx_check(ue, status)
				continue

			# check backhaul
			if base_station.tdd_config[TTI%10] == 'D' and\
			base_station.queue['backhaul'][rn.name]:
				reset(rn, status)
				available_cap = rn.capacity['backhaul']
				pass_pkt = []

				for pkt in base_station.queue['backhaul'][rn.name]:
					if available_cap >= pkt['size']:
						rn.queue['backhaul'].append(pkt)
						pass_pkt.append(pkt)
						available_cap -= pkt['size']
					else:
						break

				for pkt in pass_pkt:
					base_station.queue['backhaul'][rn.name].remove(pkt)

			# check access
			elif rn.queue['backhaul']:
				available_cap = rn.capacity['access']
				pass_pkt = []
				rcv_ue = []
				for pkt in rn.queue['backhaul']:
					if available_cap >= pkt['size']:
						if not status[pkt['device'].name]['off']:
							rn.queue['access'][pkt['device'].name].append(pkt)
							status[pkt['device'].name]['delay'] += TTI-pkt['arrival_time']
							available_cap -= pkt['size']

							rcv_ue.append(pkt['device'])
							pass_pkt.append(pkt)
					else:
						break

				for pkt in pass_pkt:
					rn.queue['backhaul'].remove(pkt)

				for ue in rn.childs:
					ue not in rcv_ue and drx_check(ue, status)
					ue in rcv_ue and reset(ue, status)

			else:
				drx_check(rn, status)
				for ue in rn.childs:
					drx_check(ue, status)

	# test
	print(base_station.name, end='\t')
	msg_execute("CQI= %d" % base_station.CQI)
	for i in base_station.childs:
		print(i.name, end='\t')
		msg_execute("CQI= %d" % i.CQI, end='\t\t')
		msg_execute("total ue sleep: %d times" %\
			sum([status[ue.name]['sleep'] for ue in i.childs]))

	# performance
	rn_pse = [status[rn.name]['sleep']/simulation_time\
	for rn in base_station.childs]
	ue_pse = [status[ue.name]['sleep']/simulation_time\
	for rn in base_station.childs for ue in rn.childs]
	ue_delay = [status[ue.name]['delay']\
	for rn in base_station.childs for ue in rn.childs]
	deliver_pkt = [len(rn.queue['access'][ue.name])\
	for rn in base_station.childs for ue in rn.childs]

	PERFORMANCE['RN-PSE'][return_name].append(round(sum(rn_pse)/NUMBER_OF_RN, round_para))
	PERFORMANCE['UE-PSE'][return_name].append(round(sum(ue_pse)/NUMBER_OF_UE, round_para))
	if sum(deliver_pkt):
		PERFORMANCE['DELAY'][return_name].append(\
			round(sum(ue_delay)/sum(deliver_pkt), round_para))
	else:
		PERFORMANCE['DELAY'][return_name].append(0)
	if sum(ue_pse):
		PERFORMANCE['PSE-FAIRNESS'][return_name].append(round(\
			sum(ue_pse)**2/(NUMBER_OF_UE*sum([i**2 for i in ue_pse]))\
			, round_para))
	else:
		PERFORMANCE['PSE-FAIRNESS'][return_name].append(1)
	if sum(ue_delay):
		PERFORMANCE['DELAY-FAIRNESS'][return_name].append(round(\
			sum(ue_delay)**2/(NUMBER_OF_UE*sum([i**2 for i in ue_delay]))
			,round_para))
	else:
		PERFORMANCE['DELAY-FAIRNESS'][return_name].append(1)

	msg_success("==========\t\t%s simulation with lambda %g Mbps end\t\t=========="%\
					(return_name, base_station.lambd['backhaul']))

	return PERFORMANCE

def get_all_sleep_cycle(base_station, simulation_time):
	prefix= "get all sleep cycle\t"
	try:
		round_para = len(str(int(simulation_time/10)))

		scheduling = {
			'TD-aggr': LBPS.top_down,
			'TD-split': LBPS.top_down,
			'TD-merge': LBPS.top_down,
			'BU-aggr': LBPS.bottom_up,
			'BU-split': LBPS.bottom_up,
			'BU-merge': LBPS.bottom_up
		}

		return {
			k:v(k[3:], base_station, simulation_time, check_K=True)
			for (k,v) in scheduling.items()
		}

	except Exception as e:
		msg_fail(str(e), pre=prefix)

if __name__ == '__main__':

	start_time = datetime.now()
	performance_list = {
		'LAMBDA':[],
		'LOAD':[],
		'RN-PSE':{
			'TD-aggr':[],'TD-split':[],'TD-merge':[],\
			'BU-aggr':[],'BU-split':[],'BU-merge':[],\
			'Std-DRX-1':[],'Std-DRX-2':[]},
		'UE-PSE':{
			'TD-aggr':[],'TD-split':[],'TD-merge':[],\
			'BU-aggr':[],'BU-split':[],'BU-merge':[],\
			'Std-DRX-1':[],'Std-DRX-2':[]},
		'DELAY':{
			'TD-aggr':[],'TD-split':[],'TD-merge':[],\
			'BU-aggr':[],'BU-split':[],'BU-merge':[],\
			'Std-DRX-1':[],'Std-DRX-2':[]},
		'PSE-FAIRNESS':{
			'TD-aggr':[],'TD-split':[],'TD-merge':[],\
			'BU-aggr':[],'BU-split':[],'BU-merge':[],\
			'Std-DRX-1':[],'Std-DRX-2':[]},
		'DELAY-FAIRNESS':{
			'TD-aggr':[],'TD-split':[],'TD-merge':[],\
			'BU-aggr':[],'BU-split':[],'BU-merge':[],\
			'Std-DRX-1':[],'Std-DRX-2':[]}
	}

	K_list = {
		'LAMBDA':[],
		'LOAD':[],
		'TD-aggr':{},'TD-split':{},\
		'TD-merge':{},'BU-aggr':{},\
		'BU-split':{},'BU-merge':{}
	}

	def simulate(\
		base_station,\
		iterate_times=10,\
		simulation_time=1000,\
		filename='LBPS'):
		round_para = len(str(int(simulation_time/10)))
		equal_load_performance = copy.deepcopy(performance_list)
		equal_load_K = copy.deepcopy(K_list)

		for i in range(iterate_times):

			# increase lambda
			for rn in base_station.childs:
				for ue in rn.childs:
					rn.connect(ue, interface='access', bandwidth=BANDWIDTH)

			timeline = base_station.simulate_timeline(simulation_time)
			base_station.choose_tdd_config(timeline, fixed=17)

			# # tune sleep cycle for testing
			# k = get_all_sleep_cycle(base_station, simulation_time)
			# equal_load_K['LAMBDA'].append(base_station.lambd['backhaul'])
			# equal_load_K['LOAD'].append(round(LBPS.getLoad(base_station, 'TDD'), round_para))
			# update_nested_dict(equal_load_K, k)

			# test lbps performance in transmission scheduling
			performance = transmission_scheduling(base_station, timeline)
			update_nested_dict(equal_load_performance, performance)

			# test short DRX
			performance = DRX(base_station,\
				timeline,\
				inactivity_timer=40,\
				return_name="Std-DRX-1")
			update_nested_dict(equal_load_performance, performance)

			# test longDRX
			performance = DRX(base_station,\
				timeline,\
				inactivity_timer=40,\
				short_cycle=160,\
				return_name="Std-DRX-2")
			update_nested_dict(equal_load_performance, performance)

			equal_load_performance['LAMBDA'].append(base_station.lambd['backhaul'])
			equal_load_performance['LOAD'].append(round(LBPS.getLoad(base_station, 'TDD'), round_para))
			processing_time = "processing time: {}".format(datetime.now()-start_time)
			msg_warning(processing_time)

		pprint(equal_load_performance, indent=2)
		export_csv(equal_load_performance, filename=filename)
		# export_sleep_cycle(base_station, equal_load_K, filename=filename+'_K')


	"""[summary] Case: equal load

	"""
	# create device instance
	base_station = eNB()
	relays = [RN() for i in range(NUMBER_OF_RN)]
	users = [UE() for i in range(NUMBER_OF_UE)]

	# assign the relationship and CQI
	base_station.childs = relays
	for i in range(len(relays)):
		relays[i].childs = users[i*40:i*40+40]
		relays[i].parent = base_station
		relays[i].CQI = 15
		for j in range(i*40, i*40+40):
			users[j].parent = relays[i]
			users[j].CQI = 15

	# build up the bearer from parent to child
	for i in base_station.childs:
		base_station.connect(i, interface='backhaul', bandwidth=BANDWIDTH)

	simulate(base_station, ITER_TIMES, SIMULATION_TIME, filename="equal_load")
	processing_time = "processing time: {}".format(datetime.now()-start_time)
	msg_success(processing_time)

	del base_station
	del relays
	del users

	# """[summary] Case: 8:2 load

	# """
	# # create device instance
	# base_station = eNB()
	# relays = [RN() for i in range(NUMBER_OF_RN)]
	# users = [UE() for i in range(NUMBER_OF_UE)]

	# # assign the relationship and CQI
	# base_station.childs = relays
	# for i in range(2):
	# 	relays[i].childs = users[i*96:i*96+96]
	# 	relays[i].parent = base_station
	# 	relays[i].CQI = 15
	# 	for j in range(i*96, i*96+96):
	# 		users[j].parent = relays[i]
	# 		users[j].CQI = 15

	# for i in range(len(relays)-2):
	# 	relays[i+2].childs = users[192+i*12:192+i*12+12]
	# 	relays[i+2].parent = base_station
	# 	relays[i+2].CQI = 15
	# 	for j in range(192+i*12, 192+i*12+12):
	# 		users[j].parent = relays[i+2]
	# 		users[j].CQI = 15

	# # build up the bearer from parent to child
	# for i in base_station.childs:
	# 	base_station.connect(i, interface='backhaul', bandwidth=BANDWIDTH)

	# simulate(base_station, ITER_TIMES, SIMULATION_TIME, filename="hot_spot")
	# processing_time = "processing time: {}".format(datetime.now()-start_time)
	# msg_success(processing_time)
