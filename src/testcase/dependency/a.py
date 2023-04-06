import xmltodict
import json

# Open the XML file
with open('pom.xml') as xml_file:
    # Parse the XML into an ordered dictionary
    xml_data = xmltodict.parse(xml_file.read())

# Convert the ordered dictionary to a JSON object
# json_data = json.dumps(xml_data, indent=4)

# Print the JSON data
print(xml_data["project"]["dependencyManagement"]["dependencies"])