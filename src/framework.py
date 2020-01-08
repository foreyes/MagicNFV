# Visitor object is used to recursively access a NF
class Visitor:
	def __str__(self):
		return 'Visitor'

	def enter(self, node):
		print(node)
		return False

	def leave(self, node):
		pass

# Node object means a node in NF
class Node:
	def __init__(self, type = ''):
		self.type = type
		self.state = {e: 'null' for e in ['ip_src', 'ip_dst', 'protocol', 'port_src', 'port_dst']}
		# the state updated by rewrite nodes
		self.extra_state = {}

	def __str__(self):
		if self.type:
			return self.type
		else:
			return 'Node'

	# copy return an copy of a node
	def copy(self):
		import copy
		res = copy.copy(self)
		res.state = self.state.copy()
		res.extra_state = self.extra_state.copy()
		return res

	def accept(self, visitor):
		visitor.enter(self)
		visitor.leave(self)

# NetworkFunction object means a NF
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

	# connect adds an edge between two NFs
	def connect(self, out_idx, nf):
		node1 = self.out_nodes[out_idx]
		node2 = nf.in_node
		if hasattr(node1, 'set_child'):
			node1.set_child(node2)
		if hasattr(node1, 'add_child'):
			node1.add_child(node2)

# Condition object means conditions for a branch or expression
class Condition:
	def __init__(self, cond = {}):
		self.type = 'normal'
		self.cond = cond

	# eliminate_with_state extracts conditions which are not satisfied yet.
	def eliminate_with_state(self, state):
		if self.type == 'normal':
			pops = []
			for key in self.cond:
				if key in state and self.cond[key] == state[key]:
					pops.append(key)
			for key in pops:
				self.cond.pop(key)

	# And constructs an 'And' Condition
	def And(self, cond):
		and_node = Condition()
		and_node.type = 'and'
		and_node.oprands = [self, cond]
		return and_node

	# Or constructs a 'Or' Condition
	def Or(self, cond):
		or_node = Condition()
		or_node.type = 'or'
		or_node.oprands = [self, cond]
		return or_node

	# update_to_state update a state if this Condition's type if normal
	def update_to_state(self, state):
		if self.type == 'normal':
			state.update(self.cond)

	# match checks if the given state satisfy this Condition
	# -1 False, 0 Unknown, 1 True
	def match(self, state):
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

# class Graph:
# 	def __init__(self):
# 		# idx -> node, node -> idx
# 		self.nodes = {}
# 		self.node_idx = {}
# 		# idx -> edge, edge -> idx
# 		self.edges = {}
# 		self.edge_idx = {}

# 	# return idx, add same node twice will do nothing
# 	def add_node(self, node):
# 		if node not in self.node_idx:
# 			idx = len(self.nodes)
# 			self.nodes[idx] = node
# 			self.node_idx[node] = idx
# 		return self.node_idx[node]

# 	# return idx, add same edge twice will do nothing
# 	def add_edge(self, edge):
# 		if edge not in self.edge_idx:
# 			idx = len(self.edges)
# 			self.edges[idx] = edge
# 			self.edge_idx[edge] = idx
# 		return self.edge_idx[edge]
