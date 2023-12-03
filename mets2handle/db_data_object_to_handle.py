'''
This module implements the creation of the PID records for the
data object/item.

The Metadata follow the definitions of
Data Object: https://dtr-test.pidconsortium.net/#objects/21.T11148/b0047df54c686b9df82a
'''

__author__ = "Henry Beiker, Sven Bingert"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

from datetime import datetime

def specific_Carrier_type(dmdsec, ns):
    for description in dmdsec.findall('.//ebucore:description', ns):
        if description.get('typeLabel') == 'specificCarrierType':
            carrier = description.find('.//dc:description', ns).text
            return carrier

def perservationAccessStatus(dmdsec, ns):
    for description in dmdsec.findall('.//ebucore:description', ns):
        if description.get('typeLabel') == 'accessStatus':
            status = description.find('.//dc:description', ns).text
            return {'type': 'preservation_access_status', 'parsed_data': status}

def supplementaryInformation(dmdsec, ns):
    for description in dmdsec.findall('.//ebucore:description', ns):
        if description.get('typeLabel') == 'comment':
            information = description.find('.//dc:description', ns).text
            return information
    return 'teststring'

def item_file_size(dmdsec, ns):
    if dmdsec.find('.//ebucore:format//ebucore:fileSize', ns) is not None:
        size = dmdsec.find('.//ebucore:format//ebucore:fileSize', ns).text
        unit = dmdsec.find('.//ebucore:format//ebucore:fileSize', ns).get('unit')
        return str(size) + str(unit)
    else:
        return None

def languages(dmdsec, ns):
    # will change
    language_version = []
    '''for language in dmdsec.findall('.//ebucore:language',ns):
        language_label=language.get('typeLabel')
        lang=language.find('.//dc:language',ns).text
        language_version.append({'language_version':{'language':language,'label':language_label}})'''
    for language in dmdsec.findall('.//ebucore:language', ns):
        language_version.append(language.get('typeLabel'))
    return {'type': 'language_versions', 'parsed_data': language_version}

def getSource(dmdsec, ns):
    """
    Findet den Namen der Organisation, welche das Werk verwaltet
    """
    sources = []
    for source in dmdsec.find('.//ebucore:organisationDetails', ns).findall('.//ebucore:organisationName', ns):
        sources.append({'name': source.text, 'identifier_uri': source.find('..').get('organisationId')})
    source = {'source': sources}
    source =  {'sourceAttribution': {'attributionDate': datetime.now().replace(microsecond=0).isoformat()+'Z','attributionType': 'Created'},'sourceIdentifier': '21:','sourceName': 'SDK' }
    return source

def getLast_modified(dmdsec, ns) -> dict[str,str]:
    """
    21.T11148/cc9350e8525a1ca5ffe4
    Findet das Datum  an dem die Mets DATei zuletzt verändert wurde.
    """
    date = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('dateLastModified').split("Z")
    uhrzeit = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('timeLastModified').split('Z')

    time= date[0] + ' ' + uhrzeit[0]

    return time

def getIdentifier(identifier: str) -> dict[str,str]:
    '''
    21.T11148/fae9fd39301eb7e657d4
    '''
    # identifier= dmdsec.find('.//ebucore:identifiert',ns).find('.//dc:identifier',ns).text
    return '21.123/123'


def build_data_object_json(dmdsec, ns: dict[str, str], dataobjectPid, workpid: str) -> list[dict]:
    values = {}
    values['item_file_size'] = item_file_size(dmdsec, ns)
    values['specific_carrier_type'] = specific_Carrier_type(dmdsec, ns)
    values['supplementary_information'] = supplementaryInformation(dmdsec, ns)
    # Nr 7
    values['is_data_object_of'] = getIdentifier(dataobjectPid)
    # Nr 10
    values['source'] = getSource(dmdsec, ns)
    # Nr 11
    values['last_modified'] = getLast_modified(dmdsec, ns)
    # values.append(languages(dmdsec,ns)) will change soon
    # values.append(perservationAccessStatus(dmdsec,ns)) TODO uncomment as soon as enum list is ready

    return values