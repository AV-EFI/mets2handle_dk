'''
This module implements the mapping from the relevant values in the METS xml to 
a JSON file that contains the data for an Work Object which represents a 
cinematographic work. The functions basicly map from the METS xml values to  
standardized values by putting the values from the XML files into dictionarys 
that can later be transformed into a JSON file that can be sent to the PID 
service.

The function "buildWorkJson" calls all the functions and puts them into the 
right order to appear in the JSON file. It is possible to deselect values that 
should not appear in the JSON and therefore will not be sent to the PID service.

The function "create_identifier_element" creates and xml element that contains 
the information about the PID and which can later be inserted into the original 
METS file.

The Metadata follow the definitions of
Work: https://dtr-test.pidconsortium.net/#objects/21.T11148/31b848e871121c47d064
'''
__author__ = "Henry Beiker, Sven Bingert"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

from typing import Union

from lxml import etree as ET
from lxml.etree import Element

from mets2handle import helpers
import pycountry

from datetime import datetime


def get_identifier(pid_work: str) -> dict[str]:
    """
    DTR: 21.T11148/fae9fd39301eb7e657d4
    """
    handleID = [{'identifier': pid_work.upper()}]
    return {'identifiers': handleID}


def get_title(dmdsec: ET, ns):
    """
    Find the Title of the work
    DTR: 21.T11148/4b18b74f5ed1441bc6a3
    """
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


def get_series_name(dmdsec, ns):
    """
    Use series name if given, otherwise set to none.
    Wenn das Werk einen Seriennamen besitzt, dann wird diser hiermit gefunden.
    Existiert kein Serienname ist der Eintrag None
    """
    # TODO: Es gibt noch ungereimtheiten bei den wertelisten sowie mit den identifiern
    name = ""
    for title in dmdsec.findall('.//ebucore:alternativeTitle', ns):
        if title.get('typeLabel') == 'series':
            name = title.find('.//dc:title', ns).text
    return name


def get_source(dmdsec, ns):
    """
    Findet den Namen der Organisation, welche das Werk verwaltet
    """
    sources = []
    for source in dmdsec.find('.//ebucore:organisationDetails', ns).findall('.//ebucore:organisationName', ns):
        sources.append({'name': source.text, 'identifier_uri': source.find('..').get('organisationId')})
    source = {'source': sources}
    source = [{'sourceAttribution': {'attributionDate': datetime.now().replace(microsecond=0).isoformat() + 'Z',
                                     'attributionType': 'Created'}, 'sourceIdentifier': '21:', 'sourceName': 'SDK'}]
    return source


def get_credits(dmdsec, ns):
    """
    Findet den Regisseur
    """
    creditsRole = helpers.getEnumFromType('21.T11148/8dca46428d005a2f4c2e')

    credits_list = []
    for contributor in dmdsec.findall('.//ebucore:contributor', ns):
        for role in contributor.findall('.//ebucore:role', ns):
            if role.get('typeLabel').lower() in [creditoption.lower() for creditoption in creditsRole]:
                name = contributor.find('./ebucore:contactDetails', ns).find('./ebucore:name', ns).text.split(',')

                if contributor.find('.//ebucore:contactDetails', ns).get(
                        'contactId') is not None:  # checktob es eine uri gibt
                    credits_list.append({
                        'identifier': {
                            'identifier': contributor.find('.//ebucore:contactDetails', ns).get('contactId').split('/')[
                                -1],
                            'identifier_uri': contributor.find('.//ebucore:contactDetails', ns).get('contactId')},
                        'name': {'family-name': name[0],
                                 'given-name': name[1].strip()},
                        'role': str(role.get('typeLabel')).capitalize()
                    })
                else:
                    credits_list.append({
                        'name': {'family-name': name[0],
                                 'given-name': name[1].strip()},
                        'role': role.get('typeLabel').capitalize()
                    })

    return credits_list


def get_cast(dmdsec, ns):
    """
    Findet alle personen , welche vor der Kamera standen -> cast
    """
    cast = []
    for contributor in dmdsec.findall('.//ebucore:contributor', ns):

        if contributor.find('.//ebucore:role', ns).get('typeLabel') == 'cast':
            name = contributor.find('./ebucore:contactDetails', ns).find('./ebucore:name', ns).text.split(',')
            if contributor.find('.//ebucore:contactDetails', ns).get('contactId') is not None:

                cast.append(
                    {'name': {'family-name': name[0], 'given-name': name[1].strip()},
                     'identifier_uri': contributor.find('.//ebucore:contactDetails', ns).get('contactId')
                     })
            else:
                cast.append({'name': {'family-name': name[0], 'given-name': name[1].strip()}, })
    if len(cast) == 0:
        return None
    return cast


def get_original_duration(dmdsec: Element, ns: dict) -> Union[dict, None]:
    """
    Findet die Länge des Werkes
    21.T11148/b8a2e906c01f78a0d37b
    """
    duration = dmdsec.find('.//ebucore:duration', ns)
    if duration is not None and duration.get('typeLabel') == 'originalDuration':
        time = duration.find('.//ebucore:normalPlayTime', ns).text
        return {'original_duration': time}

    return ""


def get_source_identifier(dmdsec, ns):
    """
    21.T11148/4f79cf79777ae7c379fe
    Findet die identifier id/url der Hauptorganisation die dieses Werk verwaltet
    """
    return dmdsec.find('.//ebucore:organisationDetails', ns).get('organisationId')


def get_last_modified(dmdsec, ns):
    """
    21.T11148/cc9350e8525a1ca5ffe4
    Findet das Datum  an dem die Mets DATei zuletzt verändert wurde.
    """
    date = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('dateLastModified').split("Z")
    uhrzeit = dmdsec.find('.//ebucore:ebuCoreMain', ns).get('timeLastModified').split('Z')

    time = date[0] + ' ' + uhrzeit[0]

    return time


def get_production_companies(dmdsec, ns):
    """
    Findet die am Werk beteiligten Produktionsfirmen
    21.T11148/cc9350e8525a1ca5ffe4
    """
    companies = []
    # for companie in companies add {name + uri} to companies
    company = ' '
    # platzhalter companielist nicht zu finden in xml

    # if len(companies) == 0:
    #    return None

    return [{'identifier_uri': 'http://gwdg.de', 'name': 'TESTNAME'}]


def get_original_language(dmdsec, ns):
    """
    Findet die Sprache, in der das Werk erstmalig aufgenommen worden ist
    21.T11148/577d96232ee6ea2f8dfa
    """
    original_languages = []

    for lan in dmdsec.findall('.//ebucore:language', ns):
        original_languages.append(lan.find('.//dc:language', ns).text)
    if not len(original_languages):
        return None
    # platzhalter nicht klar im xml
    return original_languages


def get_countries_of_reference(dmdsec, ns):
    """
    Findet Ursprungsland
    """
    landlist = []
    for country in dmdsec.findall('.//ebucore:location', ns):
        landstring = str(country.find('.//ebucore:name', ns).text)
        # Try to find country name in the database
        if pycountry.countries.get(name=landstring) is not None:
            landlist.append(pycountry.countries.get(name=landstring).aplha_2)
        elif pycountry.countries.get(official_name=landstring) is not None:
            landlist.append(pycountry.countries.get(official_name=landstring).aplha_2)
        elif pycountry.historic_countries.get(name=landstring) is not None:
            landlist.append(pycountry.historic_countries.get(name=landstring).aplha_2)
        else:
            # As everything failed use fuzzy search and log the information
            check_historic = True
            try:
                res = pycountry.countries.search_fuzzy(landstring)
            except LookupError:
                helpers.logger.error('WORK: countryOfReference "' + landstring + '" not found by pycountry')
            else:
                country_hits = [x for x in res if x is not None]
                helpers.logger.error('WORK: countryOfReference "' + landstring + '" found as "'
                                     + country_hits[0].alpha_2 + '" but might not be correct')

                landlist.append(country_hits[0].alpha_2)
                check_historic = False
            if check_historic:
                try:
                    res = pycountry.historic_countries.search_fuzzy(landstring)
                except LookupError:
                    helpers.logger.error(
                        'WORK: countryOfReference "' + landstring + '" not found by pycountry historic')
                else:
                    country_hits = [x for x in res if x is not None]
                    helpers.logger.error('WORK: countryOfReference "' + landstring + '" found as "'
                                         + country_hits[0].alpha_2 + '" but might not be correct')
                    landlist.append(country_hits[0].alpha_2)

    return landlist


def get_years_of_reference(dmdsec, ns):  # wird eventuell noch abgeändert
    """
    Findet den Erstellsungszeitraum hier benannt year of reference
    21.T11148/089d6db63cf69c35930d
    ISSUES: referenceType nicht gegeben aber immer created ?
    """
    yearOfReferenceTypes = helpers.getEnumFromType('21.T11148/03dfc92c55cea3e18920')
    start_year = dmdsec.find(".//ebucore:date", ns).find(".//ebucore:created", ns).get("startYear")
    end_year = dmdsec.find(".//ebucore:date", ns).find(".//ebucore:created", ns).get("endYear")
    years = [{'yearOfReferenceStart': start_year,
              'yearOfReferenceEnd': end_year,
              'yearOfReferenceType': 'Created'}]
    return years


def get_related_identifier(dmdsec, ns):  # was bedeute das comment?
    """
    Findet andere Identifier wie ISAN oder EIDR
    Bisher nicht im xml zu finden

    21.T11148/d72482f16d18ff46f8f4
    """
    # identifiertlist = []
    # for identifier in dmdsec.findall('.//ebucore:identifier',ns):
    # identifiertlist.append( {'relatedIdentifierValue': identifier.find('.//dc:identifier',ns).text , 'relatedIdentifiertType':identifier.get('formatLabel')}) #immer other? oder doch format label?)
    return {'relatedIdentifierValue': ' ', 'relatedIdentifierType': ' '}


def get_genre(dmdsec, ns):
    """
    Findet das Genre eines Filmes
    """
    genrelist = []
    genres = helpers.getEnumFromType('21.T11148/9100b6b9d1719c5f6c82')
    #
    for genre in dmdsec.findall('.//ebucore:genre', ns):
        genrestring = str(genre.get('typeLabel'))
        try:
            genrelist.append(helpers.vocab_map[genrestring])
        except KeyError:
            helpers.logger.error('WORK: Genre "' + genrestring + '" not in vocab_map.json')
        if genrestring in genres:
            genrelist.append(genrestring)
    return genrelist


def get_original_format(dmdsec, ns):
    """
    Gibt das Format zurück, auf welchem der Film gespeichert wurde
    """
    try:
        format_sec = dmdsec.xpath(
            './/ebucore:format[@typeLabel="originalFormat"]',
            namespaces=ns)[0]
    except IndexError:
        return None
    parsed_data = {}
    for prefix in ('video', 'audio'):
        for suffix in ('Format', 'Type'):
            try:
                val = format_sec.xpath(
                    f'ebucore:{prefix}Format/ebucore:technicalAttributeString'
                    f'[@typeLabel="material{suffix}"]',
                    namespaces=ns)[0].text
            except IndexError:
                continue
            if val:
                parsed_data[f"{prefix}Material{suffix}"] = val
    if not parsed_data:
        return None
    return parsed_data


# build json gibt ein dict zurück, welches von der json bibliothek in die fertige json datei ausgegeben werden kann.
def build_work_json(dmdsec: Element, ns: dict[str, str], pid_work, handleId=True, title=True, series=False,
                    credit=False,
                    cast=True,
                    original_duration=True, source=True, source_identifier=False, last_modifed=True,
                    production_companies=True,
                    countries_of_reference=True, original_language=False, years_of_reference=True,
                    related_identifier=True, original_format=True, genre=True):
    """
    Erhält als Eingabe ein Xml Element
    Gibt ein Dict zurück, welches die Struktur für eine Json Datei beinhaltet, wie sie das Handle System erwartet.
    Die Struktur kann verändert werden, indem die if-Bedingungen in der Funktion selbstr vertauscht werden.
    Es können Blöcke weggelassen werden, wenn beim Funktionsaufruf der jeweilige Block mit =False belegt wird.
    Standardmäßig werden alle Blöcke ausgegeben
    TODO set originallanguage to true when regex is fixed
    """
    values = {}

    # if handleId:
    #  values.append(getIdentifier (pid_work))

    if title:
        values['title'] = get_title(dmdsec, ns)
    if series:
        values['series'] = get_series_name(dmdsec, ns)
    if credit:
        values['credits'] = get_credits(dmdsec, ns)
    if cast:
        values['cast'] = get_cast(dmdsec, ns)
    if original_duration:
        values['originalDuration'] = get_original_duration(dmdsec, ns)
    if source:
        values['source'] = get_source(dmdsec, ns)
    if source_identifier:
        values['sourceIdentifier'] = get_source_identifier(dmdsec, ns)
    if last_modifed:
        values['lastModified'] = get_last_modified(dmdsec, ns)
    if production_companies:
        values['productionCompany'] = get_production_companies(dmdsec, ns)
    if countries_of_reference:
        values['countryOfReference'] = get_countries_of_reference(dmdsec, ns)
    if original_language:
        values['originalLanguage'] = get_original_language(dmdsec, ns)
    if years_of_reference:
        values['yearOfReference'] = get_years_of_reference(dmdsec, ns)
    if related_identifier:
        values['relatedIdentifier'] = get_related_identifier(dmdsec, ns)
    if original_format:
        values['originalFormat'] = get_original_format(dmdsec, ns)
    if genre:
        values['genre'] = get_genre(dmdsec, ns)
    return values


def create_identifier_element(pid: str):
    ebu_identifier = ET.Element('{urn:ebu:metadata-schema:ebucore}identifier', )
    ebu_identifier.attrib['formatLabel'] = 'hdl.handle.net'
    ebu_identifier.tail = '\n          '

    dc_identifier = ET.SubElement(ebu_identifier, '{http://purl.org/dc/elements/1.1/}identifier')
    dc_identifier.text = '\n                    ' + pid + '\n              '
    dc_identifier.tail = '         \n            '
    return ebu_identifier
