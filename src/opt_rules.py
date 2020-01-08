import copy, nodes
from framework import Condition


# These codes are ugly, and will be modified later.
# These codes are ugly, and will be modified later.
# These codes are ugly, and will be modified later.
# These codes are ugly, and will be modified later.
# These codes are ugly, and will be modified later.
# These codes are ugly, and will be modified later.
# These codes are ugly, and will be modified later.

# rule_split
class split_solver:
	def __init__(self):
		self.node_set = set()

	def get_new_child(self, child):
		if child in self.node_set:
			child = child.copy()
		return child

	def split_nodes(self, node):
		self.node_set.add(node)
		if hasattr(node, 'child'):
			child = self.get_new_child(node.child)
			node.set_child(child)
			self.split_nodes(child)
		elif hasattr(node, 'childs'):
			for i in range(len(node.childs)):
				child = self.get_new_child(node.childs[i])
				node.set_one_child(i, child)
				self.split_nodes(child)

def apply_rule_split(nf):
	solver = split_solver()
	solver.split_nodes(nf.in_node)

# rule_out_traffic_classification
class out_traffic_classification_solver():
	def __init__(self):
		pass

	def add_classifier_for_nfs(self, nfs):
		for nf in nfs:
			for node in nf.out_nodes:
				if not isinstance(node, nodes.OutTrafficNode):
					continue
				classifier = nodes.OutClassifierNode()
				classifier.set_children([suc.in_node for suc in nf.successors] + [nodes.OutTrafficNode()])
				classifier.set_conds([Condition({'ip_dst': suc.in_node.ip_addr}) for suc in nf.successors] + [Condition({})])
				node.set_child(classifier)

def apply_rule_out_traffic_classification(nfs):
	solver = out_traffic_classification_solver()
	solver.add_classifier_for_nfs(nfs)

# rule_out_traffic_elimination
class out_traffic_elimination_solver():
	def eliminate(self, node):
		if hasattr(node, 'child'):
			child = node.child
			if isinstance(child, nodes.OutTrafficNode):
				if hasattr(child, 'child'):
					node.set_child(child.child)
			self.eliminate(node.child)
		elif hasattr(node, 'childs'):
			for i in range(len(node.childs)):
				child = node.childs[i]
				if isinstance(child, nodes.OutTrafficNode):
					if hasattr(child, 'child'):
						node.set_one_child(i, child.child)
				self.eliminate(node.childs[i])

def apply_rule_out_traffic_elimination(nf):
	solver = out_traffic_elimination_solver()
	solver.eliminate(nf.in_node)

# rule_classifier_pull_up
class out_classifier_pull_up_solver:
	def __init__(self):
		self.visit_stack = []

	def pull_up(self, node):
		if isinstance(node, nodes.OutClassifierNode):
			fa, fafa = self.visit_stack[-1], self.visit_stack[-2]
			for i in range(len(node.childs)):
				child = node.childs[i]
				new_child = fa.copy()
				new_child.set_child(child)
				node.set_one_child(i, new_child)
			fafa.set_child(node)
		self.visit_stack.append(node)
		if hasattr(node, 'child'):
			self.pull_up(node.child)
		elif hasattr(node, 'childs'):
			for child in node.childs:
				self.pull_up(child)
		self.visit_stack.pop()

def apply_rule_out_classifier_pull_up(nf):
	# 3 times
	solver = out_classifier_pull_up_solver()
	solver.pull_up(nf.in_node)
	solver = out_classifier_pull_up_solver()
	solver.pull_up(nf.in_node)
	solver = out_classifier_pull_up_solver()
	solver.pull_up(nf.in_node)

# rule_write_read_elimination
class write_read_elimination_solver:
	def __init__(self):
		self.visit_stack = []

	def eliminate(self, node):
		if isinstance(node, nodes.WriteFrameNode):
			if hasattr(node, 'child') and isinstance(node.child, nodes.ReadFrameNode):
				pre = self.visit_stack[-3]
				nxt = node.child.child.child
				pre.set_one_child(0, nxt)
		# recursive
		self.visit_stack.append(node)
		if hasattr(node, 'child'):
			self.eliminate(node.child)
		elif hasattr(node, 'childs'):
			for child in node.childs:
				self.eliminate(child)
		self.visit_stack.pop()

def apply_rule_write_read_elimination(nf):
	solver = write_read_elimination_solver()
	solver.eliminate(nf.in_node)

# rule_predicate_push_down
class predicate_push_down_solver:
	def __init__(self):
		self.visit_stack = []

	def push_down(self, node):
		if self.visit_stack:
			fa = self.visit_stack[-1]
			node.state.update(fa.state)
		node.state.update(node.extra_state)

		self.visit_stack.append(node)
		if hasattr(node, 'child'):
			if hasattr(node, 'content'):
				node.child.extra_state.update(node.content)
			self.push_down(node.child)
		elif hasattr(node, 'childs'):
			for i in range(len(node.childs)):
				child = node.childs[i]
				if hasattr(node, 'conds'):
					node.conds[i].update_to_state(child.extra_state)
				self.push_down(child)
		self.visit_stack.pop()

def apply_rule_predicate_push_down(nf):
	solver = predicate_push_down_solver()
	solver.push_down(nf.in_node)

# rule_branch_elimination
class branch_elimination_solver:
	def __init__(self):
		self.visit_stack = []

	def cond_match(self, cond, state):
		return cond.match(state)

	def run(self, nf):
		self.eliminate(nf.in_node)

	def eliminate(self, node):
		if isinstance(node, nodes.ClassifierNode) or isinstance(node, nodes.OutClassifierNode):
			dels = []
			fa = self.visit_stack[-1]
			for i in range(len(node.conds)):
				match_res = self.cond_match(node.conds[i], node.state)
				if match_res == 0:
					continue
				elif match_res == -1:
					dels.append(node.childs[i])
				else:
					fa.set_child(node.childs[i])
					self.eliminate(node.childs[i])
					return
			for child in dels:
				node.delete_child(child)

		self.visit_stack.append(node)
		if hasattr(node, 'child'):
			self.eliminate(node.child)
		elif hasattr(node, 'childs'):
			for child in node.childs:
				self.eliminate(child)
		self.visit_stack.pop()

def apply_rule_branch_elimination(nf):
	solver = branch_elimination_solver()
	solver.run(nf)

# rule_classifier_elimination
class classifier_elimination_solver:
	def __init__(self):
		self.visit_stack = []

	def eliminate(self, node):
		if isinstance(node, nodes.ClassifierNode) or isinstance(node, nodes.OutClassifierNode):
			if len(node.childs) == 1:
				fa = self.visit_stack[-1]
				fa.set_child_instead(node, node.childs[0])
				self.eliminate(node.childs[0])
				return

		self.visit_stack.append(node)
		if hasattr(node, 'child'):
			self.eliminate(node.child)
		elif hasattr(node, 'childs'):
			for child in node.childs:
				self.eliminate(child)
		self.visit_stack.pop()

def apply_rule_classifier_elimination(nf):
	solver = classifier_elimination_solver()
	solver.eliminate(nf.in_node)

# rule_ttl_push_down
class ttl_push_down_solver:
	def __init__(self):
		self.visit_stack = []

	def push_down(self, node):
		if isinstance(node, nodes.DecrementIpTTLNode) and not isinstance(node.child, nodes.IpFragmentationNode):
			fa = self.visit_stack[-1]
			fa.set_child_instead(node, node.child)
			if isinstance(node.child, nodes.DropNode):
				return
			if isinstance(node.child, nodes.DecrementIpTTLNode):
				node.child.times += node.times
				self.push_down(node.child)
				return
			child = node.child
			if hasattr(child, 'child'):
				node.child = child.child
				child.child = node
				self.push_down(child)
				return
			if hasattr(child, 'childs'):
				for branch in child.childs:
					new_ttl = node.copy()
					new_ttl.set_child(branch)
					child.set_child_instead(branch, new_ttl)
				self.push_down(child)
				return

		self.visit_stack.append(node)
		if hasattr(node, 'child'):
			self.push_down(node.child)
		elif hasattr(node, 'childs'):
			for child in node.childs:
				self.push_down(child)
		self.visit_stack.pop()

def apply_rule_ttl_push_down(nf):
	solver = ttl_push_down_solver()
	solver.push_down(nf.in_node)

# rule_early_drop			
class early_drop_solver:
	def __init__(self):
		self.visit_stack = []
		self.classifier_stack = []

	def is_drop_child(self, child):
		return isinstance(child, nodes.DropNode)

	def has_drop_child(self, node):
		for child in node.childs:
			if self.is_drop_child(child):
				return True
		return False

	def solve(self, node):
		self.visit_stack.append(node)
		if isinstance(node, nodes.ClassifierNode) or isinstance(node, nodes.OutClassifierNode):
			self.classifier_stack.append(node)
		if hasattr(node, 'child'):
			self.solve(node.child)
		elif hasattr(node, 'childs'):
			for child in node.childs:
				self.solve(child)

		if isinstance(node, nodes.ClassifierNode) or isinstance(node, nodes.OutClassifierNode):
			self.classifier_stack.pop()
			if self.has_drop_child(node) and len(self.classifier_stack) > 0:
				pre = self.classifier_stack[-1]
				additional_cond, drop_node = None, None
				for i in range(len(node.childs)):
					if self.is_drop_child(node.childs[i]):
						drop_node = node.childs[i]
						continue
					if additional_cond is None:
						additional_cond = node.conds[i]
					else:
						additional_cond = additional_cond.Or(node.conds[i])
				additional_cond.eliminate_with_state(node.state)
				# print(str(additional_cond))

				for i in range(len(pre.childs)):
					# in current stack
					child = pre.childs[i]
					if child in self.visit_stack:
						pre.conds[i] = pre.conds[i].And(additional_cond)

				node.delete_child(drop_node)

		self.visit_stack.pop()

def apply_rule_early_drop(nf):
	solver = early_drop_solver()
	solver.solve(nf.in_node)