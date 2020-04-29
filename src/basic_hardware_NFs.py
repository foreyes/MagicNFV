# TODO: 加上 Cost 属性
# TODO: 实现 Codition 和 ValueSource, get_read_fields
# TODO: 实现 Field, State, Packet
# TODO: 区分 字段，包状态，全局状态

from framework import NFNode, write_field
from copy import deepcopy

class Start(NFNode):
	def __init__(self):
		super().__init__()
		# 提示不可被交换位置
		self._attributes = {"hardware": True, "will_not_read": set(), "will_not_write": set()}

	def solve_packet(self, packet, states):
		return 0

	def __str__(self):
		return "Start"


class Discard(NFNode):
	def __init__(self):
		super().__init__()
		self._attributes = {"hardware": True, "will_read": set(), "will_write": set()}

	def solve_packet(self, packet, states):
		return -1

	def __str__(self):
		return "Discard"


class DecIpTTL(NFNode):
	def __init__(self, dec_times = 1):
		super().__init__()
		self._attributes = {"hardware": True, "will_read": {("packet", "ip_ttl")}, "will_write": {("packet", "ip_ttl")}}
		self._dec_times = dec_times

	def solve_packet(self, packet, states):
		ip_ttl = packet.read_field("ip_ttl")
		packet.write_field("ip_ttl", ip_ttl - self._dec_times)
		return 0

	def __str__(self):
		return "DecIpTTL_" + str(self._dec_times)


class BasicClassifier(NFNode):
	# 默认 else 是丢弃
	def __init__(self, conditions = [], children = [Discard()]):
		super().__init__()
		self._children = children
		self._attributes = {"hardware": True, "will_write": set()}
		self.set_conditions(conditions)

	def set_conditions(self, conditions):
		self._conditions = conditions
		self._attributes["will_read"] = set()
		for cond in conditions:
			self._attributes["will_read"] |= cond.get_read_fields()

	def get_conditions(self):
		return deepcopy(self._conditions)

	def solve_packet(self, packet, states):
		for i in range(len(self._conditions)):
			if self._conditions[i].check_with_packet_and_states(packet, states):
				return i
		return len(self._conditions)

	def __str__(self):
		return "BasicClassifier"


# "发送" 操作在模拟情形下处理为 "丢弃"，但是不能被任何操作交换位置(需读写所有字段)
class SendOut(NFNode):
	def __init__(self):
		super().__init__()
		self._attributes = {"hardware": True, "will_not_read": set(), "will_not_write": set()}

	def solve_packet(self, packet, states):
		return -1

	def __str__(self):
		return "SendOut"

# 写一个字段
class WriteNF(NFNode):
	def __init__(self, field, value_source):
		super().__init__()
		self._field = field
		self._value_source = value_source
		self._attributes = {"hardware": True, "will_write": {field}}
		self._attributes["will_write"] = value_source.get_read_fields()

	def solve_packet(self, packet, states):
		value = self._value_source.get_value(packet, states)
		write_field(self._field, value, packet, states)
		return 0

	def __str__(self):
		return "Write\n" + str(self._field[0]) + "_" + str(self._field[1]) + " = " + str(self._value_source)