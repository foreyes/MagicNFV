from framework import Node

NoChildNode = Node

class StatefulNode(Node):
	pass

class SingleChildNode(Node):
	def set_child(self, node):
		self.child = node

	def set_child_instead(self, child, instead):
		self.child = instead

	def accept(self, visitor):
		skip_child = visitor.enter(self)
		if not skip_child:
			if hasattr(self, 'child'):
				self.child.accept(visitor)
		visitor.leave(self)

class MultipleChildNode(Node):
	def __init__(self, type = ''):
		super().__init__(type)
		self.childs = []

	def set_children(self, childs = []):
		self.childs = childs

	def set_one_child(self, idx, child):
		self.childs[idx] = child

	def add_child(self, child):
		if not hasattr(self, 'childs'):
			self.childs = []
		self.childs.append(child)

	def set_child_instead(self, child, instead):
		for i in range(len(self.childs)):
			if self.childs[i] is child:
				self.set_one_child(i, instead)

	def delete_one_child(self, idx):
		self.childs.pop(idx)

	def delete_child(self, child):
		for i in range(len(self.childs)):
			if self.childs[i] is child:
				self.delete_one_child(i)

	def copy(self):
		res = super().copy()
		if hasattr(self, 'childs'):
			res.childs = self.childs[:]
		return res

	def accept(self, visitor):
		skip_child = visitor.enter(self)
		if not skip_child:
			if hasattr(self, 'childs'):
				for child in self.childs:
					child.accept(visitor)
		visitor.leave(self)

class StateRecorderNode(Node):
	def record_state(self):
		pass

class RewriterNode(Node):
	def rewrite_packet(self):
		pass

#### useful classes
class DropNode(NoChildNode):
	def __init__(self):
		super().__init__('Drop')

class OutTrafficNode(SingleChildNode):
	def __init__(self):
		super().__init__('OutTraffic')

class ReadFrameNode(SingleChildNode):
	def __init__(self, ip_addr = ''):
		self.ip_addr = ip_addr
		super().__init__('ReadFrame, ip: {}'.format(ip_addr))

class StripEthernetHeaderNode(SingleChildNode):
	def __init__(self):
		super().__init__('StripEthernetHeader')

class ReadIpAddressNode(SingleChildNode):
	def __init__(self):
		super().__init__('ReadIpAddress')

class IpLookUpNode(SingleChildNode, StateRecorderNode):
	def __init__(self):
		super().__init__('IpLookUp')

class DecrementIpTTLNode(SingleChildNode, RewriterNode):
	def __init__(self, times = 1):
		super().__init__()
		self.times = times

	def __str__(self):
		return 'DecrementIpTTL{}'.format(self.times)

class IpFragmentationNode(SingleChildNode, RewriterNode):
	def __init__(self):
		super().__init__('IpFragmentation')

class EncapsulateEthernetNode(SingleChildNode, RewriterNode):
	def __init__(self):
		super().__init__('EncapsulateEthernet')

class WriteFrameNode(SingleChildNode, RewriterNode):
	def __init__(self):
		super().__init__('WriteFrame')
		self.set_child(OutTrafficNode())

class RewriteNode(SingleChildNode, RewriterNode):
	def __init__(self, content = {}):
		super().__init__('Rewrite')
		self.content = content

class StatefulRewriteNode(SingleChildNode, RewriterNode, StatefulNode):
	def __init__(self):
		super().__init__('StatefulRewrite')

class ClassifierNode(MultipleChildNode):
	def __init__(self):
		super().__init__('Classifier')
		self.conds = []

	def set_conds(self, conds):
		self.conds = conds

	def delete_child(self, child):
		for i in range(len(self.childs)):
			if self.childs[i] is child:
				self.delete_one_child(i)
				self.conds.pop(i)
				return

class OutClassifierNode(MultipleChildNode):
	def __init__(self):
		super().__init__('OutClassifier')
		self.conds = []

	def set_conds(self, conds):
		self.conds = conds

	def delete_child(self, child):
		for i in range(len(self.childs)):
			if self.childs[i] is child:
				self.delete_one_child(i)
				self.conds.pop(i)
				return