import requests
import json

'''
Module to implement helper funktions to keept the code organized and less complex in metstohandle.py

'''

def getDAtaObejctPidsFrom_Versionhandle(pidOfVersion:str,url:str,user:str,password:str):

    pid=pidOfVersion.split('/')[1]
    
    answer=requests.get(url+pid, auth=(user, password))

    data=json.loads(answer.text)


    return json.loads(data[1]['parsed_data'])

