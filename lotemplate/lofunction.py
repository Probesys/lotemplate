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
from .WriterTemplate import WriterTemplate
from .CalcTemplate import CalcTemplate 
from .connexion import Connexion,start_office 
import random
from datetime import datetime

def TemplateFromExt(file_path: str, cnx, should_scan: bool,json_cache_dir=None):

        filename, file_extension = os.path.splitext(file_path)
        ods_ext=('.xls','.xlsx','.ods')
        if file_extension in ods_ext:
             document = CalcTemplate(file_path, cnx , should_scan,json_cache_dir)
        else:
             document = WriterTemplate(file_path, cnx , should_scan,json_cache_dir)
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
       raise TypeError("%s is an invalid positive int value" % nb_env)
    soffices=[]
    port=start_port
    for i in range(nb_env):
        soffices.append(start_office(host,str(port)))
        port=port+1
    return soffices

def clean_old_open_document(lstOffice, max_time):
    """
    clean open document open for too long and where a sure are not use anymore
    :lstOffice list of host,port
    :max_time:  Maximum time in second afeter wich were consider the document
    not use anymore
    :checkfile:   add a check to see if the file still exist if not just close
    the doc.
    """
    counter=0
    for host,port,lodir  in lstOffice:
        cnx=Connexion(host,port)
        for doc  in list(cnx.desktop.getComponents()):
            #print("number of opendocument"+str(len(list(cnx.desktop.getComponents()))))
            #print(doc)
            url=doc.getURL()
            file=url[7:]
            try:
                delta=(datetime.now() -
                       datetime.fromtimestamp(os.path.getmtime(file))).seconds
                if delta > int(max_time):
                    counter += 1
                    doc.close(True)
                    os.remove(file)
            except FileNotFoundError:
                counter += 1
                doc.close(True) 
    return({"nb_clean":counter})

def statistic_open_document(lstOffice, max_time,):
    mylist=[]
    for host,port,lodir  in lstOffice:
        cnx=Connexion(host,port)
        baddoc={"tooold":[],"missing":[]}
        cnxdict={"maxtime":max_time,"hosts":host,"port":port,}
        for doc  in list(cnx.desktop.getComponents()):
            #print(doc)
            url=doc.getURL()
            file=url[7:]
            try:
                delta=(datetime.now() -
                       datetime.fromtimestamp(os.path.getmtime(file))).seconds
                if delta > int(max_time):
                    baddoc["tooold"].append(file)
            except FileNotFoundError:
                    baddoc["missing"].append(file)
            cnxdict["baddoc"]=baddoc
        mylist.append(cnxdict)
    return mylist

