from API import utils
import os

workers=int(os.environ.get('NB_WORKERS', 4))
maxtime=int(os.environ.get('MAXTIME', 60))
my_lo=[]
scannedjson='uploads/scannnedjson'
def on_starting(server):
 
    utils.start_soffice(workers,scannedjson,maxtime)
