'''
This module implements the mapping from the relevant Values in the METS xml to a JSON file that contains the Data for an Work Object which represents a cinematographic work.
The functions basicly map from the METS xml Values to  Handle Values by putting the Values from the XML files into dictionarys that can later be transformed to a JSON file that can be sent to the Handle server.

The function "buildWorkJson" calls al the functions and puts them into the right order to appear in the json file. It is possible to deselect values that should not appear in the json and therefore are not sent 
to the handle server

the function "create_identifier_element" creates and xml element that contains the information about the PID and which can later be inserted into the original METS file

'''
__author__ = "Henry Beiker"
__copyright__ = "Copyright 2023, Stiftung Deutsche Kinemathek"
__license__ = "GPL"
__version__ = "3.0"

from lxml import etree as ET
import uuid

def getIdentifier(pid_work:str):
    handleID =[ {'identifier':pid_work.upper()}]
    return {'type': 'identifiers','parsed_data':handleID}#21.T11148/fae9fd39301eb7e657d4

def getTitle(dmdsec :ET,ns):
    """
    Find the Original Title
    #21.T11148/4b18b74f5ed1441bc6a3
    TODO:
    In the current implementation only the last title with a valid titletype is used.
    Maybe we are more interested in another field.
    """
    titles=[]
    titletypen = ['originaltitle', 'releasetitle', 'archivetitle', 'alternativetitle', 'sorttitle']
    
    for title in dmdsec.findall(".//dc:title", ns):
        if str(title.find('..').get('typeLabel')).lower() not in titletypen :
            """
            TODO: Check if title can be mapped to on of the allowed titles.
            Add info to log file.
            """
            continue
        else:
            titletype=str(title.find('..').get('typeLabel'))
            # Need to capitalize
            titletype=titletype[0].capitalize()+titletype[1:]
        titles.append({'titleValue':title.text, 'titleType':titletype})
    return {'type': 'titles','parsed_data': titles}

def getSeriesName(dmdsec,ns):
    
    """
    Wenn das Werk einen Seriennamen besitzt, dann wird diser hiermit gefunden.
    Existiert kein Serienname ist der Eintrag None

    
    """
    #TODO: Es gibt noch ungereimtheiten bei den wertelisten sowie mit den identifiern
    name=" "
    for title in dmdsec.findall('.//ebucore:alternativeTitle',ns):
        if title.get('typeLabel')=='series':
            name=title.find('.//dc:title',ns).text

    title = {'type': 'series', 'parsed_data':name}#21.T11148/8c45d090913a21d5cac1
    return title

def getSource(dmdsec,ns):
    
    """
    Findet den Namen der Organisation, welche das Werk verwaltet
    """
    sources=[]
    for source in dmdsec.find('.//ebucore:organisationDetails',ns).findall('.//ebucore:organisationName',ns):
        
        sources.append({'name':source.text,'identifier_uri':source.find('..').get('organisationId')})
    source = {'type': 'sources',#21.T11148/b33655d6fe2e0e7244de
               'parsed_data':sources}
    return source

def getCredits(dmdsec,ns):
    """
    Findet den Regisseur
    """
    creditoptions=["Assistant Camera Operator","2nd Unit Director","2nd Unit Director of Photography","Adaptation","Animation","Art Director",
                    "Artistic direction","Assistant","Assistant Art Direction","Assistant Camera Operator","Assistant Director","Assistant Editor",
                    "Assistant Set Designer","Associate producer","Casting Director","Caterer","Chief Lighting Technician","Choreographer","Clapper Loader",
                    "Commentary","Compilation","Consultant","Continuity","Costume Design","Director","Director of Photography","Editor","Executive Producer",
                    "Film Funding","Foley Artist","Gowns by","Host","Idea","Lamp Operator","Line Producer","Location Scout","Make-up","Musical direction","Narration",
                    "Negative Cutter","Pre-Production Design","Producer","Producer","Production Assistant","Production design","Props","Researcher","Screenplay","Set Decorator",
                    "Set Decorator","Set Designer","Singing Voice","Sound","Sound Assistant","Sound Design","Sound Editor","Sound Recordist","Source Material","Special Effects",
                    "Special Effects Camera","Steadicam Operator","Still Photography","Stock Footage","Storyboard Artist","Stunt Coordinator","Title Design","TV Director","Visual Effects"]
    
    credits=[]
    for contributor in dmdsec.findall('.//ebucore:contributor',ns):
        
        for role in contributor.findall('.//ebucore:role',ns):
            
            if role.get('typeLabel').lower() in [creditoption.lower() for creditoption in creditoptions]:
                name=contributor.find('./ebucore:contactDetails',ns).find('./ebucore:name',ns).text.split(',')
               
                if contributor.find('.//ebucore:contactDetails',ns).get('contactId') != None: #checktob es eine uri gibt
                    credits.append({
                        'identifier':{'identifier':contributor.find('.//ebucore:contactDetails',ns).get('contactId').split('/')[-1],'identifier_uri':contributor.find('.//ebucore:contactDetails',ns).get('contactId')
                                      
                                      }
                        ,'name':{'family-name':name[0],'given-name':name[1].strip()},'role':str(role.get('typeLabel')).capitalize()
                        
                        })
                else:
                    credits.append({
                        
                        'name':{'family-name':name[0],'given-name':name[1].strip()},'role':role.get('typeLabel').capitalize()
                        
                        })

       
    
    return {'type': 'credits','parsed_data':credits}#21.T11148/66c22fad3a990a40eb2b

def getCast(dmdsec,ns):
    """
    Findet alle personen , welche vor der Kamera standen -> cast
    """
    cast=[]
    for contributor in dmdsec.findall('.//ebucore:contributor',ns):
        
        if  contributor.find('.//ebucore:role',ns).get('typeLabel')=='cast':
            name=contributor.find('./ebucore:contactDetails',ns).find('./ebucore:name',ns).text.split(',')
            if contributor.find('.//ebucore:contactDetails',ns).get('contactId') is not None:
                
                cast.append(
                    {'name':{'family-name':name[0],'given-name':name[1].strip()},
                    'identifier_uri':contributor.find('.//ebucore:contactDetails',ns).get('contactId')
                    
                     
                    
                    
                    
                    })
            else:
                cast.append(
                    {'name':{'family-name':name[0],'given-name':name[1].strip()},
                    
                    
                     
                    
                    
                    
                    })
                

                    
    if  len(cast)==0:
        return None                  
    return  {'type': 'cast','parsed_data':cast}#21.T11148/39aa12e6d633fbb40d65

def getOriginal_duration(dmdsec,ns):
    
    """
    
    Findet die Länge des Werkes
    21.T11148/b8a2e906c01f78a0d37b
    TODO:
    nicht in xml zu finden
    """
    duration=''# nicht in xml zu finden
    if duration =='':
        return None
    return {'type': 'original_duration','parsed_data':{'original_duration':duration}}

def getSource_identifier(dmdsec,ns):
    """
    21.T11148/4f79cf79777ae7c379fe
    Findet die identifier id/url der Hauptorganisation die dieses Werk verwaltet
    """
    return{'type': 'source_identifier', 'parsed_data': dmdsec.find('.//ebucore:organisationDetails', ns).get('organisationId')}
    
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

def getProduction_companies(dmdsec,ns):
    """
    Findet die am Werk beteiligten Produktionsfirmen
    21.T11148/cc9350e8525a1ca5ffe4
    """
    companies=[]
    # for companie in companies add {name + uri} to companies
    company=' '

    
    #platzhalter companielist nicht zu finden in xml

    if len(companies)==0:
        return None
    
    return {'type': 'production_companies','parsed_data':[{'production_company':companies}]}

def getOriginal_language(dmdsec,ns):
    """
    Findet die Sprache, in der das Werk erstmalig aufgenommen worden ist
    21.T11148/577d96232ee6ea2f8dfa
    """
    
    original_languages=[]
    if not len(original_languages):
        return None

    #platzhalter nicht klar im xml 
    return {'type': 'original_languages','parsed_data':original_languages}

def getCountries_of_reference(dmdsec,ns):
    """
    Findet ursprungsland
    TODO:
    Unklar ob es mehrere urspunrgsländer gebven kann

    es muss unbedingt die länder liste geändert werden
    """
    land = []
    for country in dmdsec.findall('.//ebucore:location', ns):
        land.append(country.find('.//ebucore:name', ns).text)
    
    if  not len(land):
        return None
    return{'type': 'countries_of_reference', 'parsed_data': land}

def getYears_of_reference(dmdsec,ns):#wird eventuell noch abgeändert
    
    """
    Findet den Erstellsungszeitraum hier Benannt year of reference
    
    21.T11148/089d6db63cf69c35930d
    """
    
    years = [{'startYear': dmdsec.find(".//ebucore:date", ns).find(".//ebucore:created", ns).get("startYear"), 
             'endYear': dmdsec.find(".//ebucore:date", ns).find(".//ebucore:created", ns).get("endYear"),
             'referenceType':'created'}]# referenceType nicht gegeben aber immer created ?
    
    return {'type': 'years_of_reference','parsed_data':years}

def getRelated_identifier(dmdsec,ns):#was bedeute das comment?
    """
    Findet andere Identifier wie ISAN oder EIDR
    Bisher nicht im xml zu finden
    
    21.T11148/d72482f16d18ff46f8f4
    """
    #identifiertlist = []
    #for identifier in dmdsec.findall('.//ebucore:identifier',ns):
        #identifiertlist.append( {'relatedIdentifierValue': identifier.find('.//dc:identifier',ns).text , 'relatedIdentifiertType':identifier.get('formatLabel')}) #immer other? oder doch format label?)
    return {'type': 'related_identifiers', 'parsed_data': {'relatedIdentifierValue': ' ', 'relatedIdentifierType': ' '}}

def getgenre(dmdsec,ns):
    """
    Findet das Genre eines Filmes und
    21.T11148/cee386b04503398bc6ca
    ["Amateur film","Animation","Animation with live-action","Non-fiction","Documentary-drama",
    "Anthology film","Essay film","Experimental film","Home movie","Industrial film","Compilation film",
    "Short film","Educational film","Music video","Propaganda film","Fiction","Trailer","Advertising film","Newsreel"]
    TODO:
    Unklar, ob ein Film mehrere Genres haben kann
    get('typeLabel')
    """
    
    genrelist=[]
    
    for genre in dmdsec.findall('.//ebucore:genre', ns):
        if genre.get('typeLabel')=="nonFiction":
            
            genre_done='Non-fiction'
        else:
            genre_done=genre.get('typeLabel')
        genrelist.append(str(genre_done).capitalize())
    
    return {'type': 'genres', 'parsed_data': genrelist} #mehrere genres ?

def getOriginal_format(dmdsec,ns):
    """
    Gibt das Format zurück, auf welchem der Film gespeichert wurde
    21.T11148/cda76378eeb3ce51a3ff
    TODO:
    Noch unklar, wo in der XML Datei das zu finden ist
    """
    
    format ='' # wo zu finden? was ist gemeint ?
    if not len(format):
        return None
    return {'type': 'original_format','parsed_data':format}


#build json gibt ein dict zurück, welches von der json bibliothek in die fertige json datei ausgegeben werden kann. Standarmä
def buildWorkJson(dmdsec, ns,pid_work,handleId=True,title=True,series=False,credit=False,cast=True,
original_duration=True,Source=True,source_identifier=False,last_modifed=True,production_companies=True,
countries_of_reference=True,original_language=True,years_of_reference=True,
related_identifier=True,original_format=True,genre=True):
    """
    Erhält als Eingabe ein Xml Element
    Gibt ein Dict zurück, welches die Struktur für eine Json Datei beinhaltet, wie sie das Handle System erwartet.
    Die Struktur kann verändert werden, indem die if-Bedingungen in der Funktion selbstr vertauscht werden.
    Es können Blöcke weggelassen werden, wenn beim Funktionsaufruf der jeweilige Block mit =False belegt wird.
    Standardmäßig werden alle Blöcke ausgegeben
    """
    json=dict()
    values=[]
    #if handleId:
      #  values.append(getIdentifier (pid_work))
    
    if title:
        values.append(getTitle(dmdsec,ns))
    
    if series:
        values.append(getSeriesName(dmdsec,ns))
    
    if credit:
        values.append(getCredits(dmdsec,ns))
    
    if cast:
        values.append(getCast(dmdsec,ns))
    
    if original_duration:
        values.append(getOriginal_duration(dmdsec,ns))
    
    if Source:
        values.append(getSource(dmdsec,ns))
    
    if source_identifier:
        values.append(getSource_identifier(dmdsec,ns))
    
    if last_modifed:
        values.append(getLast_modified(dmdsec,ns))
    
    if production_companies:
        values.append(getProduction_companies(dmdsec,ns))
    
    if countries_of_reference:
        values.append(getCountries_of_reference(dmdsec,ns))
    
    if original_language:
        values.append(getOriginal_language(dmdsec,ns))
    
    if years_of_reference:
        values.append(getYears_of_reference(dmdsec,ns))
    
    if related_identifier:
        values.append(getRelated_identifier(dmdsec,ns))
    

    if original_format:
        values.append(getOriginal_format(dmdsec,ns))
    
    if genre:
        values.append(getgenre(dmdsec,ns))
    
    values.append({'type':'KernelInformationProfile','parsed_data':'21.T11148/31b848e871121c47d064'}) #version 0.1
    
    json=  [value for value in values if value is not None] 
    
    return json







def create_identifier_element(pid):
   
   ebuident = ET.Element('{urn:ebu:metadata-schema:ebucore}identifier',)
   ebuident.attrib['formatLabel'] = 'hdl.handle.net'
   ebuident.text='\n    '
   
   dcident = ET.SubElement( ebuident, '{http://purl.org/dc/elements/1.1/}identifier')
   dcident.text = pid+'\n              '
   dcident.tail = '\n            '
   
   attributor = ET.SubElement(
       dcident, '{urn:ebu:metadata-schema:ebucore}attributor')
   attributor.text = '\n               '
   attributor.tail = '\n              '
   
   orgadetals = ET.SubElement(
       attributor, '{urn:ebu:metadata-schema:ebucore}organisationsDetails')
   orgadetals.attrib['organisationsID'] = 'url to handle doku zu kinemathek?'
   orgadetals.text = '\n                '
   orgadetals.tail = '\n              '

   organame = ET.SubElement(
       orgadetals, '{urn:ebu:metadata-schema:ebucore}organisationName')
   organame.text = 'Handlesystem ? Kinemathek ?'
   organame.tail = '\n               '
    
   return ebuident



