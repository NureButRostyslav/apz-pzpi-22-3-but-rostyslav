# Приклад 2: Конвертація XML → JSON (Класовий адаптер) 
# Код без адаптера (ручне перетворення)
import xml.etree.ElementTree as ET
import json

class XMLService:
    """Старий сервіс, який повертає дані у форматі XML"""
    def get_data(self):
        return """<data>
                    <temperature>25</temperature>
                    <humidity>60</humidity>
                  </data>"""

class JSONApp:
    """Новий застосунок, який працює тільки з JSON"""
    def display_data(self, data_json):
        print(f"Received JSON data: {data_json}")

# Використання без адаптера (ручне перетворення)
xml_service = XMLService()
json_app = JSONApp()

xml_data = xml_service.get_data()  # Отримуємо XML
root = ET.fromstring(xml_data)  # Розбираємо XML вручну
data = {child.tag: int(child.text) for child in root}  # Конвертуємо в словник
json_data = json.dumps(data)  # Перетворюємо у JSON

json_app.display_data(json_data)  # Ручна конвертація кожного разу


# Код з класовим адаптером (автоматична конвертація)
import xml.etree.ElementTree as ET
import json

class XMLService:
    """Старий сервіс, який повертає дані у форматі XML"""
    def get_data(self):
        return """<data>
                    <temperature>25</temperature>
                    <humidity>60</humidity>
                  </data>"""

class XMLServiceAdapter(XMLService):
    """Класовий адаптер, який успадковує XMLService та конвертує XML → JSON"""
    def get_data(self):
        xml_data = super().get_data()  # Викликаємо метод батьківського класу
        root = ET.fromstring(xml_data)
        data = {child.tag: int(child.text) for child in root}
        return json.dumps(data)  # Повертаємо JSON

class JSONApp:
    """Новий застосунок, який працює тільки з JSON"""
    def display_data(self, data_json):
        print(f"Received JSON data: {data_json}")

# Використання адаптера (автоматична конвертація)
xml_service = XMLServiceAdapter()  # Обгортаємо старий сервіс у адаптер
json_app = JSONApp()

json_data = xml_service.get_data()  # Отримуємо вже готовий JSON
json_app.display_data(json_data)  # Все працює автоматично
