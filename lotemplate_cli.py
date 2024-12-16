#!/bin/python3

"""
Copyright (C) 2023 Probesys
"""

import lotemplate as ot

import configargparse as cparse
import json
import urllib.request
import urllib.error
import sys
import traceback
import shlex, subprocess
from time import sleep
import os
import random

def set_arguments() -> cparse.Namespace:
    """
    set up all the necessaries arguments, and return them with their values

    :return: user-given values for set up command-line arguments
    """

    p = cparse.ArgumentParser(default_config_files=['config.yml', 'config.ini', 'config'])
    p.add_argument('template_file',
                   help="Template file to scan or fill")
    p.add_argument('--json_file', '-jf', nargs='+', default=[],
                   help="Json files that must fill the template, if any")
    p.add_argument('--json', '-j', nargs='+', default=[],
                   help="Json strings that must fill the template, if any")
    p.add_argument('--output', '-o', default="output.pdf",
                   help="Names of the filled files, if the template should be filled. supported formats: "
                        "pdf, html, docx, png, odt")
    p.add_argument('--config', '-c', is_config_file=True, help='Configuration file path')
    p.add_argument('--host', default="localhost", help='Host address to use for the libreoffice connection')
    p.add_argument('--port', default="2002", help='Port to use for the libreoffice connexion')
    p.add_argument('--cpu', default="0", help='number of libreoffice start, default 0 is the number of CPU')
    p.add_argument('--scan', '-s', action='store_true',
                   help="Specify if the program should just scan the template and return the information, or fill it.")
    p.add_argument('--force_replacement', '-f', action='store_true',
                   help="Specify if the program should ignore the scan's result")
    return p.parse_args()

if __name__ == '__main__':

    # get the necessaries arguments
    args = set_arguments()

    # run soffice
    if args.cpu == "0":
        nb_process=len(os.sched_getaffinity(0))
    else:
        nb_process=int(args.cpu)

    for i in range(nb_process):

       subprocess.Popen(
             shlex.split('soffice  -env:UserInstallation="file:///tmp/LibO_Process'+str(i)+'" \
            -env:UserInstallation="file:///tmp/LibO_Process'+str(i)+'" \
            "--accept=socket,host="'+args.host+',port='+args.port+str(i)+';urp;" \
            --headless --nologo --terminate_after_init \
            --norestore " '), shell=False, stdin = subprocess.PIPE,
                     stdout = subprocess.PIPE,)

    #sleep(1+nb_process/2)
    i=random.randint(0,nb_process-1)
    # establish the connection to the server
    connexion = ot.Connexion(args.host, args.port+str(i))
    # generate the document to operate and its parameters
    document = ot.TemplateFromExt(args.template_file, connexion, not args.force_replacement)

    # prints scan result in json format if it should
    if args.scan:
        print(json.dumps(document.variables))

    # fill and export the template if it should
    else:

        # get the specified jsons
        json_dict = {}
        for elem in args.json_file:
            if ot.is_network_based(elem):
                json_dict[elem] = json.loads(urllib.request.urlopen(elem).read())
            else:
                with open(elem) as f:
                    json_dict[elem] = json.loads(f.read())
        for index, elem in enumerate(args.json):
            json_dict[f"json_{index}"] = json.loads(elem)

        for json_name, json_variables in json_dict.items():

            try:
                # scan for errors
                document.search_error(ot.convert_to_datas_template(json_variables))
                #pdb.set_trace()
                # fill and export the document
                document.fill(json_variables)
                if not args.output:
                    filename=json_name
                    path='exports'
                else:
                    filename=os.path.basename(args.output)
                    path=os.path.dirname(args.output)
                    if not path:
                        path='exports'

                print(
                    f"Document saved as " +
                    repr(document.export( filename, path, True))
                )
            except Exception as exception:
                print(f'Ignoring exception on json {repr(json_name)}:', file=sys.stderr)
                traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
                continue
    document.close()
