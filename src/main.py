from framework import Painter, get_whole_cost
from sample_networks import ppt_sample_network, sample_NATP_network, sample_router_NAPT_chain, sample_classic_NAPT_router_ACL
from optimizer import split_path, path_arrange, hardware_classifier_pull_up, software_arrange

# networks = ppt_sample_network
# split_path(networks)
# path_arrange(networks)
# hardware_classifier_pull_up(networks)
# software_arrange(networks)
# p = Painter(networks)
# p.show()

networks = sample_classic_NAPT_router_ACL
previous_cost = get_whole_cost(networks)
split_path(networks)
path_arrange(networks)
hardware_classifier_pull_up(networks)
software_arrange(networks)
current_cost = get_whole_cost(networks)
print("")
print("优化前代价：{}\n优化后代价：{}".format(previous_cost, current_cost))
print("结构图为 test.gv.pdf")
p = Painter(networks)
p.show()

