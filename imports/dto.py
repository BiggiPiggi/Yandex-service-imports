import datetime

import imports.models
import json


class DataResponse:

    def __init__(self, data):
        self.data = data


class CitizenDTO:
    def __init__(self, citizen):
        self.citizen_id = citizen.citizen_id
        self.town = citizen.town
        self.street = citizen.street
        self.building = citizen.building
        self.appartement = citizen.appartement
        self.name = citizen.name
        self.birth_date = citizen.birth_date.strftime('%d.%m.%Y')
        self.gender = citizen.gender
        self.relatives = [c.citizen_id for c in citizen.relatives.all()]


class CitizenDTOEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CitizenDTO):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)