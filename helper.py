import requests
import json
from lxml import etree as ET

'''
Module to implement helper funktions to keept the code organized and less complex in metstohandle.py

'''

def getDAtaObejctPidsFrom_Versionhandle(pidOfVersion:str,url:str,user:str,password:str):

    pid=pidOfVersion.split('/')[1]
    
    answer=requests.get(url+pid, auth=(user, password))

    data=json.loads(answer.text)


    return json.loads(data[1]['parsed_data'])


def buildisVersiontOfVersionXML(pidWerk:str):

    root = ET.Element("{urn:ebu:metadata-schema:ebucore}isVersionOf")
    
    # Create the relationIdentifier element
    relation_identifier = ET.SubElement(root, "{urn:ebu:metadata-schema:ebucore}relationIdentifier", formatLabel="hdl.handle.net")

    # Create the dc:identifier element
    dc_identifier = ET.SubElement(relation_identifier, "{http://purl.org/dc/elements/1.1/}identifier")
    dc_identifier.text = pidWerk
    

    

    return root