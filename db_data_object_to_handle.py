'''
This module implements the creation of the PID records for the
data object/item-KernelInformationProfile.
'''

__author__ = "Henry Beiker"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

from lxml import etree as ET
import uuid

def specific_Carrier_type(dmdsec,ns):

    for description in dmdsec.findall('.//ebucore:description',ns):
        if description.get('typeLabel')=='specificCarrierType':
            carrier=description.find('.//dc:description',ns).text

def perservationAccessStatus(dmdsec,ns):
    for description in dmdsec.findall('.//ebucore:description',ns):
        if description.get('typeLabel')=='accessStatus':
            carrier=description.find('.//dc:description',ns).text

def sumplementaryInformation(dmdsec,ns):
    for description in dmdsec.findall('.//ebucore:description',ns):
        if description.get('typeLabel')=='comment':
           information=description.find('.//dc:description',ns).text

def item_file_size(dmdsec,ns):
    if dmdsec.find('.//ebucore:format//ebucore:fileSize',ns) != None:
        size =dmdsec.find('.//ebucore:format//ebucore:fileSize',ns).text
        unit= dmdsec.find('.//ebucore:format//ebucore:fileSize',ns).get('unit')
        return {'type':'item_file_size','parsed_data':str(size)+str(unit)}
    else:
        return None

def languages(dmdsec,ns):
    #will change
    language_version=[]
    '''for language in dmdsec.findall('.//ebucore:language',ns):
        language_label=language.get('typeLabel')
        lang=language.find('.//dc:language',ns).text
        language_version.append({'language_version':{'language':language,'label':language_label}})'''
    for language in dmdsec.findall('.//ebucore:language',ns):
        language_version.append(language.get('typeLabel'))
    return {'type':'language_versions','parsed_data':language_version}

def getLast_modified(dmdsec,ns):
    """
    21.T11148/cc9350e8525a1ca5ffe4
    Findet das Datum  an dem die Mets DATei zuletzt verändert wurde.
    """
    date = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('dateLastModified').split("+")
    uhrzeit = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('timeLastModified').split('+')
    if len(uhrzeit[1])==4:
        uhrzeit[1]='0'+uhrzeit[1]
    split=date[0].split('-')
    if len(split[2])==1:
        split[2]='0'+split[2]
        time = split[0]+'-'+split[1]+'-'+split[2]+' '+uhrzeit[0]+'+'+uhrzeit[1]
    else:
        time = split[0]+'-'+split[1]+'-'+split[2]+' '+uhrzeit[0]+'+'+uhrzeit[1]

    return {'type': 'last_modified', 'parsed_data': time}

def getIdentifier(identifier:str):
    '''
    21.T11148/fae9fd39301eb7e657d4
    '''
    work_pid='21.T11148/{}'.format(str(uuid.uuid4()))
    #identifier= dmdsec.find('.//ebucore:identifiert',ns).find('.//dc:identifier',ns).text
    return {'type':'identifier','parsed_data':{'identifier':identifier.upper()}}

def buildData_Object_Json(dmdsec,ns,dataobjectPid,workpid):
    json=dict()
    valuedict=dict()
    values=[]
    #values.append(getIdentifier(dataobjectPid))

    values.append({'type':'is_data_object_of','parsed_data':workpid})

    values.append(getLast_modified(dmdsec,ns))

    values.append({'type':'source','parsed_data':{'name':'no metadata provider in mets'}})

   # values.append(languages(dmdsec,ns)) will change soon

    values.append(item_file_size(dmdsec,ns))

    values.append(sumplementaryInformation(dmdsec,ns))

    values.append(perservationAccessStatus(dmdsec,ns))

    values.append(specific_Carrier_type(dmdsec,ns))

    values.append({'type':'KernelInformationProfile','parsed_data':'21.T11148/b0047df54c686b9df82a'}) #version 0.1

    json=  [value for value in values if value is not None]
    return json
