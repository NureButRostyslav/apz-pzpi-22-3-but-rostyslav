# Приклад 2: Конвертація XML → JSON (Класовий адаптер) 
# Код без адаптера (ручне перетворення)
import xml.etree.ElementTree as ET
import json

# Стара система повертає XML
class XMLService:
    def get_xml(self):
        return "<person><name>John</name><age>30</age></person>"

# Клієнтський код
def process_data():
    xml_service = XMLService()
    xml_data = xml_service.get_xml()

    # Ручне перетворення
    root = ET.fromstring(xml_data)
    json_data = {
        "name": root.find("name").text,
        "age": int(root.find("age").text)
    }

    print("Processed JSON:", json.dumps(json_data, indent=2))

process_data()


# Код з класовим адаптером (автоматична конвертація)
import xml.etree.ElementTree as ET
import json

# Стара система (Adaptee)
class XMLService:
    def get_xml(self):
        return "<person><name>John</name><age>30</age></person>"

# Новий інтерфейс (Target)
class JSONServiceInterface:
    def get_json(self):
        pass

# Класовий адаптер
class XMLtoJSONAdapter(XMLService, JSONServiceInterface):
    def get_json(self):
        xml_data = self.get_xml()
        root = ET.fromstring(xml_data)
        return {
            "name": root.find("name").text,
            "age": int(root.find("age").text)
        }

# Клієнтський код
def process_data():
    adapter = XMLtoJSONAdapter()
    json_data = adapter.get_json()
    print("Processed JSON:", json.dumps(json_data, indent=2))

process_data()

