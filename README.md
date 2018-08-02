# SFDC-PackageAllChangedMetadata
Queries for all changed metadata since a given date and generates a salesforce package.xml file

How to run:
 - `pip install -r requirements.txt` ideally in a new virtualenv to install dependencies.
 - Update the constants USERNAME,PASSWORD,VERSION and MIN_MOD_DATE in the script.
 - Download the partner and metadata wsdl from your salesforce org and place them in the same folder as the script.
 - Rename the two wsdls as `partner.wsdl.xml` and `metadata.wsdl.xml`
 - Run the script

Will retrieve all components of all types that have been channged since the MIN_MOD_DATE set and output a file named package.xml

Output is separated by comments listing the most recent change date and person who changed the component, grouped by name and day.

Output looks like:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<Package>
  <types>
    <!--Emmett Smyth On 06/03/18 START-->
    <members>FancyStringPrinter</members>
    <members>OtherStringPrinter</members>
    <!--Fathima Stein On 06/08/18 START-->
    <members>SomeClass_test</members>
    <members>SomeOtherClass_test</members>
    <name>ApexClass</name>
  </types>
  <types>
    <!--Rehan Begum On 08/02/18 START-->
    <members>SBQQ__Quote__c.Quote Not Accepted Status</members>
    <name>WorkflowRule</name>
  </types>
  <version>43.0</version>
</Package>
```
