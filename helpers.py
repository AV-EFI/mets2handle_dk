import requests
from urllib.request import urlopen
import json
from lxml import etree as ET

import logging
logging.basicConfig(filename='/tmp/myapp.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

vocab_map_file = open('mets2handle/vocab_map.json')
vocab_map = json.load(vocab_map_file)

'''
Module to implement helper funktions to keept the code organized and less complex in metstohandle.py
'''

def getEnumFromType(datatype):
    baseurl = "https://dtr-test.pidconsortium.net/objects/"
    url = baseurl + datatype
    response = urlopen(url)
    typedata = json.loads(response.read())
    return typedata['properties'][0]['enum']

def getDAtaObejctPidsFrom_Versionhandle(pidOfVersion:str,url:str,user:str,password:str):

    pid=pidOfVersion.split('/')[1]
    
    answer=requests.get(url+pid, auth=(user, password))

    data=json.loads(answer.text)


    return json.loads(data[1]['parsed_data'])


def buildisVersiontOfVersionXML(pidWerk:str):

    root = ET.Element("{urn:ebu:metadata-schema:ebucore}isVersionOf")

    root.tail='     \n  '
    
    # Create the relationIdentifier element
    relation_identifier = ET.SubElement(root, "{urn:ebu:metadata-schema:ebucore}relationIdentifier", formatLabel="hdl.handle.net")

    # Create the dc:identifier element
    dc_identifier = ET.SubElement(relation_identifier, "{http://purl.org/dc/elements/1.1/}identifier")
    dc_identifier.text = pidWerk

    return root

def buildIsPartOfInXML(pidVersion:str):

    root = ET.Element("{urn:ebu:metadata-schema:ebucore}isPartOf")

    root.tail='     \n  '
    
    # Create the relationIdentifier element
    relation_identifier = ET.SubElement(root, "{urn:ebu:metadata-schema:ebucore}relationIdentifier", formatLabel="hdl.handle.net")

    # Create the dc:identifier element
    dc_identifier = ET.SubElement(relation_identifier, "{http://purl.org/dc/elements/1.1/}identifier")
    dc_identifier.text = pidVersion

    return root

def buildHasPartInXML(pidDataobject:str):
    
    root = ET.Element("{urn:ebu:metadata-schema:ebucore}hasPart")

    root.tail='     \n  '
    
    # Create the relationIdentifier element
    relation_identifier = ET.SubElement(root, "{urn:ebu:metadata-schema:ebucore}relationIdentifier", formatLabel="hdl.handle.net")

    # Create the dc:identifier element
    dc_identifier = ET.SubElement(relation_identifier, "{http://purl.org/dc/elements/1.1/}identifier")
    dc_identifier.text = pidDataobject

    return root
    

