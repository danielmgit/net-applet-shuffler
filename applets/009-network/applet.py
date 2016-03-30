# usage: exec 009-network setup:direct host1 host2 host3 ...
# obviously, also the physical replug hast to happen as well

import os
import subprocess
import time

from threading import Thread

LOCAL_CONT_PATH = os.path.dirname(os.path.realpath(__file__))
REMOTE_CONT_PATH = "/tmp/net-applet-shuffler"
CONTR_NAME = "network-controller.py"


class ControllerStart(Thread):

    host_user = "host_user"
    host_ip = "host_ip"
    arguments = "arguments"

    def __init__(self, user, ip, arguments):
        Thread.__init__(self)
        self.daemon = True
        self.host_user = user
        self.host_ip = ip
        self.arguments = arguments

    def run(self):
        ssh_command = "ssh {}@{} sudo python3.5 {}/{} {}".format(
            self.host_user, self.host_ip, REMOTE_CONT_PATH, CONTR_NAME,
            self.arguments)
        process = subprocess.Popen(ssh_command.split(), stdout=subprocess.PIPE)
        process.communicate()


def distribute_network_controller(x, host_user, host_ip):
    _, _, exit_code = x.ssh.exec(host_ip, host_user, "test -f {}/{}"
                                 .format(REMOTE_CONT_PATH, CONTR_NAME))
    # if exit_code != 0 -> does not exist on host
    if not exit_code == 0:
        x.ssh.copy_to_restricted(host_user, host_ip, LOCAL_CONT_PATH,
                                 REMOTE_CONT_PATH, CONTR_NAME, CONTR_NAME)


def main(x, conf, args):
    if not len(args) > 1:
        x.p.msg("wrong usage. use: setup:[direct|indirect] host1 host2 "
                "host3...\n")
        return False

    setup = args[0].split(":")[1]
    # arguments for controller on hosts
    host_list = list()
    # read in all host names
    for host_number in range(0, (len(args))):
        name_host = str(args[host_number])
        if "setup:" not in name_host:
            host_list.append(name_host)
    # distribute the network controller program
    for host_name in host_list:
        host_user = conf.get_user(host_name)
        host_ip = conf.get_ip(host_name, 0)
        distribute_network_controller(x, host_user, host_ip)
    x.p.msg("network controllers distributed\n")
    # start the network controllers
    for host_name in host_list:
        host_user = conf.get_user(host_name)
        host_ip = conf.get_ip(host_name, 0)
        host_interface = conf.get_iface_name(host_name, 0)
        host_def_route = conf.get_default_route(host_name, 0)
        arguments = "{} {} {} {}".format(setup, host_interface, host_ip,
                                         host_def_route)
        host_thread = ControllerStart(host_user, host_ip, arguments)
        host_thread.start()
    # sleep a minimum of 24 (network controller sleeps) + 2 (safety margin)
    # seconds, unfortunately this is necessary
    time.sleep(26)
    x.p.msg("direct setup (hopefully) completed\n")

    return True