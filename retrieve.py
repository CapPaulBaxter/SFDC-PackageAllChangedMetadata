from zeep import Client
import datetime

import os

USERNAME = 'USERNAME'
PASSWORD = 'PASSWORD'
VERSION  = 43.0
MIN_MOD_DATE =  datetime.datetime(2018,6,1, tzinfo=datetime.timezone.utc)

fileMissing = False
for requiredfile in ['partner.wsdl.xml','metadata.wsdl.xml']:
  if not os.path.exists(requiredfile):
    print('required wsdl ',requiredfile,' does not exist in the script folder, please retrieve from your salesforce org')
    fileMissing=True
if fileMissing:
  exit()

loginClient = Client('partner.wsdl.xml')
loginResponse = loginClient.service.login(USERNAME,PASSWORD)

soap_headers = {}
soap_headers['SessionHeader'] = loginResponse['sessionId']

metadataClient = Client('metadata.wsdl.xml')
metadataClient.set_default_soapheaders(soap_headers)

print(loginResponse['serverUrl'])

metadataService = metadataClient.create_service('{http://soap.sforce.com/2006/04/metadata}MetadataBinding',loginResponse['serverUrl'].replace('/u/','/m/'))

metadataDescription = metadataService.describeMetadata(VERSION)


changedTypes = {}

for metaDataType in metadataDescription.metadataObjects:
  namedTypes = []



  if len(metaDataType.childXmlNames) > 0:  
    for childXmlName in metaDataType.childXmlNames:
      namedTypes.append(childXmlName)
  else:
    namedTypes.append(metaDataType.xmlName)

  for namedType in namedTypes:
    metadataList = metadataService.listMetadata( metadataClient.type_factory('ns0').ListMetadataQuery(type=namedType,folder=None), VERSION )
    for component in metadataList:
      if component.lastModifiedDate >  MIN_MOD_DATE:
        updatedFullName = component.fullName

        if component.type == 'Layout' and component.namespacePrefix is not None:
          sobject,sep,name = component.fullName.partition('-')
          updatedFullName = "{}-{}__{}".format(sobject,component.namespacePrefix,name) 

        if 'Flow' == component.type:
          name,sep,version = component.fullName.rpartition('-')
          if not version.isdigit():
            updatedFullName = component.fullName+'-0'
            print(updatedFullName)


        typeSection  = changedTypes.setdefault(component.type, {})
        dateblock    = typeSection.setdefault(component.lastModifiedDate.date(),{})
        personblock  = dateblock.setdefault(component.lastModifiedByName,[] )
        personblock.append(updatedFullName)


from lxml import etree

package = etree.Element('Package')
doc = etree.ElementTree(package)

for namedtype,dates in sorted( changedTypes.items() ):
  typeBlock =  etree.SubElement(package,'types')
  for date,people in sorted( dates.items() ):
    

    for person,changes in sorted( people.items() ):
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
