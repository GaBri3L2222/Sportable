#!/usr/bin/env -P /usr/bin:/usr/local/bin python3 -B
# coding: utf-8

#
#  main.py
#  Moteur
#  Created by Sportable & Co on 2026/01/09
#
# "no description"
#

import signal
import getopt
import time
from pathlib import Path
import traceback
import sys

from Moteur import *

port = 5670
agent_name = "Moteur"
device = None
verbose = False
is_interrupted = False

short_flag = "hvip:d:n:"
long_flag = ["help", "verbose", "interactive_loop", "port=", "device=", "name="]

ingescape_path = Path("~/Documents/Ingescape").expanduser()


def print_usage():
    print("Usage example: ", agent_name, " --verbose --port 5670 --device device_name")
    print("\nthese parameters have default value (indicated here above):")
    print("--verbose : enable verbose mode in the application (default is disabled)")
    print("--port port_number : port used for autodiscovery between agents (default: 31520)")
    print("--device device_name : name of the network device to be used (useful if several devices available)")
    print("--name agent_name : published name for this agent (default: ", agent_name, ")")
    print("--interactive_loop : enables interactive loop to pass commands in CLI (default: false)")


def print_usage_help():
    print("Available commands in the terminal:")
    print("	/quit : quits the agent")
    print("	/help : displays this message")

def return_io_value_type_as_str(value_type):
    if value_type == igs.INTEGER_T:
        return "Integer"
    elif value_type == igs.DOUBLE_T:
        return "Double"
    elif value_type == igs.BOOL_T:
        return "Bool"
    elif value_type == igs.STRING_T:
        return "String"
    elif value_type == igs.IMPULSION_T:
        return "Impulsion"
    elif value_type == igs.DATA_T:
        return "Data"
    else:
        return "Unknown"

def return_event_type_as_str(event_type):
    if event_type == igs.PEER_ENTERED:
        return "PEER_ENTERED"
    elif event_type == igs.PEER_EXITED:
        return "PEER_EXITED"
    elif event_type == igs.AGENT_ENTERED:
        return "AGENT_ENTERED"
    elif event_type == igs.AGENT_UPDATED_DEFINITION:
        return "AGENT_UPDATED_DEFINITION"
    elif event_type == igs.AGENT_KNOWS_US:
        return "AGENT_KNOWS_US"
    elif event_type == igs.AGENT_EXITED:
        return "AGENT_EXITED"
    elif event_type == igs.AGENT_UPDATED_MAPPING:
        return "AGENT_UPDATED_MAPPING"
    elif event_type == igs.AGENT_WON_ELECTION:
        return "AGENT_WON_ELECTION"
    elif event_type == igs.AGENT_LOST_ELECTION:
        return "AGENT_LOST_ELECTION"
    else:
        return "UNKNOWN"

def signal_handler(signal_received, frame):
    global is_interrupted
    print("\n", signal.strsignal(signal_received), sep="")
    is_interrupted = True


def on_agent_event_callback(event, uuid, name, event_data, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        # add code here if needed
    except:
        print(traceback.format_exc())



# inputs
def Rep_Validated_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        # add code here if needed
    except:
        print(traceback.format_exc())

# services
def Stopworkout_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        agent_object.Stopworkout(sender_agent_name, sender_agent_uuid)
    except:
        print(traceback.format_exc())


def Startworkout_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        agent_object.Startworkout(sender_agent_name, sender_agent_uuid)
    except:
        print(traceback.format_exc())


def Removerecuperation_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        Recuperationid = tuple_args[0]
        agent_object.Removerecuperation(sender_agent_name, sender_agent_uuid, Recuperationid)
    except:
        print(traceback.format_exc())


def Addrecuperation_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        agent_object.Addrecuperation(sender_agent_name, sender_agent_uuid)
    except:
        print(traceback.format_exc())


def Addexercice_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        agent_object.Addexercice(sender_agent_name, sender_agent_uuid)
    except:
        print(traceback.format_exc())


def Removeexercice_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Moteur)
        Exerciceid = tuple_args[0]
        agent_object.Removeexercice(sender_agent_name, sender_agent_uuid, Exerciceid)
    except:
        print(traceback.format_exc())


if __name__ == "__main__":

    # catch SIGINT handler before starting agent
    signal.signal(signal.SIGINT, signal_handler)
    interactive_loop = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], short_flag, long_flag)
    except getopt.GetoptError as err:
        igs.error(err)
        sys.exit(2)
    for o, a in opts:
        if o == "-h" or o == "--help":
            print_usage()
            exit(0)
        elif o == "-v" or o == "--verbose":
            verbose = True
        elif o == "-i" or o == "--interactive_loop":
            interactive_loop = True
        elif o == "-p" or o == "--port":
            port = int(a)
        elif o == "-d" or o == "--device":
            device = a
        elif o == "-n" or o == "--name":
            agent_name = a
        else:
            assert False, "unhandled option"

    igs.agent_set_name(agent_name)
    igs.definition_set_class("Moteur")
    igs.log_set_console(verbose)
    igs.log_set_file(True, None)
    igs.log_set_stream(verbose)
    igs.set_command_line(sys.executable + " " + " ".join(sys.argv))

    igs.debug(f"Ingescape version: {igs.version()} (protocol v{igs.protocol()})")

    if device is None:
        # we have no device to start with: try to find one
        list_devices = igs.net_devices_list()
        list_addresses = igs.net_addresses_list()
        if len(list_devices) == 1:
            device = list_devices[0]
            igs.info("using %s as default network device (this is the only one available)" % str(device))
        elif len(list_devices) == 2 and (list_addresses[0] == "127.0.0.1" or list_addresses[1] == "127.0.0.1"):
            if list_addresses[0] == "127.0.0.1":
                device = list_devices[1]
            else:
                device = list_devices[0]
            print("using %s as de fault network device (this is the only one available that is not the loopback)" % str(device))
        else:
            if len(list_devices) == 0:
                igs.error("No network device found: aborting.")
            else:
                igs.error("No network device passed as command line parameter and several are available.")
                print("Please use one of these network devices:")
                for device in list_devices:
                    print("	", device)
                print_usage()
            exit(1)

    agent = Moteur()

    igs.observe_agent_events(on_agent_event_callback, agent)

    igs.input_create("rep_validated", igs.IMPULSION_T, None)
    igs.observe_input("rep_validated", Rep_Validated_input_callback, agent)

    igs.output_create("current_exercice", igs.STRING_T, None)
    igs.output_create("rep_remaining", igs.INTEGER_T, None)
    igs.output_create("set_remaining", igs.INTEGER_T, None)
    igs.output_create("rest_time_remaining", igs.INTEGER_T, None)
    igs.output_set_description("rest_time_remaining", """<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\np, li { white-space: pre-wrap; }\nhr { height: 1px; border-width: 0; }\nli.unchecked::marker { content: \"\\2610\"; }\nli.checked::marker { content: \"\\2612\"; }\n</style></head><body style=\" font-family:'Asap'; font-size:12px; font-weight:400; font-style:normal;\">\n<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">en secondes</p></body></html>""")
    igs.output_create("session_state", igs.STRING_T, None)
    igs.output_create("workout_summary", igs.STRING_T, None)

    igs.service_init("stopWorkout", Stopworkout_callback, agent)
    igs.service_reply_add("stopWorkout", "updateVue");
    igs.service_reply_arg_add("stopWorkout", "updateVue", "displayJSON", igs.STRING_T);
    igs.service_init("startWorkout", Startworkout_callback, agent)
    igs.service_reply_add("startWorkout", "updateVue");
    igs.service_reply_arg_add("startWorkout", "updateVue", "displayJSON", igs.STRING_T);
    igs.service_init("removeRecuperation", Removerecuperation_callback, agent)
    igs.service_arg_add("removeRecuperation", "recuperationID", igs.INTEGER_T)
    igs.service_reply_add("removeRecuperation", "updateVue");
    igs.service_reply_arg_add("removeRecuperation", "updateVue", "displayJSON", igs.STRING_T);
    igs.service_init("addRecuperation", Addrecuperation_callback, agent)
    igs.service_reply_add("addRecuperation", "updateVue");
    igs.service_reply_arg_add("addRecuperation", "updateVue", "displayJSON", igs.STRING_T);
    igs.service_init("addExercice", Addexercice_callback, agent)
    igs.service_reply_add("addExercice", "updateVue");
    igs.service_reply_arg_add("addExercice", "updateVue", "displayJSON", igs.STRING_T);
    igs.service_init("removeExercice", Removeexercice_callback, agent)
    igs.service_arg_add("removeExercice", "exerciceID", igs.INTEGER_T)
    igs.service_reply_add("removeExercice", "updateVue");
    igs.service_reply_arg_add("removeExercice", "updateVue", "displayJSON", igs.STRING_T);

    igs.start_with_device(device, port)
    # catch SIGINT handler after starting agent
    signal.signal(signal.SIGINT, signal_handler)

    if interactive_loop:
        print_usage_help()
        while True:
            command = input()
            if command == "/quit":
                break
            elif command == "/help":
                print_usage_help()
    else:
        while (not is_interrupted) and igs.is_started():
            time.sleep(0.1)

    igs.stop()
