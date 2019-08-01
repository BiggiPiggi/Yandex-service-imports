import json


class DataResponse:

    def __init__(self, data):
        self.data = data


class CitizenDTO:
    def __init__(self, citizen=None):
        self.citizen_id = citizen.citizen_id if citizen else None
        self.town = citizen.town if citizen else None
        self.street = citizen.street if citizen else None
        self.building = citizen.building if citizen else None
        self.appartement = citizen.appartement if citizen else None
        self.name = citizen.name if citizen else None
        self.birth_date = citizen.birth_date.strftime('%d.%m.%Y') if citizen else None
        self.gender = citizen.gender if citizen else None
        self.relatives = [c.citizen_id for c in citizen.relatives.all()] if citizen else None


class CitizenDTOEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CitizenDTO):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)