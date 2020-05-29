from framework import NFNode, ValueSource, Expression, Condition
from basic_hardware_NFs import *
from sample_software_NFs import *

def get_ppt_sample_network():
	st = Start()
	fw = SampleFirewall()
	decTTL1 = DecIpTTL()
	decTTL2 = DecIpTTL()
	classifier1 = BasicClassifier()
	classifier2 = BasicClassifier()
	w_state1 = WriteNF(("private", "P"), Condition("const", "T1"))
	w_state2 = WriteNF(("private", "P"), Condition("const", "U1"))
	drop = Discard()
	load_balance = SampleLoadBalance()
	send_out = SendOut()

	st.set_children([fw])
	fw.set_children([decTTL1, drop])
	decTTL1.set_children([classifier1])

	field_protocol = Condition("field", ("packet", "protocol"))
	eq2TCP = Condition("==", (field_protocol, Condition("const", "TCP")))
	eq2UDP = Condition("==", (field_protocol, Condition("const", "UDP")))
	field_port = Condition("field", ("packet", "port"))
	eq2port1 = Condition("==", (field_port, Condition("const", 1)))

	classifier1.set_conditions([Condition("and", (eq2TCP, eq2port1)), Condition("and", (eq2UDP, eq2port1))])
	classifier1.set_children([w_state1, w_state2, drop])
	w_state1.set_children([decTTL2])
	w_state2.set_children([decTTL2])
	decTTL2.set_children([classifier2])

	field_P = Condition("field", ("private", "P"))
	eq2T1 = Condition("==", (field_P, Condition("const", "T1")))

	classifier2.set_conditions([eq2T1])
	classifier2.set_children([load_balance, drop])
	load_balance.set_children([send_out])

	return st

def get_NAPT_sample():
	st = Start()
	ed = SendOut()
	napt = NAPT([("1.1.1.1", 1080, "192.168.0.1", 20), ("1.1.1.1", 1081, "192.168.0.2", 20), ("1.1.1.1", 1082, "192.168.0.3", 20), ("1.1.1.1", 1083, "192.168.0.4", 20)])
	st.set_children([napt.entrance])
	napt.exit.set_children([ed])
	return st

ppt_sample_network = get_ppt_sample_network()

sample_NATP_network = get_NAPT_sample()