#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
import serial
import serial.tools.list_ports

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def space_pad(number, length):
    """
    Return a number as a string, padded with spaces to make it the given length

    :param number: the number to pad with spaces
    :param length: the specified length
    :returns: the number padded with spaces as a string
    """

    number_length = len(str(number))
    spaces_to_add = length - number_length
    return (' ' * spaces_to_add) + str(number)


def get_local_json_contents(json_filename):
    """
    Returns the contents of a (local) JSON file

    :param json_filename: the filename (as a string) of the local JSON file
    :returns: the data of the JSON file
    """

    try:
        with open(json_filename) as json_file:
            try:
                data = json.load(json_file)
            except ValueError:
                print('Contents of "' + json_filename + '" are not valid JSON')
                raise
    except IOError:
        print('An error occurred while reading "' + json_filename + '"')
        raise

    return data


def get_json_contents(json_url):
    """
    Return the contents of a (remote) JSON file

    :param json_url: the url (as a string) of the remote JSON file
    :returns: the data of the JSON file
    """

    data = None

    req = Request(json_url)
    try:
        response = urlopen(req).read()
    except HTTPError as e:
        print('HTTPError ' + str(e.code))
    except URLError as e:
        print('URLError ' + str(e.reason))
    else:
        try:
            data = json.loads(response.decode('utf-8'))
        except ValueError:
            print('Invalid JSON contents')

    return data


def find_in_data(ohw_data, name):
    """
    Search in the OpenHardwareMonitor data for a specific node, recursively

    :param ohw_data:    OpenHardwareMonitor data object
    :param name:        Name of node to search for
    :returns:           The found node, or -1 if no node was found
    """
    if ohw_data['Text'] == name:
        # The node we are looking for is this one
        return ohw_data
    elif len(ohw_data['Children']) > 0:
        # Look at the node's children
        for child in ohw_data['Children']:
            if child['Text'] == name:
                # This child is the one we're looking for
                return child
            else:
                # Look at this children's children
                result = find_in_data(child, name)
                if result != -1:
                    # Node with specified name was found
                    return result
    # When this point is reached, nothing was found in any children
    return -1


def get_hardware_info(ohw_ip, ohw_port, cpu_name, gpu_name, gpu_mem_size):
    """
    Get hardware info from OpenHardwareMonitor's web server and format it
    """

    # Init arrays
    my_info = {}
    gpu_info = {}
    cpu_core_temps = {}

    ohw_json_url = 'http://' + ohw_ip + ':' + ohw_port + '/data.json'

    # Get data from OHW's data json file
    data_json = get_json_contents(ohw_json_url)

    # Get info for CPU
    cpu_data = find_in_data(data_json, cpu_name)

    #cpu_temps = find_in_data(cpu_data, 'Temperatures')
    cpu_load = find_in_data(cpu_data, 'CPU Total')

    # Get CPU total load, and remove ".0 %" from the end
    cpu_load_value = cpu_load['Value'][:-4]

    my_info['cpu_load'] = cpu_load_value

    # Get info for GPU
    gpu_data = find_in_data(data_json, gpu_name)

    gpu_clocks = find_in_data(gpu_data, 'Clocks')
    gpu_load = find_in_data(gpu_data, 'Load')

    gpu_core_clock = find_in_data(gpu_clocks, 'GPU Core')
    gpu_mem_clock = find_in_data(gpu_clocks, 'GPU Memory')
    gpu_temp = find_in_data(find_in_data(gpu_data, 'Temperatures'), 'GPU Core')
    gpu_core_load = find_in_data(gpu_load, 'GPU Core')
    fan_rpm = find_in_data(find_in_data(gpu_data, 'Fans'), 'GPU')
    fan_percent = find_in_data(find_in_data(gpu_data, 'Controls'), 'GPU Fan')
    gpu_mem_percent = find_in_data(gpu_load, 'GPU Memory')

    # Calculate how many MB of GPU memory are used based on the percentage
    used_percentage = float(gpu_mem_percent['Value'][:-2])
    used_mb = int((gpu_mem_size * used_percentage) / 100)

    # Add GPU info to GPU object
    gpu_info['temp'] = gpu_temp['Value'][:-5]
    gpu_info['load'] = gpu_core_load['Value'][:-4]
    gpu_info['core_clock'] = gpu_core_clock['Value'][:-4]
    
    # Memory clock divided by 2 so it is the same as GPU-Z reports
    gpu_info['mem_clock'] = int(int(gpu_mem_clock['Value'][:-4]) )#/ 2)
    gpu_info['used_mem'] = used_mb
    gpu_info['fan_percent'] = fan_percent['Value'][:-4]
    gpu_info['fan_rpm'] = fan_rpm['Value'][:-4]

    # Add GPU info to my_info
    my_info['gpu'] = gpu_info

    return my_info


def main():
    # Get serial ports
    ports = list(serial.tools.list_ports.comports())

    # Load config JSON
    cd = os.path.join(os.getcwd(), os.path.dirname(__file__))
    __location__ = os.path.realpath(cd)
    config = get_local_json_contents(os.path.join(__location__, 'config.json'))

    # If there is only 1 serial port (so it is the Arduino) connect to that one
    if len(ports) > 1:
        # Connect to the port
        port = 'COM3'
        print('Only 1 port found: ' + port + '. Connecting to it...')
        ser = serial.Serial(port,baudrate=9600,timeout=1.0)
        
		#ser.flushOutput()
        while True:
            # Get current info
            my_info = get_hardware_info(
                config["ohw_ip"],
                config["ohw_port"],
                config["cpu_name"],
                config["gpu_name"],
                config["gpu_mem_size"]
            )

            # Prepare CPU string
            cpu = \
                space_pad(int(my_info['cpu_load']), 4) + '%'

            # Prepare GPU strings
            gpu_info = my_info['gpu']
            gpu1 = \
            	space_pad(int(gpu_info['load']), 4) + '% ' + \
            	space_pad(int(gpu_info['temp']), 4) + 'C ' + \
            	space_pad(int(gpu_info['used_mem']), 4) + ' MB'

            gpu2 = \
            	space_pad(int(gpu_info['fan_percent']), 4) + '% F ' + \
            	space_pad(int(gpu_info['fan_rpm']), 4) + ' RPM'

            gpu3 = \
            	space_pad(int(gpu_info['core_clock']), 4) + '|' + \
            	space_pad(int(gpu_info['mem_clock']), 4) + ' MHz'

            ser.flushInput()
            # Send the strings via serial to the Arduino
            ser.write(str('C' + cpu + '/G' + gpu1 + '/F' + gpu2 +
                      	  '/A' + gpu3 + '/').encode())
            ser.flushOutput()
            # Wait until refreshing Arduino again
            time.sleep(1.0)
            cpu=""
            gpu1=""
            gpu2=""
            gpu3=""
        ser.close()
    else:
     	
     	print('Number of ports is not 1, can\'t connect!')

if __name__ == '__main__':
    main()
