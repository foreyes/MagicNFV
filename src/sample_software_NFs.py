from framework import NFNode, AllFields

class SampleFirewall(NFNode):
	def __init__(self):
		super().__init__()
		# 提示可能需要读所有字段，但不会写任何字段
		self._attributes = {"hardware": False, "will_not_read": set(), "will_write": set()}

	def solve_packet(self, packet, states):
		ip_src = packet.read_field("ip_src")
		if ip_src != "127.0.0.1":
			return 1
		return 0

	def get_cost(self, is_hardware):
		return 1.5

	def __str__(self):
		return "SampleFirewall"


class SampleLoadBalance(NFNode):
	def __init__(self):
		super().__init__()
		# 提示不会读任何字段，但是会写 ip_dst
		self._attributes = {"hardware": False, "will_read": set(), "will_write": {("packet", "ip_dst")}}

	def solve_packet(self, packet, states):
		ip_dst_list = ["192.168.0.5", "192.168.0.6", "192.168.0.7", "192.168.0.8"]
		from random import choice
		ip_dst = choice(ip_dst_list)
		packet.write_field("ip_dst", ip_dst)
		return 0

	def get_cost(self, is_hardware):
		return 3.5

	def __str__(self):
		return "SampleLoadBalance"


# 实验用的软件路由。链成一条链了，于是只固定发送到下一个，代价直接通过估算值计算。
class SampleRouter(NFNode):
	def __init__(self):
		super().__init__()
		self._attributes = {"hardware": False, "will_read": {("packet", AllFields)}, "will_write": {("packet", "ethenet_header")}}

	def get_cost(self, is_hardware):
		return 55

	def solve_packet(self, packet, states):
		packet.write_field("ethenet_header", "test")
		return 0
