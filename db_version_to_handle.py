'''
This module implements the creation of the PID records for the
manifestion/version-KernelInformationProfile.

It is designed to map the values from the METS XML files to the values in the Handle System.
For that each function is a mapping which searches for the value in a section of the METS file and puts it in a Dictionary which has the format of
{type:<value that is defined in the handle>,parsed_data:<object or value defined in the handle>}

The function buildVersionJson is there to call all the defined functions and put them into a format, so that the json library can covert the dictionary into a json file that is accepted by the handle server
it is possible to deselect values that one does not want in the json and therefore not sent to the handle server
'''
__author__ = "Henry Beiker"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

import xml.etree.ElementTree as ET
import sys
import requests
import uuid

ns = {"mets":"http://www.loc.gov/METS/", "xlink":"http://www.w3.org/1999/xlink","xsi":"http://www.w3.org/2001/XMLSchema-instance","ebucore":"urn:ebu:metadata-schema:ebucore", "dc":"http://purl.org/dc/elements/1.1/"}

def getIdentifier(workPid:str):
    '''
    21.T11148/fae9fd39301eb7e657d4
    '''
    #work_pid='21.T11148/{}'.format(str(uuid.uuid4()))
    #identifier= dmdsec.find('.//ebucore:identifiert',ns).find('.//dc:identifier',ns).text
    return {'type':'identifier','parsed_data':workPid.upper()}

def isVersionof(pids_of_works):
    '''
    21.T11148/ef19de26cec8cae78ceb
    Mandatory,repeatable
    enthält die PID(s) vom Werk
    '''
    versions=pids_of_works
    return {'type':'is_version_of','parsed_data':versions}

def hasDataObject(dataobjectpid:str):
    #geht davon aus, dass es nur ein dataobject pro mets gibt!
    objects=[dataobjectpid.upper()]
    return {'type':'has_data_objects','parsed_data':objects}

def sameAs(dmdsec,ns):
    objects=['21.T11148/ef19de26cec8cae78ceb']#platzhalter pid auf same_as Registry -> aktuell nicht im mets zu finden
    return {'type':'same_as','parsed_data':objects}

def titles(dmdsec,ns):
    titles=[]
    titletypen = ['Original Title', 'Release Title', 'Archive Title', 'Alternative Title', 'Sort Title']
    for title in dmdsec.findall(".//dc:title", ns):
        if title.find('..').get('typeLabel') not in titletypen :

            titletype='Other'
        else:
            titletype=title.find('..').get('typeLabel')
        titles.append({'titleValue':title.text, 'titleType':titletype})
    title = {'type': 'titles',#21.T11148/4b18b74f5ed1441bc6a3
             'parsed_data':
             titles}
    return title

def releaseDate(dmdsec,ns):#
    releasedate=dmdsec.find('.//ebucore:date//ebucore:released',ns).get('year')
    return({'type':'release_date','parsed_data':releasedate})

def getYears_of_reference(dmdsec,ns):#wird eventuell noch abgeändert
    """
    Findet den Erstellsungszeitraum hier Benannt year of reference
    21.T11148/089d6db63cf69c35930d
    """
    #years = [{'year_of_reference': dmdsec.find(
    #    ".//ebucore:date", ns).find(".//ebucore:created", ns).get("startYear")}, {'year_of_reference': dmdsec.find(".//ebucore:date", ns).find(".//ebucore:created", ns).get("endYear")}]
    if dmdsec.find('.//ebucore:date//ebucore:created',ns) != None:
        year=dmdsec.find('.//ebucore:date//ebucore:created',ns).get('startYear')
        return {'type': 'production_year','parsed_data':year}
    else:
        return None

def getManifestationType(dmdsec,ns):
    types=[]
    for type in dmdsec.findall('.//ebucore:type//ebucore:objectType',ns):
        type_=type.get('typeLabel')
        if type_ in ['Broadcast', 'Home viewing publication', 'Internet', 'Theatrical distribution', 'Unreleased', 'Non-theatrical distribution', 'Not for release', 'Pre-Release', 'Preservation/Restoration', 'Unknown']:
            types.append(type_)
        else:
            types.append('Unknown')
    return {'type':'manifestation_types','parsed_data':types}

def getHasAgent(dmdsec,ns):
    data=[]
    for companie in dmdsec.findall('.//ebucore_contributor',ns):
        data.append({'name':companie.find('.//ebucore:organisationDetails//ebucore:organisationName',ns).text,'identifier_uri':companie.find('.//ebucore:organisationDetails',ns).get('organisationID')})
    return {'type':'has_agent','parsed_data':data}

def getSources(dmdsec,ns):
    dmdsec.find('.//ebucore:metadataProvider//ebucore:organisationDetails//ebucore:organisationName',ns)
    source = {'type': 'source',#21.T11148/b33655d6fe2e0e7244de
               'parsed_data':{'name':dmdsec.find('.//ebucore:metadataProvider//ebucore:organisationDetails//ebucore:organisationName',ns).text,'identifier_uri':dmdsec.find('.//ebucore:metadataProvider//ebucore:organisationDetails',ns).get('organisationId')}}
    return source

def getLast_modified(dmdsec,ns):
    """
    21.T11148/cc9350e8525a1ca5ffe4
    Findet das Datum  an dem die Mets Datei zuletzt verändert wurde.
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

def buildVersionJson(dmdsec,ns , pid_works ,dataobject_pid, version_pid,lastModified=True,Sources=True,HasAgent=True,ManfiestationType=True,YearsofReference=True,releasedate=False,sameas=True,title=False, DataObject=True,VerisonOf=True,identifier=True):
    json=dict()
    valuedict=dict()
    values=[]
    #if identifier:
       # values.append(getIdentifier(version_pid))

    if VerisonOf:
        values.append(isVersionof(pid_works))

    if DataObject:
        values.append(hasDataObject(dataobject_pid))

    if title:
        values.append(titles(dmdsec,ns))

    if sameas:
        values.append(sameAs(dmdsec,ns))

    if releasedate:
        values.append(releaseDate(dmdsec,ns))

    if YearsofReference:
        values.append(getYears_of_reference(dmdsec,ns))

    if ManfiestationType:
        values.append(getManifestationType(dmdsec,ns))

    if HasAgent:
        values.append(getHasAgent(dmdsec,ns))

    if Sources:
        values.append(getSources(dmdsec,ns))

    if lastModified:
        values.append(getLast_modified(dmdsec,ns))

    values.append({'type':'KernelInformationProfile','parsed_data':'21.T11148/ef6836b80e4d64e574e3'}) #version 0.1

    json=  [value for value in values if value is not None]

    return json