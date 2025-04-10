# Приклад 1: API-запити (Об’єктний адаптер)

# Код без адаптера (ручне перетворення)
# Старий API (Adaptee)
class LegacyAPI:
    def get_data(self):
        # Повертає дані у старому форматі
        return {"name": "John", "surname": "Doe", "age": 30}

# Клієнтський код (новий формат очікує об'єднане ім'я)
def process_data():
    legacy = LegacyAPI()
    data = legacy.get_data()
    
    # Ручна адаптація
    full_name = f"{data['name']} {data['surname']}"
    new_data = {
        "fullName": full_name,
        "age": data["age"]
    }
    
    print("Processed data:", new_data)

process_data()



# Код з об’єктним адаптером (автоматична конвертація)
# Старий API (Adaptee)
class LegacyAPI:
    def get_data(self):
        return {"name": "John", "surname": "Doe", "age": 30}

# Новий інтерфейс (Target)
class NewAPIInterface:
    def get_formatted_data(self):
        pass

# Адаптер (Object Adapter)
class LegacyAPIAdapter(NewAPIInterface):
    def __init__(self, legacy_api):
        self.legacy_api = legacy_api

    def get_formatted_data(self):
        old_data = self.legacy_api.get_data()
        return {
            "fullName": f"{old_data['name']} {old_data['surname']}",
            "age": old_data["age"]
        }

# Клієнтський код
def process_data():
    adapter = LegacyAPIAdapter(LegacyAPI())
    new_data = adapter.get_formatted_data()
    print("Processed data:", new_data)

process_data()

