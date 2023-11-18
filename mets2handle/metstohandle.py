#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Henry Beiker, Sven Bingert"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

import argparse
import json
import sys
# import db_works_to_handle as xj
# import .db_version_to_handle as vh
# import .db_data_object_to_handle as oh
import uuid
from pathlib import Path
from xml.etree import ElementTree

import requests
from lxml import etree as ET
from mets2handle import helpers
import mets2handle

'''
Vollständige Menschen am Sonntag Handle unter handle id 21.T11998/0412EF68-FC59-4240-9D5D-EEA25F083873

Dies ist ein Python-Code, der ein METS-Dokument (Metadata Encoding and 
Transmission Standard) verarbeitet und bestimmte Teile davon in JSON-Objekte 
umwandelt, die dann an einen Handle-Server gesendet werden. Der Handle-Server 
ist ein System zur Zuweisung von persistenten Identifikatoren (Handles) zu 
digitalen Objekten, um ihre Langzeitarchivierung und -verfügbarkeit zu g
ewährleisten.

Die wichtigsten Bibliotheken, die in diesem Code verwendet werden, sind:
* lxml.etree zum Parsen des METS-Dokuments
* json zum Erstellen von JSON-Objekten
* requests zum Senden von HTTP-Anfragen an den Handle-Server

Einige wichtige Variablen, Funktionen und Abschnitte des Codes sind:
* url: Die URL des Handle-Servers, an den die JSON-Objekte gesendet werden.
* header: Einige HTTP-Header, die in den POST- und PUT-Anfragen verwendet 
    werden, um den Server darüber zu informieren, welche Art von Daten erwartet werden.
* struct: Das structMap-Element im METS-Dokument, das die Struktur des Dokuments beschreibt.
* cineworks und version: Listen von div-Elementen im METS-Dokument, die den 
    Typ "cinematographicWork" bzw. "version" haben. Diese werden später verwendet, um 
    bestimmte Teile des Dokuments zu finden und in JSON-Objekte umzuwandeln.
* xj und vh: Module mit Hilfsfunktionen zum Erstellen von JSON-Objekten aus den METS-Daten.
* uuid.uuid4(): Eine Funktion zum Generieren einer eindeutigen UUID (Universally 
    Unique Identifier), die als Teil der Handle-ID für jeden erstellten cineastischen 
    Work verwendet wird.
* requests.post() und requests.put(): Funktionen zum Senden von HTTP-POST- bzw. 
    PUT-Anfragen an den Handle-Server mit den erstellten JSON-Daten.
* sys.argv[1]: Der Pfad zum METS-Dokument, der als Argument beim Aufruf des Skripts 
    übergeben wird.

Der Code funktioniert wie folgt:
Das METS-Dokument wird mit lxml.etree geparsed und das structMap-Element wird gefunden, 
um die Liste der "cinematographicWork" und "version" DIVs zu erstellen. Für jedes 
"cinematographicWork" DIV wird eine Handle-ID generiert und ein JSON-Objekt mit 
Hilfe des xj-Moduls erstellt. Dieses Objekt wird dann mit requests.post() an den 
Handle-Server gesendet. Wenn die POST-Anfrage erfolgreich ist, wird die neue Handle-ID 
im METS-Dokument eingefügt und das Dokument gespeichert. Für jedes "version" DIV wird 
ein JSON-Objekt mit Hilfe des vh-Moduls erstellt und mit requests.put() an den 
Handle-Server gesendet.

'''


def m2h(filename,
        out_file=None,
        work_pid=None,
        version_pid=None,
        credentials='./mets2handle/credentials/handle_connection.txt',
        dumpjsons=True):
    helpers.logger.info(' --- Start new run ---')
    # dumpjsons=True  set to false if you wish not to have the jsons that are sent to the
    # handle server beeing outputted into this directory

    # Define where to write the new XML
    if out_file is None:
        out_file = filename

    # Read credentials for the ePIC PID service
    connection_details = {}

    print(Path.cwd())
    if True:
        with open(credentials, "r") as f:
            for line in f:
                key, value = line.strip().split("|")
                connection_details[key] = value

    header = {'accept': 'application/json', 'If-None-Match': 'default', 'If-Match': 'default',
              'Content-Type': 'application/json'}

    multiworkno = 0  # counter to enumerate the files that result from the json dump for multiworks

    # Defining namespace dictionary to be used later in the code to access XML data
    ns = {"mets": "http://www.loc.gov/METS/", "xlink": "http://www.w3.org/1999/xlink",
          "xsi": "http://www.w3.org/2001/XMLSchema-instance", "ebucore": "urn:ebu:metadata-schema:ebucore",
          "dc": "http://purl.org/dc/elements/1.1/"}
    parser = ET.XMLParser(remove_comments=False)

    try:
        xml_tree: ElementTree = ET.parse(filename, parser=parser)
    except IndexError:
        raise SystemExit(f"Usage: {sys.argv[0]} <path_to_XML_file>")

    root = xml_tree.getroot()
    struct = xml_tree.find('.//mets:structMap', ns)

    # Create empty lists for the DMDIDs of cinematographic works, versions, and data objects
    cinematographic_works = []
    versions = []
    dataobjects = []
    boolean_list_if_pids_exists = [0, 0, 0]

    # Loop through the structure map of the METS file and find the DMDIDs of cinematographic works, versions, and data objects
    # TODO: Make sure only on valid TYPE is given in the mets file
    for div in struct.findall('.//mets:div', ns):
        element_type = div.get('TYPE')

        if element_type == 'cinematographicWork':
            cinematographic_works.append(div.get('DMDID'))

        if element_type == 'version':
            versions.append(div.get('DMDID'))

        if element_type == 'dataObject':
            dataobjects.append(div.get('DMDID'))
    if len(versions) != 1:
        raise ValueError(
            f"Unexpectedly found {len(versions)} versions in {filename}.")
    if len(dataobjects) != 1:
        raise ValueError(
            f"Unexpectedly found {len(dataobjects)} DataObjects in {filename}.")
    if work_pid and len(cinematographic_works) != 1:
        raise ValueError(
            f"Parameter work_pid not allowed since there are"
            f" {len(cinematographic_works)} works recorded in {filename}.")
    if version_pid and len(versions) != 1:
        raise ValueError(
            f"Parameter version_pid not allowed since there are"
            f" {len(versions)} versions recorded in {filename}.")

    # empty list to hold PIDs of cinematographic works
    cinematographic_work_pids = []

    # generate a new UUID to use as the PID for the data object
    # has to be done here, so we have it already when we get to
    # the Version object where the entry for the PID of a dataobject is needed
    data_object_uuid = str(uuid.uuid4())
    dataobject_Pid = connection_details['prefix'] + '/{}'.format(data_object_uuid)

    for dmdsec in xml_tree.findall('.//mets:dmdSec', ns):

        # If the ID attribute of the dmdSec element is in the list of cinematographic works,
        # generate a new UUID to use as the PID for the work, generate the JSON for the work,
        # write it to a file, and send a PUT request to the handle server to create a new handle for the work
        if dmdsec.get('ID') in cinematographic_works:
            pid = None
            # TODO: hier abfrage, ob Werk bereits Pid hat

            for identifier in dmdsec.findall('.//ebucore:identifier',
                                             ns):  # checks if work has a existing pid. if thats the case we add a 1 to the boolean array
                if identifier.get('formatLabel') == "hdl.handle.net":
                    boolean_list_if_pids_exists[0] = 1
                    cinematographic_work_pids.append(str(identifier.find('.//dc:identifier', ns).text).strip())

            if work_pid:
                if boolean_list_if_pids_exists[0]:
                    if work_pid not in cinematographic_work_pids:
                        raise ValueError(
                            f"Parameter work_pid={work_pid} clashes with"
                            f" existing value in {filename}:"
                            f" {cinematographic_work_pids[-1]}.")
                else:
                    pid = work_pid
            elif not boolean_list_if_pids_exists[0]:
                work_uuid = str(uuid.uuid4())
                cinematographic_work_pid = '21.T11998/{}'.format(str(work_uuid))

                if dumpjsons:
                    json.dump(mets2handle.buildWorkJson(dmdsec, ns, pid_work=cinematographic_work_pid),
                              open(str(multiworkno) + 'handlejson.json', 'w', encoding='utf8'),
                              indent=4, sort_keys=False, ensure_ascii=False)

                payload = mets2handle.buildWorkJson(root, ns, pid_work=cinematographic_work_pid,
                                                    original_duration=False,
                                                    related_identifier=False, original_format=False)
                response_from_handle_server = requests.put(connection_details['url'] + work_uuid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Response to create-Work-request')
                response_from_handle_server.raise_for_status()

                respon = json.loads(response_from_handle_server.text)
                multiworkno = multiworkno + 1
                if True: # Just to keep diff output short
                    # gets pid from response
                    pid = respon['handle']

            if pid:
                if True: # Just to keep diff output short
                    cinematographic_work_pids.append(pid)

                    # writes new PID into the mets file
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '

                    new_tree = ET.tostring(xml_tree, pretty_print=True)
                    with open(out_file, 'wb') as metsfile:

                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')

        # if the ID attribute of the dmdSec element is in the list of versions,
        #  generate a new UUID to use as the PID for the work, generate the JSON for the version,
        # write it to a file, and send a PUT request to the handle server to create a new handle for the version
        if dmdsec.get('ID') in versions:
            pid = existing_pid = None
            # TODO: Hier gegebenenfalls abfrage, ob Versions_pid bereits im METS vorhanden ist
            for identifier in dmdsec.findall('.//ebucore:identifier',
                                             ns):  # checks if work has a existing pid. if thats the case we add a 1 to the boolean array
                if identifier.get('formatLabel') == "hdl.handle.net":
                    boolean_list_if_pids_exists[1] = 1
                    existing_pid = str(identifier.find('.//dc:identifier', ns).text).strip()
                    if version_pid and version_pid != existing_pid:
                        raise ValueError(
                            f"Parameter version_pid={version_pid} clashes with"
                            f" existing value in {filename}: {existing_pid}.")
                    version_uuid = str(identifier.find('.//dc:identifier', ns).text).strip().split('/')[1]
                    dataObjectPids.extend(
                        helpers.getDAtaObejctPidsFrom_Versionhandle(version_pid, connection_details['url'],
                                                                    connection_details['user'],
                                                                    connection_details['password']))
                    break

            xml_tree_modified = False
            if version_pid:
                if not boolean_list_if_pids_exists[1]:
                    pid = version_pid
            elif not boolean_list_if_pids_exists[1]:
                version_uuid = str(uuid.uuid4())
                version_pid = '21.T11998/{}'.format(str(version_uuid))
                dataObjectPids = [dataobject_Pid]
                if dumpjsons:
                    json.dump(mets2handle.buildVersionJson(dmdsec, ns, pid_works=cinematographic_work_pids,
                                                           dataobject_pid=dataObjectPids, version_pid=version_pid),
                              open('version.json', 'w', encoding='utf8'),
                              indent=4, sort_keys=False, ensure_ascii=False)

                payload_version = mets2handle.buildVersionJson(root, ns, pid_works=cinematographic_work_pids,
                                                               dataobject_pid=dataObjectPids, version_pid=version_pid)

                response_from_handle_server = requests.put(connection_details['url'] + version_uuid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload_version))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Response to create-Version-request')
                response_from_handle_server.raise_for_status()

                if True: # Just to keep diff output short
                    # gets pid from response
                    respon = json.loads(response_from_handle_server.text)
                    pid = respon['handle']
            else:
                pid = existing_pid
            if pid:
                if True: # Just to keep diff output short
                    version_pid = pid

                    # writes new PID into the mets file
                    for workPid in cinematographic_work_pids:
                        dmdsec.find('.//ebucore:isVersionOf', ns).addprevious(
                            helpers.buildisVersiontOfVersionXML(workPid))
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '
                    xml_tree_modified = True

            # Update list of referenced DataObjects
            old_references = dmdsec.xpath(
                './/ebucore:hasPart[@formatLabel="hdl.handle.net"]', ns)
            recorded_data_objects = set([
                str(el.find('.//dc:identifier', ns).text).strip()
                for el in old_references])
            if recorded_data_objects != set(dataObjectPids):
                insert_here = dmdsec.find('.//ebucore:hasPart', ns)
                for pid in dataObjectPids:
                    insert_here.addprevious(
                        helpers.buildHasPartInXML(pid))
                if old_references:
                    parent_element = data_object_references[0].getparent()
                    for old_record in data_object_references:
                        parent_element.remove(old_record)
                xml_tree_modified = True

            if xml_tree_modified:
                if True: # Just to keep diff output short
                    with open(out_file, 'wb') as metsfile:

                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')

        # if the ID attribute of the dmdSec element is in the list of dataobjects,
        #  generate a new UUID to use as the PID for the work, generate the JSON for the dataobject,
        # write it to a file, and send a PUT request to the handle server to create a new handle for the dataobject
        if dmdsec.get('ID') in dataobjects:

            for identifier in dmdsec.findall('.//ebucore:identifier', ns):
                # checks if work has a existing pid. if thats the case we add a 1 to the boolean array
                if identifier.get('formatLabel') == "hdl.handle.net":
                    boolean_list_if_pids_exists[2] = 1

            if not boolean_list_if_pids_exists[2] and not boolean_list_if_pids_exists[1]:
                # dataobject, work or version has never been seen by the handle -> new mets
                json.dump(mets2handle.buildData_Object_Json(dmdsec, ns, dataobject_Pid, version_pid),
                          open('dataobject.json', 'w', encoding='utf8'),
                          indent=4, sort_keys=False, ensure_ascii=False)

                payload = mets2handle.buildData_Object_Json(dmdsec, ns, dataobject_Pid, version_pid)

                # Create PID
                response_from_handle_server = requests.put(connection_details['url'] + data_object_uuid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Response to create-DataObject-request')
                response_from_handle_server.raise_for_status()
                if True: # Just to keep diff output short
                    respon = json.loads(response_from_handle_server.text)
                    pid = respon['handle']
                    dataobject_Pid = pid

                    # writes new PID into the mets file
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '

                    dmdsec.find('.//ebucore:isPartOf', ns).addprevious(
                        helpers.buildIsPartOfInXML(version_pid))

                    new_tree = ET.tostring(xml_tree, pretty_print=True)
                    with open(out_file, 'wb') as metsfile:
                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')

            if boolean_list_if_pids_exists[0] and boolean_list_if_pids_exists[1] and not boolean_list_if_pids_exists[
                2]:  # case fresh dataobject in mets where version and work have a pid already
                json.dump(mets2handle.buildData_Object_Json(dmdsec, ns, dataobject_Pid, version_pid),
                          open('dataobject.json', 'w', encoding='utf8'),
                          indent=4, sort_keys=False, ensure_ascii=False)

                payload = mets2handle.buildData_Object_Json(dmdsec, ns, dataobject_Pid, version_pid)

                # Create PID
                response_from_handle_server = requests.put(connection_details['url'] + data_object_uuid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Response to create-DataObject-request')
                response_from_handle_server.raise_for_status()
                if True: # Just to keep diff output short
                    respon = json.loads(response_from_handle_server.text)
                    pid = respon['handle']

                    # writes new PID into the mets file
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '

                    dmdsec.find('.//ebucore:isPartOf', ns).addprevious(
                        helpers.buildIsPartOfInXML(version_pid))

                    new_tree = ET.tostring(xml_tree, pretty_print=True)
                    with open(out_file, 'wb') as metsfile:
                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')

                payload_version = mets2handle.buildVersionJson(root, ns, pid_works=cinematographic_work_pids,
                                                               dataobject_pid=dataObjectPids, version_pid=version_pid)
                print(payload_version)
                print(version_uuid)
                response_from_handle_server = requests.put(connection_details['url'] + version_uuid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload_version))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Response to update-Version-request')

                print(response_from_handle_server)
                response_from_handle_server.raise_for_status()
    return True  # if successfull


def cli_entry_point():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--credentials', metavar='<credentials_file>',
        default='handle_connection.txt',
        help='File containing credentials for access to handle system'
        ' (default: %(default)s).')
    parser.add_argument(
        '-d', '--dump-jsons', action='store_true',
        help='Write generated json to stdout in, then send request.')
    parser.add_argument(
        '-o', '--out-file', metavar='<modified_mets>',
        help='Do not modify METS in place but write to this file instead.')
    parser.add_argument(
        '-v', '--version-pid', metavar='<known_handle_for_version>',
        help='Instead of registering new version handle, use this one.')
    parser.add_argument(
        '-w', '--work-pid', metavar='<known_handle_for_work>',
        help='Instead of registering new work handle, use this one.')
    parser.add_argument(
        'mets_file', metavar='<mets_file>',
        help='METS file containing dmdSecs for DataObject, Version, and Work.')
    args = parser.parse_args()
    return m2h(
        args.mets_file,
        out_file=args.out_file,
        work_pid=args.work_pid,
        version_pid=args.version_pid,
        credentials=args.credentials,
        dumpjsons=args.dump_jsons)
