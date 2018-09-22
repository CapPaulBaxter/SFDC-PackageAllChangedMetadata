import sys
import lxml.etree as etree

if len(sys.argv) != 3:
  print('Should be called with two file names, the first being the base file and the second being a file of additons and replacements to perform')
  exit()


labelsbyFullName = {}

source = etree.parse(sys.argv[1]).getroot()
merge  = etree.parse(sys.argv[2]).getroot()

for label in source.findall('{http://soap.sforce.com/2006/04/metadata}labels'):
  labelsbyFullName[label.find('{http://soap.sforce.com/2006/04/metadata}fullName').text] = label

for label in merge.findall('{http://soap.sforce.com/2006/04/metadata}labels'):
  labelsbyFullName[label.find('{http://soap.sforce.com/2006/04/metadata}fullName').text] = label

for child in list(source):
    source.remove(child)

for k,v in sorted(labelsbyFullName.items()):
  source.append(v)

open('out.xml','wb').write( etree.tostring(source, pretty_print=True, encoding="UTF-8") )