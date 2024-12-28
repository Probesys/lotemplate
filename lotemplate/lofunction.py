"""
Copyright (C) 2023 Probesys


The classes used for document connexion and manipulation
"""

__all__ = (
    'TemplateFromExt',
    'start_multi_office',
    'randomConnexion',
)

import os
from .WriterTemplate import *
from .CalcTemplate import *
from .connexion import *
import shlex,subprocess
import random

def TemplateFromExt(file_path: str, cnx: Connexion, should_scan: bool):

        filename, file_extension = os.path.splitext(file_path)
        ods_ext=('.xls','.xlsx','.ods')
        if file_extension in ods_ext:
             document = CalcTemplate(file_path, cnx , should_scan)
        else:
             document = WriterTemplate(file_path, cnx , should_scan)
        return document


def randomConnexion(lstOffice):
       host,port,lodir = random.choice(lstOffice)
       return Connexion(host,port) 
    

def start_multi_office(host:str="localhost",start_port:int=2000,nb_env:int=1):
    """
    start a nb_env of process LibreOffice

    :param host:  define host in the UNO connect-string --accept
    :param port:   define port in the UNO connect-string --accept
    :param nb_env: number of process to launch
    :return: list of (host,port,lo dir) 
    """
    if nb_env <= 0:
       raise TypeError("%s is an invalid positive int value" % value)
    soffices=[]
    port=start_port
    for i in range(1,nb_env+1):
        soffices.append(start_office(host,str(port)))
        port=port+1
    return soffices

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
