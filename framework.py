class Visitor:
	def __init__(self, type = ''):
		self.type = type

	def __str__(self):
		return 'Visitor' + self.type

	# enter(node Node) (skip_child bool)
	def enter(self, node):
		print(node)
		return False

	# leave(node Node) (ok bool)
	def leave(self, node):
		pass

class Node:
	def __init__(self, type = ''):
		self.type = type
		self.state = {e: 'null' for e in ['ip_src', 'ip_dst', 'protocol', 'port_src', 'port_dst']}
		self.extra_state = {}

	def __str__(self):
		if self.type:
			return self.type
		else:
			return 'Node'

	def copy(self):
		import copy
		res = copy.copy(self)
		res.state = self.state.copy()
		res.extra_state = self.extra_state.copy()
		return res

	# accept(visitor Visitor)
	def accept(self, visitor):
		visitor.enter(self)
		visitor.leave(self)

class NetworkFunction:
	def __init__(self):
		self.successors = []

	def set_in_node(self, in_node):
		self.in_node = in_node

	def set_out_nodes(self, out_nodes):
		self.out_nodes = out_nodes

	def add_successor(self, nf):
		self.successors.append(nf)

	def show(self, visitor):
		self.in_node.accept(visitor)
		if hasattr(visitor, 'show'):
			visitor.show()

	def connect(self, out_idx, nf):
		node1 = self.out_nodes[out_idx]
		node2 = nf.in_node
		if hasattr(node1, 'set_child'):
			node1.set_child(node2)
		if hasattr(node1, 'add_child'):
			node1.add_child(node2)

class Condition:
	def __init__(self, cond = {}):
		self.type = 'normal'
		self.cond = cond

	def eliminate_with_state(self, state):
		if self.type == 'normal':
			pops = []
			for key in self.cond:
				if key in state and self.cond[key] == state[key]:
					pops.append(key)
			for key in pops:
				self.cond.pop(key)

	# @staticmethod
	# def Construct_And(cond1, cond2):
	# 	and_node = Condition()
	# 	and_node.type = 'and'
	# 	and_node.oprands = [cond1, cond2]
	# 	return and_node

	# @staticmethod
	# def Construct_Or(cond1, cond2):
	# 	or_node = Condition()
	# 	or_node.type = 'or'
	# 	or_node.oprands = [cond1, cond2]
	# 	return or_node

	def And(self, cond):
		and_node = Condition()
		and_node.type = 'and'
		and_node.oprands = [self, cond]
		return and_node

	def Or(self, cond):
		or_node = Condition()
		or_node.type = 'or'
		or_node.oprands = [self, cond]
		return or_node

	def update_to_state(self, state):
		if self.type == 'normal':
			state.update(self.cond)

	def match(self, state):
		# -1 False, 0 Unknown, 1 True
		if self.type == 'normal':
			cond = self.cond
			if not cond:
				return 0
			for key in cond:
				if key not in state or state[key] == 'null' or state[key] == 'unknown':
					return 0
				if state[key] != cond[key]:
					return -1
			return 1
		elif self.type == 'and':
			final_res = 1
			for cond in self.oprands:
				res = cond.match(state)
				if res == -1:
					return -1
				if res == 0:
					final_res = 0
			return final_res
		else:
			final_res = -1
			for cond in self.oprands:
				res = cond.match(state)
				if res == 1:
					return 1
				if res == 0:
					final_res = 0
			return final_res

	def __str__(self):
		if self.type == 'normal':
			return str(self.cond)
		elif self.type == 'and':
			return '(' + ' && '.join([str(x) for x in self.oprands]) + ')'
		else:
			return '(' + ' || '.join([str(x) for x in self.oprands]) + ')'

	def __repr__(self):
		return self.__str__()

class Graph:
	def __init__(self):
		# idx -> node, node -> idx
		self.nodes = {}
		self.node_idx = {}
		# idx -> edge, edge -> idx
		self.edges = {}
		self.edge_idx = {}

	# return idx, add same node twice will do nothing
	def add_node(self, node):
		if node not in self.node_idx:
			idx = len(self.nodes)
			self.nodes[idx] = node
			self.node_idx[node] = idx
		return self.node_idx[node]

	# return idx, add same edge twice will do nothing
	def add_edge(self, edge):
		if edge not in self.edge_idx:
			idx = len(self.edges)
			self.edges[idx] = edge
			self.edge_idx[edge] = idx
		return self.edge_idx[edge]
