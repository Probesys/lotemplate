import ootemplate as ot
import configargparse as cparse
import json


def set_arguments() -> cparse.Namespace:
    """
    set up all the necessaries arguments, and return them with their values

    :return: user-given values for set up command-line arguments
    """

    p = cparse.ArgumentParser(default_config_files=['config.ini'])
    p.add_argument('template_file',
                   help="Template file to scan or fill")
    p.add_argument('--json_file', '-jf', nargs='+', default=[],
                   help="Json file(s) that must fill the template, if any")
    p.add_argument('--json', '-j', nargs='+', default=[],
                   help="Json strings that must fill the template, if any")
    p.add_argument('--output', '-o', default="output.pdf",
                   help="Name of the filled file, if the template should be filled. supported formats: "
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
        vars_list = document.compare_variables(ot.get_files_json(args.json_file) | ot.get_normized_json(args.json))
        for json_name, json_values in vars_list.items():
            document.fill(json_values)
            print(
                "File " +
                repr(json_name) +
                " : Document saved as " +
                repr(document.export(
                    args.output if len(vars_list) == 1 else
                    ".".join(args.output.split(".")[:-1]) + '_' + (
                        json_name.split("/")[-1][:-5] if json_name.split("/")[-1][-5:] == ".json"
                        else json_name.split("/")[-1]
                    ) + "." + args.output.split(".")[-1]
                ))
            )
    document.close()

