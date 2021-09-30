import ootemplate as ot
import configargparse as cparse
import json
import urllib.request
import urllib.error


def set_arguments() -> cparse.Namespace:
    """
    set up all the necessaries arguments, and return them with their values

    :return: user-given values for set up command-line arguments
    """

    p = cparse.ArgumentParser(default_config_files=['config.ini'])
    p.add_argument('template_file',
                   help="Template file to scan or fill")
    p.add_argument('--json_file', '-jf', default=None,
                   help="Json file that must fill the template, if any")
    p.add_argument('--json', '-j', default=None,
                   help="Json string that must fill the template, if any")
    p.add_argument('--output', '-o', nargs='+', default=["output.pdf"],
                   help="Names of the filled files, if the template should be filled. supported formats: "
                        "pdf, html, docx, png, odt")
    p.add_argument('--config', '-c', is_config_file=True, help='Configuration file path')
    p.add_argument('--host', required=True, help='Host address to use for the libreoffice connection')
    p.add_argument('--port', required=True, help='Port to use for the libreoffice connexion')
    p.add_argument('--scan', '-s', action='store_true',
                   help="Specify if the program should just scan the template and return the information, or fill it.")
    p.add_argument('--force_replacement', '-f', action='store_true',
                   help="Specify if the program should ignore the scan's result")
    return p.parse_args()


if __name__ == '__main__':
    """
    before running the script, please run the following command on your OpenOffice host:
    
    soffice "--accept=socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"
    
    read the README file for more infos
    """

    # get the necessaries arguments
    args = set_arguments()

    # establish the connection to the server
    connexion = ot.Connexion(args.host, args.port)

    # generate the document to operate and its parameters
    document = ot.Template(args.template_file, connexion, not args.force_replacement)

    # prints scan result in json format if it should
    if args.scan:
        print(json.dumps(document.variables))

    # fill and export the template if it should
    else:

        # get the json value
        if args.json_file:
            if ot.is_network_based(args.json_file):
                values = json.loads(urllib.request.urlopen(args.json_file).read())
            else:
                with open(args.json_file) as f:
                    values = json.loads(f.read())
        elif args.json:
            values = json.loads(args.json)
        else:
            values = []

        # scan for errors
        document.search_error(
            ot.convert_to_datas_template(args.json_file if args.json_file else 'input', values),
            args.json_file if args.json_file else 'input'
        )

        # fill and export the document
        document.fill(values)
        exported = document.export(
            args.output + [args.output][-1] * (len(values) - len(args.output)
                                               if len(values) - len(args.output) > 0 else 0)
        )
        print(*[f"Instance {repr(index)} : Document saved as {repr(name)}" for index, name in enumerate(exported)],
              sep="\n")
    document.close()