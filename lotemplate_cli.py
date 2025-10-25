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
import os

def set_arguments() -> cparse.Namespace:
    """
    set up all the necessaries arguments, and return them with their values

    :return: user-given values for set up command-line arguments
    """

    p = cparse.ArgumentParser(default_config_files=['config.yml', 'config.ini', 'config'])
    p.add_argument('--template_file', '-t',
                   help="Template file to scan or fill")
    p.add_argument('--json_file', '-jf', 
                   help="Json files that must fill the template, if any")
    p.add_argument('--json', '-j', 
                   help="Json strings that must fill the template, if any")
    p.add_argument('--json_watermark_file', '-jwf', 
                   help="Json files to configure pdf watermark, if any")
    p.add_argument('--json_watermark', '-jw', 
                   help="Json strings to configure pdf watermark, if any")
    p.add_argument('--output', '-o', default="output.pdf",
                   help="Names of the filled files, if the template should be filled. supported formats: "
                        "pdf, html, docx, png, odt")
    p.add_argument('--config', '-c', is_config_file=True, help='Configuration file path')
    p.add_argument('--host', default="localhost", help='Host address to use for the libreoffice connection')
    p.add_argument('--port', default="2002", help='Port to use for the libreoffice connexion')
    p.add_argument('--cpu', default="0", help='number of libreoffice start, default 0 is the number of CPU')
    p.add_argument('--clean', action='store_true',
                   help="Specify if the program should all to old open connection")
    p.add_argument('--maxtime', default="60" , help='number of second before considering a document open for too long')
    p.add_argument('--stats', action='store_true',
                   help="return statistic about open files that should not be")
    p.add_argument('--scan', '-s', action='store_true',
                   help="Specify if the program should just scan the template and return the information, or fill it.")
    p.add_argument('--force_replacement', '-f', action='store_true',
                   help="Specify if the program should ignore the scan's result")
    p.add_argument('--json_cache_dir',nargs='?',  help="Specify a cache for the scanned json")
    args=p.parse_args()
    if not args.scan and not args.clean and not args.template_file and not args.stats:
         p.error(" ####### You need at minimun --scan or --clean or --template_file")
    elif (args.scan and not  args.template_file):
         p.error(" ####### with --scan you need --template_file")
    return args

def load_json_file(file):
    if ot.is_network_based(file):
        json_variables = json.loads(urllib.request.urlopen(file).read())
    else:
        with open(file) as f:
            json_variables = json.loads(f.read())
    return json_variables

if __name__ == '__main__':
    # get the necessaries arguments
    args = set_arguments()
    # run soffice
    if args.cpu == "0":
        nb_process=len(os.sched_getaffinity(0))
    else:
        nb_process=int(args.cpu)

    my_lo=ot.start_multi_office(nb_env=nb_process)
    if args.clean:
        print(json.dumps(ot.clean_old_open_document(my_lo, args.maxtime)))
        exit()

    if args.stats:
        print(json.dumps(ot.statistic_open_document(my_lo, args.maxtime)))
        exit()


    # establish the connection to the server
    connexion = ot.randomConnexion(my_lo)
    # generate the document to operate and its parameters
    document = ot.TemplateFromExt(args.template_file, connexion, not args.force_replacement,args.json_cache_dir)

    # prints scan result in json format if it should
    if args.scan:
        print(json.dumps(document.variables))

    # fill and export the template if it should
    else:
        json_watermark_variables={}
        # get the specified jsons
        json_dict = {}
        if args.json_file:
            json_variables = load_json_file(args.json_file) 
        if args.json:
            json_variables = json.loads(args.json)
        if args.json_watermark_file:
            json_watermark_variables = load_json_file(args.json_watermark_file) 
        if args.json:
            json_watermark_variables = json.loads(args.json_watermark)

        try:
            # scan for errors
            document.search_error(ot.convert_to_datas_template(json_variables))
            #pdb.set_trace()
            # fill and export the document
            document.fill(json_variables)
            filename=os.path.basename(args.output)
            path=os.path.dirname(args.output)
            if not path:
               path='exports'
            print(
                "Document saved as " +
                repr(document.export( filename, path,
                                     True,json_watermark_variables))
            )
        except Exception as exception:
            print('Ignoring exception on json :', file=sys.stderr)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
    document.close()
