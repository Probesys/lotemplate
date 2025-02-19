"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'Connexion',
    'start_office',
)

import os
from sorcery import dict_of
import shlex
import subprocess
import uno
from com.sun.star.connection import NoConnectException
from com.sun.star.uno import RuntimeException
from time import sleep
from . import errors
#from .utils import *
from .WriterTemplate import WriterTemplate
from .CalcTemplate import CalcTemplate

def start_office(host:str="localhost",port:str="2000"):
    """
    start one process LibreOffice

    :param host:  define host in the UNO connect-string --accept
    :param port:   define port in the UNO connect-string --accept
    environnement had to be different for each environnement
    """
    subprocess.Popen(
             shlex.split('soffice \
             -env:UserInstallation="file:///tmp/LibO_Process'+port+'" \
            -env:UserInstallation="file:///tmp/LibO_Process'+port+'" \
            "--accept=socket,host="'+host+',port='+port+';urp;" \
            --headless --nologo --terminate_after_init \
            --norestore " '), shell=False, stdin = subprocess.PIPE,
                     stdout = subprocess.PIPE,)
    return host, port,'file:///tmp/LibO_Process'+str(port)


class Connexion:

    def __repr__(self):
        return (
            f"<Connexion object :'host'={self.host!r}, 'port'={self.port!r}, "
            f"'local_ctx'={self.local_ctx!r}, 'ctx'={self.local_ctx!r}, 'desktop'={self.desktop!r}, "
            f"'graphic_provider'={self.graphic_provider!r}>"
        )

    def __str__(self):
        return f"Connexion host {self.host}, port {self.port}"

    def __init__(self, host: str, port: str):
        """
        An object representing the connexion between the script and the LibreOffice/OpenOffice processus

        :param host: the address of the host to connect to
        :param port: the host port to connect to
        """

        self.host = host
        self.port = port
        self.local_ctx = uno.getComponentContext()
        for attempt in range(3):
            try:
                self.ctx = self.local_ctx.ServiceManager.createInstanceWithContext(
                    "com.sun.star.bridge.UnoUrlResolver", self.local_ctx
                ).resolve(f"uno:socket,host={host},port={port};urp;StarOffice.ComponentContext")
            except (NoConnectException, RuntimeException) as e:
                if attempt==0:
                    sleep(4)
                elif  attempt<2:
                    start_office(host,port)
                    sleep(5)
                else:
                    raise errors.UnoException(
                        'connection_error',
                        f"Couldn't find/connect to the soffice process on \'{host}:{port}\'. "
                        f"Make sure the soffice process is correctly running with correct host and port informations. "
                        f"Read the README file, section 'Executing the script' for more informations about how to "
                        f"run the script.", dict_of(host, port)
                    ) from e
            else:
                break
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
        self.graphic_provider = self.ctx.ServiceManager.createInstance('com.sun.star.graphic.GraphicProvider')

    def restart(self) -> None:
        """
        Restart the connexion

        :return: None
        """
        print( "##### RESTART One Office#####")
        self.__init__(self.host, self.port)

def TemplateFromExt(file_path: str, cnx: Connexion, should_scan: bool):

        filename, file_extension = os.path.splitext(file_path)
        ods_ext=('.xls','.xlsx','.ods')
        if file_extension in ods_ext:
             document = CalcTemplate(file_path, cnx , should_scan)
        else:
             document = WriterTemplate(file_path, cnx , should_scan)
        return document

