from framework import Visitor, Node, NetworkFunction, Condition
import nodes, visitors, opt_rules

def get_nf1():
	rf = nodes.ReadFrameNode('192.168.0.1')
	seh = nodes.StripEthernetHeaderNode()
	classifer = nodes.ClassifierNode()
	drop = nodes.DropNode()
	# random 1000-9000
	rw1, rw2 = nodes.RewriteNode({'ip_src': '10.0.0.1', 'ip_dst': '10.0.0.2'}), nodes.RewriteNode({'port_src': 1234, 'ip_dst': '192.168.0.2'})
	ri = nodes.ReadIpAddressNode()
	il = nodes.IpLookUpNode()
	dttl = nodes.DecrementIpTTLNode()
	ifrag = nodes.IpFragmentationNode()
	ee = nodes.EncapsulateEthernetNode()
	wf = nodes.WriteFrameNode()

	rf.set_child(seh)
	seh.set_child(classifer)
	classifer.set_children([rw1, rw2, drop])
	classifer.set_conds([Condition({'protocol': 'UDP'}), Condition({'protocol': 'TCP'}), Condition({})])
	rw1.set_child(ri)
	rw2.set_child(ri)
	ri.set_child(il)
	il.set_child(dttl)
	dttl.set_child(ifrag)
	ifrag.set_child(ee)
	ee.set_child(wf)

	nf = NetworkFunction()
	nf.set_in_node(rf)
	nf.set_out_nodes([wf.child, drop])

	return nf

def get_nf2():
	rf = nodes.ReadFrameNode('10.0.0.2')
	seh = nodes.StripEthernetHeaderNode()
	rw = nodes.RewriteNode({'ip_dst': '10.0.0.3'})
	f = nodes.ClassifierNode()
	drop = nodes.DropNode()
	dttl = nodes.DecrementIpTTLNode()
	ifrag = nodes.IpFragmentationNode()
	ee = nodes.EncapsulateEthernetNode()
	wf = nodes.WriteFrameNode()

	rf.set_child(seh)
	seh.set_child(rw)
	rw.set_child(f)
	f.set_children([dttl, drop])
	f.set_conds([Condition({'ip_src': '10.0.0.1', 'port_dst': 1234}), Condition({})])
	dttl.set_child(ifrag)
	ifrag.set_child(ee)
	ee.set_child(wf)

	nf = NetworkFunction()
	nf.set_in_node(rf)
	nf.set_out_nodes([wf.child, drop])

	return nf

def get_nf3():
	rf = nodes.ReadFrameNode('10.0.0.3')
	seh = nodes.StripEthernetHeaderNode()
	srw = nodes.StatefulRewriteNode()
	dttl = nodes.DecrementIpTTLNode()
	ifrag = nodes.IpFragmentationNode()
	ee = nodes.EncapsulateEthernetNode()
	wf = nodes.WriteFrameNode()

	rf.set_child(seh)
	seh.set_child(srw)
	srw.set_child(dttl)
	dttl.set_child(ifrag)
	ifrag.set_child(ee)
	ee.set_child(wf)

	nf = NetworkFunction()
	nf.set_in_node(rf)
	nf.set_out_nodes([wf.child])

	return nf

if __name__ == '__main__':
	# get NFs and define DAG
	nf1, nf2, nf3 = get_nf1(), get_nf2(), get_nf3()
	nf1.add_successor(nf2)
	nf2.add_successor(nf3)

	# draw original picture
	org = visitors.Painter('original')
	nf1.in_node.accept(org)
	nf2.in_node.accept(org)
	nf3.in_node.accept(org)
	org.show()

	# applay optimize rules and draw pictures
	opt_rules.apply_rule_out_traffic_classification([nf1, nf2, nf3])
	nf1.show(visitors.Painter('s1'))
	opt_rules.apply_rule_split(nf1)
	nf1.show(visitors.Painter('s2'))
	opt_rules.apply_rule_out_traffic_elimination(nf1)
	nf1.show(visitors.Painter('s3'))
	opt_rules.apply_rule_out_classifier_pull_up(nf1)
	nf1.show(visitors.Painter('s4'))
	opt_rules.apply_rule_write_read_elimination(nf1)
	nf1.show(visitors.Painter('s5'))
	opt_rules.apply_rule_predicate_push_down(nf1)
	nf1.show(visitors.Painter('s6'))
	opt_rules.apply_rule_branch_elimination(nf1)
	nf1.show(visitors.Painter('s7'))
	opt_rules.apply_rule_classifier_elimination(nf1)
	nf1.show(visitors.Painter('s8'))
	opt_rules.apply_rule_ttl_push_down(nf1)
	nf1.show(visitors.Painter('s9'))
	opt_rules.apply_rule_early_drop(nf1)
	opt_rules.apply_rule_classifier_elimination(nf1)
	nf1.show(visitors.Painter('s10'))