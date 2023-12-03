"""""
This module implements the creation of the PID records for the manifestion/version.

It is designed to map the values from the METS XML files to the required values.
For that each function is a mapping which searches for the value in a section
of the METS file and puts it in a dictionary which has the format of:
{
    type:<value that is defined in the handle>,
    parsed_data:<object or value defined in the handle>
}

The function buildVersionJson is there to call all the defined functions and
put them into a format, so that the JSON library can convert the dictionary into
a JSON file that is accepted by the PID system. It is possible to deselect values
that one does not want in the json and therefore will not be sent to the
PID system.

The Metadata follow the definitions of
Manifestation: https://dtr-test.pidconsortium.net/#objects/21.T11148/ef6836b80e4d64e574e3

"""
__author__ = "Henry Beiker, Sven Bingert"
__maintainer__ = "Sven Bingert"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

from mets2handle import helpers

ns = {"mets": "http://www.loc.gov/METS/", "xlink": "http://www.w3.org/1999/xlink",
      "xsi": "http://www.w3.org/2001/XMLSchema-instance", "ebucore": "urn:ebu:metadata-schema:ebucore",
      "dc": "http://purl.org/dc/elements/1.1/"}


def get_identifier_version(workPid: str):
    """
    21.T11148/fae9fd39301eb7e657d4
    """
    # work_pid='21.T11148/{}'.format(str(uuid.uuid4()))
    # identifier= dmdsec.find('.//ebucore:identifiert',ns).find('.//dc:identifier',ns).text
    return {'type': 'identifier', 'parsed_data': workPid.upper()}


def get_is_version_of(pids_of_works):
    """
    21.T11148/ef19de26cec8cae78ceb
    Mandatory,repeatable
    enthält die PID(s) vom Werk
    """
    return pids_of_works


def get_has_data_object(dataobjectpid: list):
    # geht davon aus, dass es nur ein dataobject pro mets gibt!
    for dataobject in dataobjectpid:
        dataobject = dataobject.upper()
    #
    if not isinstance(dataobjectpid, list):
        dataobjectpid = [dataobjectpid]
    return dataobjectpid


def get_same_as(dmdsec, ns):
    objects = ['21.T11148/ef19de26cec8cae78ceb']
    # platzhalter pid auf same_as Registry -> aktuell nicht im mets zu finden
    return objects


def get_titles(dmdsec, ns):
    # Allowed titles are at the moment equal to the titles used in "work"
    # Thus it is the same function as in db_works_to_handle
    titlelist = []
    titletypes = helpers.getEnumFromType('21.T11148/2f4e516fbdfa40a52453')

    for title in dmdsec.findall(".//dc:title", ns):
        titlestring = str(title.find('..').get('typeLabel'))
        try:
            titlelist.append({'titleValue': title.text, 'titleType': helpers.vocab_map[titlestring]})
        except KeyError:
            helpers.logger.error('WORK: Titel Type "' + titlestring + '" not in vocab_map.json')
        # If already mapped:
        if titlestring in titletypes:
            titlelist.append({'titleValue': title.text, 'titleType': titlestring})
    return titlelist


def get_release_date(dmdsec, ns):
    # Release data has to be given in YYYY-MM-DD
    try:
        releasedate = dmdsec.find('.//ebucore:date//ebucore:released', ns).get('year')
    except AttributeError:
        helpers.logger.error('VERSION: No release date found')
        releasedate = '1000'
    # if only year is given, we apped -01-01
    if len(releasedate) == 4:
        releasedate = releasedate + '-01-01'
    return releasedate


def get_years_of_reference(dmdsec, ns):
    """
    Findet den Erstellsungszeitraum hier benannt year of reference
    21.T11148/089d6db63cf69c35930d
    """
    # years = [{'year_of_reference': dmdsec.find(".//ebucore:date", ns).find(".//ebucore:created", ns).get("startYear")},
    #         {'year_of_reference': dmdsec.find(".//ebucore:date", ns).find(".//ebucore:created", ns).get("endYear")}]
    if dmdsec.find('.//ebucore:date//ebucore:created', ns) != None:
        year = dmdsec.find('.//ebucore:date//ebucore:created', ns).get('startYear')
        return {'type': 'production_year', 'parsed_data': year}
    else:
        helpers.logger.error('VERSION: yearOfReference not found')
        return None


def get_manifestation_type(dmdsec, ns):
    # Implements: 21.T11148/c72633267da87f952971
    typelist = []
    manifestationTypes = helpers.getEnumFromType('21.T11148/567d070dfa708072819b')
    #
    for type in dmdsec.findall('.//ebucore:type//ebucore:objectType', ns):
        typestring = type.get('typeLabel')
        if typestring in manifestationTypes:
            typelist.append(typestring)
        else:
            helpers.logger.error('VERSION: manifestationType "' + typestring + '" not in the list')
            typelist.append('Unknown')
    return typelist


def get_has_agent(dmdsec, ns):
    # Implements: 21.T11148/5a69721cca16545c03e6
    data = []
    for companie in dmdsec.findall('.//ebucore_contributor', ns):
        data.append({'name': companie.find('.//ebucore:organisationDetails//ebucore:organisationName', ns).text,
                     'identifier_uri': companie.find('.//ebucore:organisationDetails', ns).get('organisationID')})
    return data


def get_sources(dmdsec, ns):
    # Implements: 21.T11148/828d338a9b04221c9cbe
    dmdsec.find('.//ebucore:metadataProvider//ebucore:organisationDetails//ebucore:organisationName', ns)
    source = {
        'sourceName': dmdsec.find('.//ebucore:metadataProvider//ebucore:organisationDetails//ebucore:organisationName',
                                  ns).text, }

    # 'identifier_uri': dmdsec.find('.//ebucore:metadataProvider//ebucore:organisationDetails',ns).get('organisationId')
    return source


def get_last_modified(dmdsec, ns):
    # Implements: 21.T11148/a27923f25913583b1ea6
    """
    Findet das Datum  an dem die Mets Datei zuletzt verändert wurde.
    TODO: Klären ob hier nicht die letzte Änderung der PID eingetragen werden muss.
    """
    date = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('dateLastModified').split("Z")
    uhrzeit = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('timeLastModified').split('Z')

    time = date[0] + ' ' + uhrzeit[0]
    return time


def build_version_json(dmdsec, ns, pid_works, dataobject_pid: list, version_pid, lastModified=True, Sources=True,
                       HasAgent=True, ManfiestationType=True, YearsofReference=True, releasedate=True, sameas=True,
                       title=False, DataObject=True, VerisonOf=True, identifier=True):
    json = dict()
    values = {}
    # if identifier:
    # values.append(getIdentifier(version_pid))

    if VerisonOf:
        values['is_version_of'] = pid_works
    if sameas:
        values['same_as'] = get_same_as(dmdsec, ns)
    if DataObject:
        values['has_data_objects'] = get_has_data_object(dataobject_pid)
    if title:
        values['title'] = get_titles(dmdsec, ns)
    if releasedate:
        values['release_date'] = get_release_date(dmdsec, ns)
    #  FixMe   if YearsofReference:
    #  FixMe      values['production_year'] = getYearsOfReference(dmdsec, ns)
    if ManfiestationType:
        values['manifestation_types'] = get_manifestation_type(dmdsec, ns)
    if HasAgent:
        values['has_agent'] = get_has_agent(dmdsec, ns)
    if Sources:
        values['source'] = get_sources(dmdsec, ns)
    if lastModified:
        values['last_modified'] = get_last_modified(dmdsec, ns)

    return values
