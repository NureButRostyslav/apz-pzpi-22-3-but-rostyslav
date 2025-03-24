# Приклад звичайної функції (перетворення XML у JSON):

import json
import xml.etree.ElementTree as ET

def xml_to_json(xml_string):
    root = ET.fromstring(xml_string)
    data = {child.tag: child.text for child in root}
    return json.dumps(data, indent=4)

xml_data = "<data><name>John</name><age>30</age></data>"
json_data = xml_to_json(xml_data)
print(json_data)


# Приклад адаптера (Об'єктний адаптер, який дозволяє API працювати з XML, а не лише з JSON)

import json
import xml.etree.ElementTree as ET

# API, який працює лише з JSON
class JsonAPI:
    def send_request(self, json_data):
        print(f"Sending JSON data to API: {json_data}")

# Адаптер, який дозволяє працювати з XML, перетворюючи його у JSON
class XmlToJsonAdapter:
    def __init__(self, json_api):
        self.json_api = json_api

    def send_request(self, xml_data):
        root = ET.fromstring(xml_data)
        data = {child.tag: child.text for child in root}
        json_data = json.dumps(data, indent=4)
        self.json_api.send_request(json_data)

# Використання адаптера
xml_data = "<data><name>John</name><age>30</age></data>"
json_api = JsonAPI()
adapter = XmlToJsonAdapter(json_api)
adapter.send_request(xml_data)
