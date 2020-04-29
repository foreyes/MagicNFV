from framework import Painter
from sample_networks import ppt_sample_network
from optimizer import split_path, path_arrange, hardware_classifier_pull_up, software_arrange

networks = ppt_sample_network
split_path(networks)
path_arrange(networks)
hardware_classifier_pull_up(networks)
software_arrange(networks)
p = Painter(networks)
p.show()