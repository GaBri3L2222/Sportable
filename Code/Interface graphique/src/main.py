#!/usr/bin/env -P /usr/bin:/usr/local/bin python3 -B
# coding: utf-8

#
#  main.py
#  Interface graphique
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
import threading

import ingescape as igs
from PyQt5.QtWidgets import QApplication
from Interface_graphique import *

port = 5670
agent_name = "Interface graphique"
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
        assert isinstance(agent_object, Interface_graphique)
        # add code here if needed
    except:
        print(traceback.format_exc())



# inputs
def Squelette_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.SqueletteI = value
        agent_object.signal_bridge.update_squelette.emit(value)
        # add code here if needed
    except:
        print(traceback.format_exc())

def Vision_State_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.Vision_StateI = value
        agent_object.signal_bridge.update_vision_state.emit(value)
        # add code here if needed
    except:
        print(traceback.format_exc())

def Feedback_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.FeedbackI = value
        agent_object.signal_bridge.update_feedback.emit(value)
        # add code here if needed
    except:
        print(traceback.format_exc())

def Current_Exercice_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.Current_ExerciceI = value
        agent_object.signal_bridge.update_current_exercice.emit(value)
        # add code here if needed
    except:
        print(traceback.format_exc())

def Rep_Remaining_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.Rep_RemainingI = value
        agent_object.signal_bridge.update_rep_remaining.emit(value)
        agent_object.signal_bridge.update_ui.emit()
        # add code here if needed
    except:
        print(traceback.format_exc())

def Set_Remaining_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.Set_RemainingI = value
        agent_object.signal_bridge.update_set_remaining.emit(value)
        agent_object.signal_bridge.update_ui.emit()
        # add code here if needed
    except:
        print(traceback.format_exc())

def Rest_Time_Remaining_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.Rest_Time_RemainingI = value
        agent_object.signal_bridge.update_rest_time.emit(value)
        agent_object.signal_bridge.update_ui.emit()
        # add code here if needed
    except:
        print(traceback.format_exc())

def Session_State_input_callback(io_type, name, value_type, value, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        agent_object.Session_StateI = value
        
        # Switch view based on session state
        if agent_object.window:
            if value == "configuration":
                agent_object.window.show_config_view()
            elif value == "execution":
                agent_object.window.show_execution_view()
        # add code here if needed
    except:
        print(traceback.format_exc())

# services
def Settotaldisplay_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    try:
        agent_object = my_data
        assert isinstance(agent_object, Interface_graphique)
        Displayjson = tuple_args[0]
        agent_object.Settotaldisplay(sender_agent_name, sender_agent_uuid, Displayjson)
    except:
        print(traceback.format_exc())


def run_ingescape_thread(agent, device, port):
    """Run Ingescape in a separate thread"""
    igs.observe_agent_events(on_agent_event_callback, agent)

    igs.input_create("squelette", igs.STRING_T, None)
    igs.observe_input("squelette", Squelette_input_callback, agent)
    igs.input_create("vision_state", igs.BOOL_T, None)
    igs.observe_input("vision_state", Vision_State_input_callback, agent)
    igs.input_create("feedback", igs.STRING_T, None)
    igs.observe_input("feedback", Feedback_input_callback, agent)
    igs.input_create("current_exercice", igs.STRING_T, None)
    igs.observe_input("current_exercice", Current_Exercice_input_callback, agent)
    igs.input_create("rep_remaining", igs.INTEGER_T, None)
    igs.observe_input("rep_remaining", Rep_Remaining_input_callback, agent)
    igs.input_create("set_remaining", igs.INTEGER_T, None)
    igs.observe_input("set_remaining", Set_Remaining_input_callback, agent)
    igs.input_create("rest_time_remaining", igs.INTEGER_T, None)
    igs.observe_input("rest_time_remaining", Rest_Time_Remaining_input_callback, agent)
    igs.input_create("session_state", igs.STRING_T, None)
    igs.input_set_description("session_state", """<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\np, li { white-space: pre-wrap; }\nhr { height: 1px; border-width: 0; }\nli.unchecked::marker { content: \"\\2610\"; }\nli.checked::marker { content: \"\\2612\"; }\n</style></head><body style=\" font-family:'Asap'; font-size:12px; font-weight:400; font-style:normal;\">\n<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">programation, execution de la seance</p></body></html>""")
    igs.observe_input("session_state", Session_State_input_callback, agent)

    igs.output_create("fin_timer", igs.IMPULSION_T, None)

    igs.service_init("setTotalDisplay", Settotaldisplay_callback, agent)
    igs.service_arg_add("setTotalDisplay", "displayJSON", igs.STRING_T)

    igs.start_with_device(device, port)

    while (not is_interrupted) and igs.is_started():
        time.sleep(0.1)

    igs.stop()


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
    igs.definition_set_class("Interface graphique")
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
            print("using %s as default network device (this is the only one available that is not the loopback)" % str(device))
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

    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create agent
    agent = Interface_graphique()
    
    # Initialize GUI
    agent.initialize_gui()
    
    # Start Ingescape in a separate thread
    igs_thread = threading.Thread(target=run_ingescape_thread, args=(agent, device, port), daemon=True)
    igs_thread.start()

    # Run Qt event loop
    sys.exit(app.exec_())
