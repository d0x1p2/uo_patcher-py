import xml.etree.ElementTree as ET
import os.path, sys
import urllib.request as urlrequest
import errno
from os import name as os_name
from json import loads
from configparser import ConfigParser
from subprocess import Popen

import file_process

# # # # # # # # # # # # # # # # # # #
# Created by: Ryan Ball (0x1p2/Schism)
# Date created: December 4th, 2015
# # # # # # # # # # # # # # # # # # # # # # # # 
# Responsible for parsing the Updates.xml file
#   ( SUPER ) important.
# # # # # # # # # # # # # # # # # # # # # # # #


def xmlparse(xml_data):
    ''' Parses the XML file passed to it. This XML should be obtained
    from a remote host/server and should include the file names, hashes,
    locations(URL), and description of all files that are to be updated. '''
    root = ET.fromstring(xml_data)   # Assign the tree/root of the XML string
    file_dict = {}              # Blank dictionary to hold the informaton of the file.
    file_list = []              # This will append to a list in the dictionary a list of the filenames.

    for UpdateObject in root[0].findall('UpdateObject'):    
        DisplayName = UpdateObject.find('DisplayName').text     # Value of DisplayName
        FileName = UpdateObject.find('FileName').text           # Value of FileName
        URL = UpdateObject.find('URL').text                     # Value of URL
        Description = UpdateObject.find('Description').text     # Value of Description
        Hash = UpdateObject.find('Hash').text.lower()           # Value of Hash (to lowercase to match)

        file_dict[DisplayName] = { "DisplayName": DisplayName,"FileName": FileName, "URL": URL, "Description": Description, "Hash": Hash }
        file_list.append(DisplayName)       # Here's that appen we talked about earlier in the file.

    file_dict['files'] = file_list          # Lastly assign the list to "Files" in the dictionary.

    return file_dict                        # Return the dictionary to be used.


def conf_write(config):
    ''' Creates and writes changes to configuration files.
    If "None" is passed to the function it creates, otherwise it
    writes new changes. '''
    if not os.path.exists('config.ini') and config == None:                     # First time write/create.
        config = ConfigParser()                                                 # Loads configuration class
        config['Files'] = {                                                     # Creates intial Files section.
                'XML_URL': 'http://www.ultima-shards.com/patches/UOP/Updates.xml',  # Places "default" repository for updates.
                'UO_Directory': '' }                                            # Assigns no default UO directory. (to be found or placed by user.)
        config['Files']['config'] = os.getcwd() + "/config.ini"                 # Set the configuration file location.
        config['Hashes'] = {}                                                   # No hashes on start, this will be updated later.
    with open(config['Files']['config'], 'w') as configfile:                    # Writes the changes.
        config.write(configfile)                    

    return config               # Returns the object of the configurtion file.


def conf_read():
    ''' Loads the configuration file. If it doesn't exist it will then call
    the write function to create a new configuration file. Then it will load it. '''
    if not os.path.exists('config.ini'):                # Check for the configuration file
        print("\nCreating configuration file...")
        config = conf_write(None)                       # Create a new configuration file.
    else:
        print("\nLoading configuration file...")
        config = ConfigParser()                         # Generate the configration object

    config.read('config.ini')                           # Assign the object to the data of in the config.ini

    return config                   # Returns the object to be used by another function.


def check_forupdates(app_version):
    ''' Compares patchers version to that of the version at GitHub. Will update if the
    local version is less than that version number remotely. (float number)
    Download is based off of the "Tag" assigned to it.'''
    # # # # # # # # # # # # # # # # # # # # # # # # 
    patcher_update_url = "https://raw.githubusercontent.com/0x1p2/uo_patcher-py/master/README.md"
    patcher_update_base = "https://github.com/0x1p2/uo_patcher-py/releases/download/"
    # # # # # # # # # # # # # # # # # # # # # # # # 
    with urlrequest.urlopen(patcher_update_url) as update_check:
        foreign_request = loads(update_check.readline().decode())   # Grabs the first line of the README.md file.

    if app_version < float(foreign_request['Current-Version']):     # Compares local to remote versions as float numbers.
        print(" Patcher is out-of-date.\n Local version: [ %s ], " % app_version, end="")
        print("Current version: [ %s ]" % foreign_request['Current-Version'])

        if os_name == 'nt':                              # Windows users....
            patcher_file_name = "Ultima_Patcher.exe"   #  Pull Ultima_Patcher.exe
            patcher_tool_name = "patcher_updater_tool.exe"
        else:                                           # Linux users....
            patcher_file_name = "Ultima_Patcher"       #  Pull Ultima_Patcher
            patcher_tool_name = "patcher_updater_tool"

        patcher_update_url = patcher_update_base + foreign_request['Tag'] + '/' + patcher_file_name   # Generates the entire IRL
        patcher_tool_url =  patcher_update_base + foreign_request['Tag'] + '/' + patcher_tool_name    # The patch to the updating tool used for updating the patcher.


        if get_q_answer(" Do you wish to update [Yes/no, enter=yes]: "):
            try:
                if not os.path.isfile(patcher_tool_name):                          # If the stand-alone updater isn't found, 
                    status = file_process.client_update(patcher_tool_url)               # If accepted, it will pull the updater.
                if os_name != 'nt':                                                  # Change the name for linux users.
                    patcher_tool_name = './' + patcher_tool_name                    # Because it requires a different execution.
                Popen([patcher_tool_name, patcher_update_url])                   # Opens a new process for update tool.
                print("Exiting... wait for download of new client. Relaunch patcher on update.")
                sys.exit()
            except FileNotFoundError as file404_err:
                print("  [ ERROR ]  Code: %s, %s" % (file404_err.errno, file404_err.strerror))
            except NameError as name_err:
                print("  [ ERROR ]  Code: %s, %s" % (name_err.errno, name_err.strerror))
            except IOError as conn_err:
                print("  [ ERROR ]  IO Error: [Code: %s, %s]" % (conn_err.errno, conn_err.strerror))

            return False

        else:
            print(" Skipping update.")
            return False

        return True
                    
    else:
        print("  No updates found for patcher.")
        return False


def get_q_answer(question_string):
    yes = set(['yes', 'ye', 'y', ''])                   # Types of "yes"'s allowed.
    no = set(['no', 'n'])                               # Unused as of now.

    question_result = input(question_string).lower()    # Grab input and make it lowercase.
    if question_result in yes:                          # Compare.
        return True                                     #  True = Yes
    else:
        return False                                    #  False = No
