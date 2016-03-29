
import os
import time

from threading import Thread

LOCAL_NET_PATH = os.path.dirname(os.path.realpath(__file__))
REMOTE_NET_PATH = "/tmp/net-applet-shuffler"


def controller_thread(x, arg_d):
    # assemble arguments
    arguments_string = "{} {} {} {} {} {} {} {} {} {} {} {}".format(
        arg_d["applet_id"], arg_d["name_source"], arg_d["user_source"],
        arg_d["ip_source"], arg_d["port_source"], arg_d["name_dest"],
        arg_d["user_dest"], arg_d["ip_dest"], arg_d["port_dest"],
        arg_d["netserver_port"], arg_d["flow_length"], arg_d["flow_offset"])
    # check if netperf controller is already on source
    _, _, exit_code = x.ssh.exec(arg_d["ip_source"], arg_d["user_source"],
            "test -f {}/netperf-controller.py".format(REMOTE_NET_PATH))
    # if not, copy it to source
    if not exit_code == 0:
        x.ssh.copy_to_restricted(arg_d["user_source"], arg_d["ip_source"],
                                 LOCAL_NET_PATH, REMOTE_NET_PATH,
                                 "netperf-controller.py",
                                 "netperf-controller.py")
    x.ssh.exec(arg_d["ip_source"], arg_d["user_source"], "python3.5 {}/{} {}"
               .format(REMOTE_NET_PATH, "netperf-controller.py",
                       arguments_string))
    return True


def main(x, conf, args):

    if not len(args) == 8:
        x.p.msg("wrong usage. use: [name] sink:[name] id:[id] source_port:["
                "port] sink_port:[port] length:[bytes|seconds] "
                "flow_offset:[seconds] netserver:[port]\n")
        return False
    # arguments dictionary
    arg_d = dict()
    arg_d["name_source"] = args[0]
    arg_d["name_dest"] = args[1].split(":")[1]
    arg_d["applet_id"] = args[2].split(":")[1]
    arg_d["port_source"] = args[3].split(":")[1]
    arg_d["port_dest"] = args[4].split(":")[1]
    arg_d["flow_length"] = args[5].split(":")[1]
    arg_d["flow_offset"] = args[6].split(":")[1]
    arg_d["netserver_port"] = args[7].split(":")[1]
    # retrieve: source ip, source user name, destination ip, destination user name
    arg_d["ip_source"] = conf.get_ip(arg_d["name_source"], 0)
    arg_d["user_source"] = conf.get_user(arg_d["name_source"])
    arg_d["ip_dest"] = conf.get_ip(arg_d["name_dest"], 0)
    arg_d["user_dest"] = conf.get_user(arg_d["name_dest"])

    # potentially start parallel netperf instances
    # note: at this point, the distribution of the applet will be done, which
    # is probably not the best way to do (can cause unwanted time offsets)
    x.p.msg("Starting netperf applet on host {}\n".format(
                                                        arg_d["user_source"]))
    contr_thread = Thread(target=controller_thread, args=(x, arg_d, ))
    contr_thread.daemon = True
    contr_thread.start()

    return True
