# Dokumentation für das Tool welches METS mit einem Handle-Server verbindet

## Ziel des Tools
Das Tool erstellt aus einer METS-Datei welche verschiedenste Informationen und Daten über ein Film-Wert enthält eine Json Datei.
Diese Json Datei wird anschließen an einen Handle server geschickt werden. Nun wird geprüft, ob das Werk schon existiert. Ist dies der Fall, wird in die METS-Datei die fehlende PID geschrieben. Ist das Werk auf dem Handle Server noch nicht vorzufinden, wird eine neue PID angelegt und ebenfalls in die METS-Datei geschrieben

## Input
Als Input erhält das Tool eine METS-Datei. Das Format dieser Datei entspricht dem XML Format.
Das Tool erhält die METS-Datei über den Pfad welcher als Argument beim Aufruf des Tools übergeben wird.


## Module
Es gibt 2 Module in diesem Tool. Zum einen das metstohandle Modul von wo aus die METS Datein eingelesen wird, sowie die nötigen Funktionen aus dem 2. Modul: dem xmltojson Modul aufgerufen werden. Im xmltojson Modul finden sich allerhand funktionen, die es ermöglichen bestimme Blöcke aus der METS-Datei für die umwandlung in das Json Format auszulesen udn aufzubereiten.

1. metstohandle
   * In diesem Modul werden die Module "lxml, "json", "sys" ,"request" ,"urllib.request" ,"urllib.error" ,"urllib.parse" und "db_works_tohandle" importiert.
   * Zuerst wird mithilfe der Elementree Bibliothek die Mets Datei eingelesen sodass hiermit nun gearbeitet werden kann. Zum einlesen wird der parse funktion der relative Pfad als argument beim aufrufen des Tools übergeben. 
   * Nun werden die einzelnen Sektionen ( Einzelne Werke bei Multiwork Dateien oder regulär Werk, Version ,DataObject, etc) mithilfe der in der METS Datei enthaltenen Struct-Map extrahiert, um diese in den kommenden Schritten auszulesen und in eine Json Datei zu schreiben.
   * das Dict ns wird benötigt, um mit den verschiedenen Namespaces in der METS-Datei umgehen zu können. Fehlt dieses, kann Elementree später nicht nach den Nametags in der Mets Datei suchen da diese nicht zu finden sind. Dokumentation Elementree: https://docs.python.org/3/library/xml.etree.elementtree.html
   * Um nun die Json-Datei zu generieren gibt es 2 Möglichkeiten: 1. Man kann die funktion buildJson aus xmltojson aufrufen und erhält eine Standard Json-Datei 2. Man stellt sich die Json Datei selber zusammen. Hierfür empfehlen wir die json Dokumentation für das json Modul: https://docs.python.org/3/library/json.html
   * Zusammengefasst wollen brauchen wir für eine Object in Json ein Dict in Python und für ein Array eine liste. Diese können beliebig verschachtelt werden, um die gewünschte Json Struktur zu erhalten
   * nachdem die Json Datei für ein Werk bzw. Abschnitt erstellt worden ist, werden die Json Datei mit einem HTTP-POST request an den Handle Server geschickt. Dazu werden die Authentifizierungsdaten, die url vom Server, ein Header sowie die Json datei als String benötigt. Ist der Post Request erfolgreich, schickt der Server den Code 201 und die Handle-ID zurück.
   * Sobald wir die Handle ID vom Server erhalten haben, schreiben wir diese zum zugehörigen Werk in die METS Datei. Um das Identifier Object zu erstellen wir dei Funktion aus dem db_works_tohandle Modul verwendet welche die Struktur sowie die richtige Formatierung und Einrückung vornimmt.



2. xmltojson
   * In diesem Modul wird lediglich das Modul Elementree importiert: https://docs.python.org/3/library/xml.etree.elementtree.html
   * Das Modul sorgt dafür, dass verschiedenste Objecte für das Json Format aus aus der METS-Datei ausgelesen werden und aufbereitet werden. Zudem enthält das Modul eine Funktion names buildJson welche Objecte in einer bestimmten Reihenfolge ausgibt. Hier eine Beschreibung aller Funktionen:
   * Paramater für alle Funktionen außer buildJson:
    Element des XML-Trees von welchem aus gesucht werden soll. Dies kann auch die Wurzel sein. Außerdem das Dict mit den Namespaces für die METS-Datei
   * getHandleID
     
     * Findet sofern sie existiert die HandleID udn gibt die als Eintrag verschachtelt in Dicts zurück
    
   * getTitle
      
      * Findet den Original Titel eines Werkes udn gibt diesen als Eintrag in Dicts verschachtel zurück
    
    * getSeriesName 
      * Findet sofern vorhanden den Serien Namen eines Werkes und gibt diesen als Eintrag in einem Dict Verschachtelt zurück. Wird der Serienname nicht gefunden ist der Wert NONE
    
    * getSource
      * Findet die Organisation, welche die Daten zur verfügung gestellt hat und gibt diese Verschachtelt als Eintrag in  Dicts zurück
    * getCredits
      * Findet den Regiseur eines Werkes und gibt diesen als Eintrag mit dem Format "Regisseur (director)" verschachtelt in Dicts zurück
    * getCast
      * Findet den Cast also alle Personen die vor der Kamera standen und gibt diese mit dem Format "cast1 ; cast2;..." verschachtelt in Dicts zurück 
    * getSource_identifier
      * Findet einen eindeutige ID die der Organisation welche mit getSource gefunden  zugewordnet werden kann udn gibt diese als Eintrag verschachtelten Dicts zurück
     * getLast_modified
       * Findet das Datum, in dem die METS-Datei zuletzt verändert worden ist und gibt dieses als Eintrag in verschachtelten Dicts zurück 
     * getCountries_of_reference
       * Findet das Land in dem das Werk gedreht worden ist und gibt dieses als Eintarg in einem Verschachtelten Dict zurück
     * getYears_of_reference
       * Findet das Start und Endjahr des Produktionszeitraumes. Und gibt diese jeweils als Einträge in einem verschachtelten Dict zurück
     * getRelated_identifiert
       * Findet alle identifiert, welche zusätzlich zu der in getSourece_identifiert gefundenen ID gefunden werden und gitb diese als Einträge in einem verschachtelten Dict zurück
     * getGenre
       * findet die zu dem Werk zugeordneten Genres udn gibt diese als Einträge in einem Dict zurück
     * buildJson
       * Parameter: Zusätzlich zum Element des XML-Baumes und dem Namespace können außerdem diverse Paramater auf True oder False gesetzt werden. Per Default sind alle Werte auf True gesetzt
     * Je nach dem welche Werte auf True gesetzt sind werden die verschiedenen vorher aufgelisteten Funktionen aufgerufen und die Dicts in eine Liste geschrieben. Dies hat zur folge, dass der Rückgabe Wert ein Dict ist welches so strukturiert ist, sodass das daraus resultierende Json vom Handle Server akzeptiert wird

## Beispiel für den Aufbau eines Dicts um eine Json-Datei zu erzeugen

Der Handle server benötigt ein Json welches folgendermaßen aufgebaut ist:

{
    
    "handle" : "handleid ,
    "values" :[
        {object 1},
        {object 2},
        {obect 3},
        ...
    ]
}

Ein Objekt entspricht in Python einem Dict und eine Array einer Liste. Dies machen wir uns zu nutze.

Zuerst erstellen wir uns eine Liste welche später alle Objekte 1-n für das Value Array enthält. In dieser Liste sind wiederum Dicts, welche dementsprechend eigene Objekte sind. Auch diese Objekte haben wiederum eine Vorgeschriebene Struktur. Diese Struktur wird durch die in xmltojson enthaltenen Funktionen eingehalten.

Wir müssen und also lediglich die Dicts aus den Rückgabewerten der Funktionen in die Liste in der gewünschten Reihenfolge einfügen.

Nun müssen wir nurnoch das Json Object ansich erzeugen.
Also ein Dict:

json={handle:handleid,values: liste mit den Dicts }

Dieses Dict können wir nun mit der funktion "dump" aus der json Bibliothek speichern bzw. danach weiterverarbeiten und an den Handle server schicken


