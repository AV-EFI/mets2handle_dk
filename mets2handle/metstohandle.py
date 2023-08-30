#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Henry Beiker, Sven Bingert"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

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
    try:
        with open(credentials, "r") as f:
            for line in f:
                key, value = line.strip().split("|")
                connection_details[key] = value
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        print('Please make sure that handle_connection.txt is in the same folder')

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
            # TODO: hier abfrage, ob Werk bereits Pid hat

            for identifier in dmdsec.findall('.//ebucore:identifier',
                                             ns):  # checks if work has a existing pid. if thats the case we add a 1 to the boolean array
                if identifier.get('formatLabel') == "hdl.handle.net":
                    boolean_list_if_pids_exists[0] = 1
                    cinematographic_work_pids.append(str(identifier.find('.//dc:identifier', ns).text).strip())

            if not boolean_list_if_pids_exists[0]:
                uid = str(uuid.uuid4())
                cinematographic_work_pid = '21.T11998/{}'.format(str(uid))
                cinematographic_work_pids.append(cinematographic_work_pid.upper())

                if dumpjsons:
                    json.dump(mets2handle.buildWorkJson(dmdsec, ns, pid_work=cinematographic_work_pid),
                              open(str(multiworkno) + 'handlejson.json', 'w', encoding='utf8'),
                              indent=4, sort_keys=False, ensure_ascii=False)

                payload = mets2handle.buildWorkJson(root, ns, pid_work=cinematographic_work_pid,
                                                    original_duration=False,
                                                    related_identifier=False, original_format=False)
                response_from_handle_server = requests.put(connection_details['url'] + uid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Work Created')

                respon = json.loads(response_from_handle_server.text)
                multiworkno = multiworkno + 1
                if response_from_handle_server.status_code == 201:
                    # gets pid from response
                    pid = respon['handle']

                    # writes new PID into the mets file
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '

                    new_tree = ET.tostring(xml_tree, pretty_print=True)
                    with open(out_file, 'wb') as metsfile:

                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')
                else:
                    print(response_from_handle_server.status_code, respon)

        # if the ID attribute of the dmdSec element is in the list of versions,
        #  generate a new UUID to use as the PID for the work, generate the JSON for the version,
        # write it to a file, and send a PUT request to the handle server to create a new handle for the version
        if dmdsec.get('ID') in versions:
            uid = str(uuid.uuid4())
            version_pid = '21.T11998/{}'.format(str(uid))
            dataObjectPids = [dataobject_Pid]
            # TODO: Hier gegebenenfalls abfrage, ob Versions_pid bereits im METS vorhanden ist
            for identifier in dmdsec.findall('.//ebucore:identifier',
                                             ns):  # checks if work has a existing pid. if thats the case we add a 1 to the boolean array
                if identifier.get('formatLabel') == "hdl.handle.net":
                    boolean_list_if_pids_exists[1] = 1
                    version_pid = str(identifier.find('.//dc:identifier', ns).text).strip()
                    uid = str(identifier.find('.//dc:identifier', ns).text).strip().split('/')[1]
                    dataObjectPids.extend(
                        helpers.getDAtaObejctPidsFrom_Versionhandle(version_pid, connection_details['url'],
                                                                    connection_details['user'],
                                                                    connection_details['password']))

            if not boolean_list_if_pids_exists[1]:
                if dumpjsons:
                    json.dump(mets2handle.buildVersionJson(dmdsec, ns, pid_works=cinematographic_work_pids,
                                                           dataobject_pid=dataObjectPids, version_pid=version_pid),
                              open('version.json', 'w', encoding='utf8'),
                              indent=4, sort_keys=False, ensure_ascii=False)

                payload_version = mets2handle.buildVersionJson(root, ns, pid_works=cinematographic_work_pids,
                                                               dataobject_pid=dataObjectPids, version_pid=version_pid)

                response_from_handle_server = requests.put(connection_details['url'] + uid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload_version))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Version Created')

                if response_from_handle_server.status_code == 201:
                    # gets pid from response
                    respon = json.loads(response_from_handle_server.text)
                    pid = respon['handle']

                    # writes new PID into the mets file
                    for workPid in cinematographic_work_pids:
                        dmdsec.find('.//ebucore:isVersionOf', ns).addprevious(
                            helpers.buildisVersiontOfVersionXML(workPid))
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '

                    new_tree = ET.tostring(xml_tree, pretty_print=True)
                    with open(out_file, 'wb') as metsfile:

                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')

                respon = json.loads(response_from_handle_server.text)

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

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Dataobject Created')
                if response_from_handle_server.status_code == 201:
                    respon = json.loads(response_from_handle_server.text)
                    pid = respon['handle']

                    # writes new PID into the mets file
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '

                    new_tree = ET.tostring(xml_tree, pretty_print=True)
                    with open(out_file, 'wb') as metsfile:
                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')
                        metsfile.close

            if boolean_list_if_pids_exists[0] and boolean_list_if_pids_exists[1] and not boolean_list_if_pids_exists[
                2]:  # case fresh dataobject in mets where version and work have a pid already

                payload_version = mets2handle.buildVersionJson(root, ns, pid_works=cinematographic_work_pids,
                                                               dataobject_pid=dataObjectPids, version_pid=version_pid)
                print(payload_version)
                print(uid)
                response_from_handle_server = requests.put(connection_details['url'] + uid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload_version))

                print(response_from_handle_server.text, response_from_handle_server.status_code, 'Dataobject Created')

                print(response_from_handle_server)

                json.dump(mets2handle.buildData_Object_Json(dmdsec, ns, dataobject_Pid, version_pid),
                          open('dataobject.json', 'w', encoding='utf8'),
                          indent=4, sort_keys=False, ensure_ascii=False)

                payload = mets2handle.buildData_Object_Json(dmdsec, ns, dataobject_Pid, version_pid)

                # Create PID
                response_from_handle_server = requests.put(connection_details['url'] + data_object_uuid, auth=(
                    connection_details['user'], connection_details['password']), headers=header,
                                                           data=json.dumps(payload))

                print(response_from_handle_server.text, response_from_handle_server.status_code)
                if response_from_handle_server.status_code == 201:
                    respon = json.loads(response_from_handle_server.text)
                    pid = respon['handle']

                    # writes new PID into the mets file
                    new_ident = mets2handle.create_identifier_element(pid)

                    new_ident.text = '\n              '
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).addprevious(new_ident)
                    dmdsec.find('.//ebucore:coreMetadata', ns).find('ebucore:identifier', ns).tail = '\n\n            '

                    new_tree = ET.tostring(xml_tree, pretty_print=True)
                    with open(out_file, 'wb') as metsfile:
                        baum = ET.ElementTree(root)
                        baum.write(metsfile, xml_declaration=True, encoding='utf-8')
    return True  # if successfull
