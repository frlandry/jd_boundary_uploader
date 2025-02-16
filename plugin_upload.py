#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Plugin Upload Script
                              A QGIS Plugin Utility
                              -------------------------
 Description:
    This script uploads a QGIS plugin package (ZIP file) to the official QGIS
    Plugin Repository. It uses XML-RPC to communicate with the repository server
    and requires valid user credentials.

 Usage:
    Run this script with the plugin ZIP file as an argument. Options include
    specifying the username, password, server, and port.
    
 Author: A. Pasotti, V. Picavet (Template Authors)
 Modified by: Frederic Landry (frlandry@gmail.com)
 Date: 2025-02-15
 License: GNU General Public License (GPL v2 or later)
***************************************************************************/

"""

import sys
import getpass
import xmlrpc.client
from optparse import OptionParser

# Import standard library aliases (if needed)
from future import standard_library
standard_library.install_aliases()

# -----------------------------------------------------------------------------
# Global Configuration Variables
# -----------------------------------------------------------------------------
PROTOCOL = 'https'
SERVER = 'plugins.qgis.org'
PORT = '443'
ENDPOINT = '/plugins/RPC2/'
VERBOSE = False

# -----------------------------------------------------------------------------
# FUNCTION: main
# -----------------------------------------------------------------------------
def main(parameters, arguments):
    """
    Main entry point for uploading the plugin package.
    
    Parameters:
        parameters: Command line parameters containing username, password, etc.
        arguments: Command line arguments; expects a single argument for the plugin ZIP file.
    """
    address = "{protocol}://{username}:{password}@{server}:{port}{endpoint}".format(
        protocol=PROTOCOL,
        username=parameters.username,
        password=parameters.password,
        server=parameters.server,
        port=parameters.port,
        endpoint=ENDPOINT)
    print("Connecting to: %s" % hide_password(address))

    # Create an XML-RPC server proxy for communication
    server = xmlrpc.client.ServerProxy(address, verbose=VERBOSE)

    try:
        with open(arguments[0], 'rb') as handle:
            # Upload the plugin package as a binary file
            plugin_id, version_id = server.plugin.upload(
                xmlrpc.client.Binary(handle.read()))
        print("Plugin ID: %s" % plugin_id)
        print("Version ID: %s" % version_id)
    except xmlrpc.client.ProtocolError as err:
        print("A protocol error occurred")
        print("URL: %s" % hide_password(err.url, 0))
        print("HTTP/HTTPS headers: %s" % err.headers)
        print("Error code: %d" % err.errcode)
        print("Error message: %s" % err.errmsg)
    except xmlrpc.client.Fault as err:
        print("A fault occurred")
        print("Fault code: %d" % err.faultCode)
        print("Fault string: %s" % err.faultString)

# -----------------------------------------------------------------------------
# FUNCTION: hide_password
# -----------------------------------------------------------------------------
def hide_password(url, start=6):
    """
    Masks the password portion in a URL with asterisks.
    
    Parameters:
        url (str): The URL containing the username and password.
        start (int): The starting index for masking (default is 6).
    
    Returns:
        str: The URL with the password portion replaced by asterisks.
    """
    start_position = url.find(':', start) + 1
    end_position = url.find('@')
    return "%s%s%s" % (
        url[:start_position],
        '*' * (end_position - start_position),
        url[end_position:])

# -----------------------------------------------------------------------------
# MAIN EXECUTION BLOCK
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = OptionParser(usage="%prog [options] plugin.zip")
    parser.add_option(
        "-w", "--password", dest="password",
        help="Password for plugin site", metavar="******")
    parser.add_option(
        "-u", "--username", dest="username",
        help="Username of plugin site", metavar="user")
    parser.add_option(
        "-p", "--port", dest="port",
        help="Server port to connect to", metavar="80")
    parser.add_option(
        "-s", "--server", dest="server",
        help="Specify server name", metavar="plugins.qgis.org")
    options, args = parser.parse_args()
    if len(args) != 1:
        print("Please specify zip file.\n")
        parser.print_help()
        sys.exit(1)
    if not options.server:
        options.server = SERVER
    if not options.port:
        options.port = PORT
    if not options.username:
        # Interactive mode to set username
        username = getpass.getuser()
        print("Please enter user name [%s] :" % username, end=' ')
        res = input()
        if res != "":
            options.username = res
        else:
            options.username = username
    if not options.password:
        # Interactive mode to set password
        options.password = getpass.getpass()
    main(options, args)
