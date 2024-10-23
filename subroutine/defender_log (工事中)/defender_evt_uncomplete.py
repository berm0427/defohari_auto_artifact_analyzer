import subprocess
import os
import re

# Change the working directory to the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def run_de_evt_parsing():
    """Step 1: Run defender_log_parsing.py to parse EVT files and save them"""
    subprocess.run(['python', 'defender_log_parsing.py'], check=True)

def run_de_evt_2_xml(evtx_file_path):
    """Step 2: Run defender_log.py to convert EVT files to XML"""
    subprocess.run(['python', 'defender_log.py', evtx_file_path], check=True)
    
def run_de_xml_2_csv(xml_file_path):
    """Step 3: Run Xml_csv_defender.py to convert XML files to CSV"""
    subprocess.run(['python', 'Xml_csv_defender.py', xml_file_path], check=True)

def run_broken_recovery(script_name):
    """Step 4: If CSV is broken, run the appropriate recovery script"""
    subprocess.run(['python', script_name], check=True)

def main():
    # Step 1: Run defender_log_parsing.py to parse EVT files
    output_dir = os.path.abspath(os.path.join('..', '..', 'output', 'artifact', 'defender_log'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    run_de_evt_parsing()
    
    # Define the general patterns to match EVT filenames
    general_patterns = [
        r'^Microsoft-Windows-Windows Defender%4\w+\.evtx$',  # Defender event logs
        r'^Microsoft-Windows-Windows Firewall With Advanced Security%4\w+\.evtx$',  # Firewall event logs
    ]
    compiled_general_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in general_patterns]
    
    # List all files in the output directory
    evtx_files = os.listdir(output_dir)
    for evtx_filename in evtx_files:
        evtx_file_path = os.path.abspath(os.path.join(output_dir, evtx_filename))
        if not os.path.isfile(evtx_file_path):
            continue  # Skip directories or non-files

        # Check if the file matches any of the general patterns
        match_found = False
        for pattern in compiled_general_patterns:
            if pattern.match(evtx_filename):
                match_found = True
                break
        if not match_found:
            continue  # Skip files that don't match the general patterns

        # Step 2: Convert EVT file to XML
        if os.path.exists(evtx_file_path):
            run_de_evt_2_xml(evtx_file_path)
            # Assume the XML file has the same name but with .xml extension
            xml_filename = os.path.splitext(evtx_filename)[0] + '.xml'
            xml_file_path = os.path.join(output_dir, xml_filename)
            if os.path.exists(xml_file_path):
                # Step 3: Convert XML file to CSV
                run_de_xml_2_csv(xml_file_path)
                # Assume the CSV file has the same name but with .csv extension
                csv_filename = os.path.splitext(evtx_filename)[0] + '.csv'
                csv_file_path = os.path.join(output_dir, csv_filename)
                if not os.path.exists(csv_file_path):
                    print(f"{csv_file_path} does not exist.")
            else:
                print(f"{xml_file_path} does not exist.")
        else:
            print(f"{evtx_file_path} does not exist.")
    
    # Step 4: Run all recovery scripts
    recovery_scripts = [
        'if_csv_broken_defender_operational.py',
        'if_csv_broken_defender_WHC.py',
        'if_csv_broken_firewall_Diagnostics.py',
        'if_csv_broken_firewall.py',
        'if_csv_broken_firewall_ConnectionSecurity.py'
    ]
    for script_name in recovery_scripts:
        print(f"Running recovery script: {script_name}")
        run_broken_recovery(script_name)

if __name__ == "__main__":
    main()
