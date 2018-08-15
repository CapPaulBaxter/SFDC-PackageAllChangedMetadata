from zeep import Client
import datetime

import os

USERNAME = 'USERNAME'
PASSWORD = 'PASSWORD'
VERSION  = 43.0
MIN_MOD_DATE =  datetime.datetime(2018,6,1, tzinfo=datetime.timezone.utc)
INDIVIDUAL_CHILD_ELEMENTS = True
USERS_TO_IGNORE = set(['FSL','SBQQ'])


fileMissing = False
for requiredfile in ['partner.wsdl.xml','metadata.wsdl.xml']:
  if not os.path.exists(requiredfile):
    print('required wsdl ',requiredfile,'does not exist in the script folder, please retrieve from your salesforce org')
    fileMissing=True
if fileMissing:
  exit()

loginClient = Client('partner.wsdl.xml')
loginResponse = loginClient.service.login(USERNAME,PASSWORD,_soapheaders={'CallOptions':{'client':'RetieveMetdataSinceDate'}})

soap_headers = {}
soap_headers['SessionHeader'] = loginResponse['sessionId']

metadataClient = Client('metadata.wsdl.xml')
metadataClient.set_default_soapheaders(soap_headers)

print(loginResponse['serverUrl'])

metadataService = metadataClient.create_service('{http://soap.sforce.com/2006/04/metadata}MetadataBinding',loginResponse['serverUrl'].replace('/u/','/m/'))

metadataDescription = metadataService.describeMetadata(VERSION)


changedTypes = {}
lastrefs     = {}
maxDates     = {}

for metaDataType in metadataDescription.metadataObjects:
  namedTypes = []

  if len(metaDataType.childXmlNames) > 0:  
    for childXmlName in metaDataType.childXmlNames:
      namedTypes.append( (childXmlName,True,metaDataType.xmlName) )
  else:
    namedTypes.append( (metaDataType.xmlName,False,metaDataType.xmlName) )

  for namedType,isChild,parentTupe in namedTypes:
    metadataList = metadataService.listMetadata( metadataClient.type_factory('ns0').ListMetadataQuery(type=namedType,folder=None), VERSION )
    for component in metadataList:
      if component.lastModifiedDate >  MIN_MOD_DATE and component.lastModifiedByName not in USERS_TO_IGNORE:
        updatedFullName = component.fullName

        if component.type == 'Layout' and component.namespacePrefix is not None:
          sobject,sep,name = component.fullName.partition('-')
          updatedFullName = "{}-{}__{}".format(sobject,component.namespacePrefix,name) 

        if 'Flow' == component.type:
          name,sep,version = component.fullName.rpartition('-')
          if not version.isdigit():
            updatedFullName = component.fullName+'-0'
            print(updatedFullName)

        if INDIVIDUAL_CHILD_ELEMENTS or not isChild:
          typeSection  = changedTypes.setdefault(component.type, {})
          dateblock    = typeSection.setdefault(component.lastModifiedDate.date(),{})
          personblock  = dateblock.setdefault(component.lastModifiedByName,[] )
          personblock.append(updatedFullName)
          maxDates[ component.type,updatedFullName ] = component.lastModifiedByName,component.lastModifiedDate.date()
        else:
          typeSection  = changedTypes.setdefault(parentTupe, {})
          dateblock    = typeSection.setdefault(component.lastModifiedDate.date(),{})
          personblock  = dateblock.setdefault(component.lastModifiedByName,[] )
          if '.' in updatedFullName:
            updatedFullName  = updatedFullName.partition('.')[0]
          else:
            updatedFullName = '*'

          personblock.append( updatedFullName )
          maxDates[ component.type,updatedFullName ] = component.lastModifiedByName,component.lastModifiedDate.date()


for metaDataType,dates in changedTypes.items():
  seenEntries = set()
  for date,people in sorted(dates.items(),reverse=True):
    for person,components in people.items():
      dedupedComponents = list(set([x for x in components if x not in seenEntries]))
      seenEntries.update(dedupedComponents)
      people[person] = dedupedComponents
      print(metaDataType,date,person,set(components))

from lxml import etree

package = etree.Element('Package')
doc = etree.ElementTree(package)

for namedtype,dates in sorted( changedTypes.items() ):
  typeBlock =  etree.SubElement(package,'types')
  for date,people in sorted( dates.items() ):
    

    for person,changes in sorted( people.items() ):
      if len(changes)>0:
        typeBlock.append( etree.Comment( '{} On {} START'.format( person, date.strftime('%D') ) ) )

      for change in sorted( changes ):
        el = etree.Element('members')
        el.text = change
        typeBlock.append( el )

  nameElem =  etree.SubElement(typeBlock,'name')
  nameElem.text = namedtype

ver = etree.Element('version')
ver.text = str( VERSION )
package.append(ver)


with open('./package.xml', 'wb') as f:
    f.write( etree.tostring(doc,pretty_print=True, xml_declaration=True, encoding='UTF-8') )
