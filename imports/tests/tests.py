from django.test import TestCase
from imports.models import Import, Citizen

from imports.dto import CitizenDTOEncoder
from imports.tests.generator import *
import json
import numpy


class TestImports(TestCase):
    url = '/imports'

    def post(self, citizen):
        citizens = {'citizens': [citizen] if type(citizen) is not list else citizen}
        data = json.dumps(citizens, cls=CitizenDTOEncoder, ensure_ascii=False).encode('utf8')
        return self.client.generic('POST', self.url, data, content_type='application/json')

    def test_trailing_slash(self):
        response = self.client.post(self.url + '/', data={'some_data': 'some_data'}, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_bad_data(self):
        response = self.client.post(self.url, data={'some_data': 'some_data'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url, data={'citizens': {}}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.name = None
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.birth_date = citizen.birth_date.replace('.', '/')
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.appartement = 'some'
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.name = 1555
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.gender = 'fmale'
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.birth_date = '12.12.2019'
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.relatives = [1000000]
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen(-1)
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        del citizen.town
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizen = generate_one_citizen()
        citizen.relatives = {'id': citizen.citizen_id}
        response = self.post(citizen)
        self.assertEqual(response.status_code, 400)

        citizens = generate_citizens(2, provide_relatives=False)
        citizens[0].relatives = [2]
        response = self.post(citizens)
        self.assertEqual(response.status_code, 400)

        citizens = generate_citizens(3, provide_relatives=False)
        citizens[0].relatives = [2, 3]
        citizens[1].relatives = [3]
        citizens[2].relatives = [1, 2]
        response = self.post(citizens)
        self.assertEqual(response.status_code, 400)

    def test_no_citizen(self):
        response = self.post([])
        self.assertEqual(response.status_code, 201)
        import_id = json.loads(response.content)['data']['import_id']
        self.assertFalse(Citizen.objects.filter(import_id=import_id).exists())

    def test_add_one_citizen(self):
        citizen = generate_one_citizen()
        response = self.post(citizen)
        self.assertEqual(response.status_code, 201)
        import_id = json.loads(response.content)['data']['import_id']
        database_citizen = Citizen.objects.filter(import_id=import_id)
        self.assertEqual(database_citizen.count(), 1)
        database_citizen = CitizenDTO(database_citizen[0])
        self.assertEqual(database_citizen.citizen_id, citizen.citizen_id)
        self.assertEqual(database_citizen.name, citizen.name)
        self.assertEqual(database_citizen.town, citizen.town)
        self.assertEqual(database_citizen.appartement, citizen.appartement)
        self.assertEqual(database_citizen.street, citizen.street)
        self.assertEqual(database_citizen.building, citizen.building)
        self.assertEqual(database_citizen.gender, citizen.gender)
        self.assertEqual(database_citizen.birth_date, citizen.birth_date)
        self.assertEqual(len(database_citizen.relatives), 0)

    def test_add_many_citizens(self):
        citizens = generate_citizens(6, provide_relatives=False)
        citizens[0].relatives = [2, 3, 4]
        citizens[1].relatives = [1]
        citizens[2].relatives = [1]
        citizens[3].relatives = [1, 4]
        citizens[4].relatives = [5]
        citizens[5].relatives = []
        response = self.post(citizens)
        self.assertEqual(response.status_code, 201)
        import_id = json.loads(response.content)['data']['import_id']
        database_citizens = Citizen.objects.filter(import_id=import_id)
        self.assertEqual(database_citizens.count(), 6)
        for db_cit in database_citizens.all():
            self.assertEqual(db_cit.citizen_id, citizens[db_cit.citizen_id - 1].citizen_id)
            self.assertEqual(db_cit.relatives.count(), len(citizens[db_cit.citizen_id - 1].relatives))
            for db_rel in db_cit.relatives.all():
                self.assertTrue(db_rel.citizen_id in citizens[db_cit.citizen_id - 1].relatives)

    def test_add_max_citizens(self):
        citizens = generate_citizens(10000)
        post_data = {'citizens': citizens}
        data = json.dumps(post_data, cls=CitizenDTOEncoder, ensure_ascii=False).encode('utf8')
        s = datetime.datetime.now()
        response = self.client.generic('POST', self.url, data, content_type='application/json')
        e = datetime.datetime.now()
        self.assertEqual(response.status_code, 201)
        self.assertLess((e - s).total_seconds(), 5)
        import_id = json.loads(response.content)['data']['import_id']
        database_citizens = Citizen.objects.filter(import_id=import_id).all()
        self.assertEqual(len(database_citizens), 10000)
        for db_cit in database_citizens.all():
            self.assertEqual(db_cit.citizen_id, citizens[db_cit.citizen_id - 1].citizen_id)
            self.assertEqual(db_cit.town, citizens[db_cit.citizen_id - 1].town)
            self.assertEqual(db_cit.street, citizens[db_cit.citizen_id - 1].street)
            self.assertEqual(db_cit.building, citizens[db_cit.citizen_id - 1].building)
            self.assertEqual(db_cit.appartement, citizens[db_cit.citizen_id - 1].appartement)
            self.assertEqual(db_cit.name, citizens[db_cit.citizen_id - 1].name)
            self.assertEqual(db_cit.gender, citizens[db_cit.citizen_id - 1].gender)
            self.assertEqual(db_cit.birth_date.strftime('%d.%m.%Y'), citizens[db_cit.citizen_id - 1].birth_date)
            db_cit_relatives = db_cit.relatives.all()
            self.assertEqual(len(db_cit_relatives), len(citizens[db_cit.citizen_id - 1].relatives))
            for db_rel in db_cit_relatives:
                self.assertTrue(db_rel.citizen_id in citizens[db_cit.citizen_id - 1].relatives)
        print("Add - {}".format((e-s).total_seconds()))



class TestChangeCitizen(TestCase):
    url = "/imports/{:n}/citizens/{:n}"

    def test_incorrect_path_params(self):
        data = {"name": "Новое имя"}
        response = self.client.patch(self.url.format(1, 1), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)

        import_obj = Import()
        Import.save(import_obj)
        response = self.client.patch(self.url.format(import_obj.import_id, 1), json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_bad_data(self):
        data = {"name": "Новое Имя",
                "birth_date": "01.01.2019"}

        data.update({"citizen_id": 1})
        response = self.client.patch(self.url.format(0, 0), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data = {"name": 1,
                "birth_date": "01.01.2019"}
        response = self.client.patch(self.url.format(0, 0), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data = {"name": "New name",
                "appartement":"1"}
        response = self.client.patch(self.url.format(0, 0), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data = {"name": "Новое имя",
                "birth_date": "01-01-2019"}
        response = self.client.patch(self.url.format(0, 0), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data = {"name": "Новое имя",
                "birth_date": "01-01-2019"}
        data.update({"town": None})
        response = self.client.patch(self.url.format(0, 0), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data = {}
        response = self.client.patch(self.url.format(0, 0), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        import_obj = Import()
        Import.save(import_obj)
        citizen = generate_one_citizen()
        db_citizen = Citizen(import_id=import_obj,
                             citizen_id=citizen.citizen_id,
                             town=citizen.town,
                             street=citizen.street,
                             appartement=citizen.appartement,
                             name=citizen.name,
                             birth_date="1955-11-29",
                             gender=citizen.gender,
                             building=citizen.building)
        Citizen.save(db_citizen)
        data = {"name": "Новое имя", "relatives": [1000000]}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizen.citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 404)

        data = {"birth_date": "12.12.2019"}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizen.citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data = {"gender": "transgender"}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizen.citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_change_info_citizen(self):
        import_obj = Import()
        Import.save(import_obj)
        citizen = generate_one_citizen()
        db_citizen = Citizen(import_id=import_obj,
                             citizen_id=citizen.citizen_id,
                             town=citizen.town,
                             street=citizen.street,
                             appartement=citizen.appartement,
                             name=citizen.name,
                             birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                             gender=citizen.gender,
                             building=citizen.building)
        Citizen.save(db_citizen)
        data = {"name": "Новое имя"}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizen.citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_citizen = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(response_citizen['citizen_id'], db_citizen.citizen_id)
        self.assertEqual(response_citizen['town'], db_citizen.town)
        self.assertEqual(response_citizen['birth_date'], citizen.birth_date)
        self.assertEqual(response_citizen['name'], data['name'])

        data = {"name": "Другое новое имя",
                "town": "Новый город",
                "street": "Ну совсем другая",
                "building": "New building",
                "appartement": 100000,
                "birth_date": "12.01.2019",
                "gender": "male",
                }
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizen.citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_citizen = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(response_citizen['citizen_id'], db_citizen.citizen_id)
        self.assertEqual(response_citizen['town'], data['town'])
        self.assertEqual(response_citizen['birth_date'], data['birth_date'])
        self.assertEqual(response_citizen['name'], data['name'])
        self.assertEqual(response_citizen['gender'], data['gender'])
        self.assertEqual(response_citizen['appartement'], data['appartement'])
        self.assertEqual(response_citizen['building'], data['building'])
        self.assertEqual(response_citizen['street'], data['street'])

    def test_change_relatives_citizen_add(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(3, provide_relatives=False)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        db_citizens[0].relatives.add(db_citizens[1])
        data = {"name": "Новое имя", "town": "Переехала", "relatives": [1]}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizens[2].citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_citizen = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(response_citizen['name'], data['name'])
        self.assertEqual(response_citizen['town'], data['town'])
        self.assertEqual(response_citizen['street'], db_citizens[2].street)
        self.assertEqual(response_citizen['relatives'], [1])
        fcitizen = Citizen.objects.get(id=db_citizens[0].id)
        fcitizen_relatives = [rel.citizen_id for rel in fcitizen.relatives.all()]
        self.assertEqual(set(fcitizen_relatives), {2, 3})
        scitizen = Citizen.objects.get(id=db_citizens[1].id)
        scitizen_relatives = [rel.citizen_id for rel in scitizen.relatives.all()]
        self.assertEqual(scitizen_relatives, [1])

    def test_change_relatives_citizen_delete(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(3, provide_relatives=False)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        db_citizens[0].relatives.set(db_citizens[1:])
        data = {"relatives": []}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizens[0].citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_citizen = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(response_citizen['citizen_id'], db_citizens[0].citizen_id)
        self.assertEqual(response_citizen['relatives'], data["relatives"])
        citizen2 = Citizen.objects.get(id=db_citizens[1].id)
        citizen3 = Citizen.objects.get(id=db_citizens[2].id)
        self.assertEqual(citizen2.relatives.count(), 0)
        self.assertEqual(citizen3.relatives.count(), 0)

    def test_change_relatives_citizen_mix(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(6, provide_relatives=False)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        db_citizens[0].relatives.set([db_citizens[1], db_citizens[3]])
        db_citizens[1].relatives.add(db_citizens[3])
        db_citizens[4].relatives.set([db_citizens[5], db_citizens[2]])
        db_citizens[5].relatives.add(db_citizens[2])

        data = {"relatives": [1, 5]}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizens[2].citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_citizen = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(response_citizen['citizen_id'], db_citizens[2].citizen_id)
        self.assertEqual(set(response_citizen['relatives']), set(data["relatives"]))

        data = {"relatives": [2, 6]}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizens[3].citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')

        data = {"relatives": [2, 6]}
        response = self.client.patch(self.url.format(import_obj.import_id, db_citizens[3].citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_citizen = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(response_citizen['citizen_id'], db_citizens[3].citizen_id)
        self.assertEqual(set(response_citizen['relatives']), set(data["relatives"]))
        citizen1 = Citizen.objects.get(id=db_citizens[0].id)
        citizen_relatives1 = [rel.citizen_id for rel in citizen1.relatives.all()]
        self.assertEqual(set(citizen_relatives1), {2, 3})
        citizen2 = Citizen.objects.get(id=db_citizens[1].id)
        citizen_relatives2 = [rel.citizen_id for rel in citizen2.relatives.all()]
        self.assertEqual(set(citizen_relatives2), {1, 4})

        citizen5 = Citizen.objects.get(id=db_citizens[4].id)
        citizen_relatives5 = [rel.citizen_id for rel in citizen5.relatives.all()]
        self.assertEqual(set(citizen_relatives5), {3, 6})
        citizen6 = Citizen.objects.get(id=db_citizens[5].id)
        citizen_relatives6 = [rel.citizen_id for rel in citizen6.relatives.all()]
        self.assertEqual(set(citizen_relatives6), {4, 5})

    def test_change_relatives_citizen_max_data(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(10000)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        for citizen in gen_citizens:
            relatives = [db_citizens[cit_id - 1].id for cit_id in citizen.relatives]
            db_citizens[citizen.citizen_id - 1].relatives.set(relatives)

        for rel_id in gen_citizens[9999].relatives:
            gen_citizens[rel_id - 1].relatives.remove(gen_citizens[9999].citizen_id)

        for i in range(5000):
            gen_citizens[i].relatives.append(gen_citizens[9999].citizen_id)

        new_relatives = [i + 1 for i in range(5000)]
        data = {"name": "Больше некуда", "gender": "male", "relatives": new_relatives}
        s = datetime.datetime.now()
        response = self.client.patch(self.url.format(import_obj.import_id, gen_citizens[9999].citizen_id),
                                     json.dumps(data),
                                     content_type='application/json')
        e = datetime.datetime.now()
        self.assertEqual(response.status_code, 200)
        response_citizen = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(response_citizen['citizen_id'], 10000)
        self.assertEqual(response_citizen['name'], data['name'])
        self.assertEqual(response_citizen['gender'], data['gender'])
        self.assertEqual(response_citizen['town'], gen_citizens[9999].town)
        self.assertEqual(len(response_citizen['relatives']), 5000)
        self.assertEqual(set(response_citizen['relatives']), set(new_relatives))

        database_citizens = Citizen.objects.filter(import_id=import_obj.import_id).all()
        self.assertEqual(len(database_citizens), 10000)
        for db_cit in database_citizens.all():
            if db_cit.citizen_id == gen_citizens[9999].citizen_id:
                continue
            self.assertEqual(db_cit.citizen_id, gen_citizens[db_cit.citizen_id - 1].citizen_id)
            self.assertEqual(db_cit.town, gen_citizens[db_cit.citizen_id - 1].town)
            self.assertEqual(db_cit.street, gen_citizens[db_cit.citizen_id - 1].street)
            self.assertEqual(db_cit.building, gen_citizens[db_cit.citizen_id - 1].building)
            self.assertEqual(db_cit.appartement, gen_citizens[db_cit.citizen_id - 1].appartement)
            self.assertEqual(db_cit.name, gen_citizens[db_cit.citizen_id - 1].name)
            self.assertEqual(db_cit.gender, gen_citizens[db_cit.citizen_id - 1].gender)
            self.assertEqual(db_cit.birth_date.strftime('%d.%m.%Y'), gen_citizens[db_cit.citizen_id - 1].birth_date)
            db_cit_relatives = db_cit.relatives.all()
            self.assertEqual(len(db_cit_relatives), len(gen_citizens[db_cit.citizen_id - 1].relatives))
            for db_rel in db_cit_relatives:
                self.assertTrue(db_rel.citizen_id in gen_citizens[db_cit.citizen_id - 1].relatives)
        self.assertLess((e - s).total_seconds(), 5)
        print("Change - {}".format((e-s).total_seconds()))


class TestGetCitizens(TestCase):
    url = '/imports/{:n}/citizens'

    def test_incorrect_path_params(self):
        response = self.client.get(self.url.format(1000000))
        self.assertEqual(response.status_code, 404)

    def test_get_one_citizen(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizen = generate_one_citizen()
        db_citizen = Citizen(import_id=import_obj,
                             citizen_id=gen_citizen.citizen_id,
                             town=gen_citizen.town,
                             street=gen_citizen.street,
                             appartement=gen_citizen.appartement,
                             name=gen_citizen.name,
                             birth_date=datetime.datetime.strptime(gen_citizen.birth_date, "%d.%m.%Y"),
                             gender=gen_citizen.gender,
                             building=gen_citizen.building)
        Citizen.save(db_citizen)
        response = self.client.get(self.url.format(import_obj.import_id))
        self.assertEqual(response.status_code, 200)
        response_citizens = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(type(response_citizens), list)
        self.assertEqual(len(response_citizens), 1)
        citizen = response_citizens[0]
        self.assertEqual(citizen['citizen_id'], db_citizen.citizen_id)
        self.assertEqual(citizen['town'], db_citizen.town)
        self.assertEqual(citizen['name'], db_citizen.name)
        self.assertEqual(citizen['street'], db_citizen.street)
        self.assertEqual(citizen['building'], db_citizen.building)
        self.assertEqual(citizen['appartement'], db_citizen.appartement)
        self.assertEqual(citizen['gender'], db_citizen.gender)
        self.assertEqual(citizen['birth_date'], gen_citizen.birth_date)
        self.assertEqual(citizen['relatives'], [])

    def test_get_three_citizens(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(3, provide_relatives=False)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        db_citizens[0].relatives.set(db_citizens[1:])
        response = self.client.get(self.url.format(import_obj.import_id))
        self.assertEqual(response.status_code, 200)
        response_citizens = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(type(response_citizens), list)
        self.assertEqual(len(response_citizens), 3)
        for json_citizen in response_citizens:
            self.assertEqual(json_citizen['citizen_id'], db_citizens[json_citizen['citizen_id'] - 1].citizen_id)
            self.assertEqual(json_citizen['town'], db_citizens[json_citizen['citizen_id'] - 1].town)
            self.assertEqual(json_citizen['name'], db_citizens[json_citizen['citizen_id'] - 1].name)
            self.assertEqual(json_citizen['street'], db_citizens[json_citizen['citizen_id'] - 1].street)
            self.assertEqual(json_citizen['building'], db_citizens[json_citizen['citizen_id'] - 1].building)
            self.assertEqual(json_citizen['appartement'], db_citizens[json_citizen['citizen_id'] - 1].appartement)
            self.assertEqual(json_citizen['gender'], db_citizens[json_citizen['citizen_id'] - 1].gender)
            self.assertEqual(json_citizen['birth_date'], gen_citizens[json_citizen['citizen_id'] - 1].birth_date)
            self.assertEqual(len(json_citizen['relatives']),
                             db_citizens[json_citizen['citizen_id'] - 1].relatives.count())
            self.assertEqual(set(json_citizen['relatives']),
                             {rel.citizen_id for rel in db_citizens[json_citizen['citizen_id'] - 1].relatives.all()})

    def test_get_max_citizens(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(10000)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        for citizen in gen_citizens:
            relatives = [db_citizens[cit_id - 1].id for cit_id in citizen.relatives]
            db_citizens[citizen.citizen_id - 1].relatives.set(relatives)

        s = datetime.datetime.now()
        response = self.client.get(self.url.format(import_obj.import_id))
        e = datetime.datetime.now()
        self.assertEqual(response.status_code, 200)
        response_citizens = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(type(response_citizens), list)
        self.assertEqual(len(response_citizens), 10000)
        for response_cit in response_citizens:
            self.assertEqual(response_cit['citizen_id'], gen_citizens[response_cit['citizen_id'] - 1].citizen_id)
            self.assertEqual(response_cit['town'], gen_citizens[response_cit['citizen_id'] - 1].town)
            self.assertEqual(response_cit['street'], gen_citizens[response_cit['citizen_id'] - 1].street)
            self.assertEqual(response_cit['building'], gen_citizens[response_cit['citizen_id'] - 1].building)
            self.assertEqual(response_cit['appartement'], gen_citizens[response_cit['citizen_id'] - 1].appartement)
            self.assertEqual(response_cit['name'], gen_citizens[response_cit['citizen_id'] - 1].name)
            self.assertEqual(response_cit['gender'], gen_citizens[response_cit['citizen_id'] - 1].gender)
            self.assertEqual(response_cit['birth_date'], gen_citizens[response_cit['citizen_id'] - 1].birth_date)
            self.assertEqual(len(response_cit['relatives']), len(gen_citizens[response_cit['citizen_id'] - 1].relatives))
            self.assertEqual(set(response_cit['relatives']), set(gen_citizens[response_cit['citizen_id'] - 1].relatives))
        self.assertLess((e-s).total_seconds(), 5)
        print("Get - {}".format((e-s).total_seconds()))


class TestBirthDate(TestCase):

    url = "/imports/{:n}/citizens/birthdays"

    def test_incorrect_path_param(self):
        response = self.client.get(self.url.format(1000000))
        self.assertEqual(response.status_code, 404)

    def test_small_citizen_batch(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(3, provide_relatives=False)
        gen_citizens[0].birth_date = '26.12.1986'
        gen_citizens[1].birth_date = '17.04.1997'
        gen_citizens[2].birth_date = '23.11.1986'
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]

        Citizen.objects.bulk_create(db_citizens)
        db_citizens[0].relatives.set(db_citizens[1:])

        response = self.client.get(self.url.format(import_obj.import_id))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(type(response_data), dict)
        self.assertEqual(len(response_data.keys()), 12)
        for key, value in response_data.items():
            if key in ['1', '2', '3', '5', '6', '7', '8', '9', '10']:
                self.assertEqual(value, [])
                continue
            if key in ['4', '11']:
                self.assertEqual(value, [{"citizen_id": 1, "presents": 1}])
                continue

            self.assertEqual(len(value), 2)
            if value[0]['citizen_id'] == 2:
                self.assertEqual(value[0], {"citizen_id": 2, "presents": 1})
                self.assertEqual(value[1], {"citizen_id": 3, "presents": 1})
            else:
                self.assertEqual(value[1], {"citizen_id": 2, "presents": 1})
                self.assertEqual(value[0], {"citizen_id": 3, "presents": 1})

    def test_max_citizens_batch(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(10000)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]

        Citizen.objects.bulk_create(db_citizens)
        for citizen in gen_citizens:
            relatives = [db_citizens[cit_id - 1].id for cit_id in citizen.relatives]
            db_citizens[citizen.citizen_id - 1].relatives.set(relatives)

        answer = {str(i): [] for i in range(1,13)}
        for citizen in db_citizens:
            buf_res = [0] * 12
            for rel_id in gen_citizens[citizen.citizen_id - 1].relatives:
                buf_res[db_citizens[rel_id - 1].birth_date.month - 1] += 1
            for i in range(len(buf_res)):
                if buf_res[i] != 0:
                    answer[str(i + 1)].append({"citizen_id": citizen.citizen_id, "presents": buf_res[i]})

        s = datetime.datetime.now()
        response = self.client.get(self.url.format(import_obj.import_id))
        e = datetime.datetime.now()
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(type(response_data), dict)
        self.assertEqual(len(response_data.keys()), 12)
        for month, values in response_data.items():
            self.assertEqual(len(answer[month]), len(values))
            if len(values) > 0:
                for value in answer[month]:
                    self.assertTrue(value in values)

        print("Birth_Date - {}".format((e-s).total_seconds()))
        self.assertLess((e-s).total_seconds(), 5)


class TestPercentile(TestCase):

    url = "/imports/{:n}/towns/stat/percentile/age"

    def test_incorrect_path_params(self):
        response = self.client.get(self.url.format(1000000))
        self.assertEqual(response.status_code, 404)

    def test_small_citizen_batch(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(100, provide_relatives=False)
        for citizen in gen_citizens:
            citizen.town = random.choice(['Москва', 'Ташкент'])
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        ages = {'Москва': [], 'Ташкент': []}
        for citizen in db_citizens:
            today = datetime.date.today()
            ages[citizen.town].append(today.year - citizen.birth_date.year - ((today.month, today.day) < (citizen.birth_date.month, citizen.birth_date.day)))

        response = self.client.get(self.url.format(import_obj.import_id))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(type(response_data), list)
        self.assertEqual(len(response_data), 2)
        for town_info in response_data:
            self.assertEqual(round(town_info['p50'], 2), round(numpy.percentile(ages[town_info['town']], 50), 2))
            self.assertEqual(round(town_info['p75'], 2), round(numpy.percentile(ages[town_info['town']], 75), 2))
            self.assertEqual(round(town_info['p99'], 2), round(numpy.percentile(ages[town_info['town']], 99), 2))

    def test_max_citizen_batch(self):
        import_obj = Import()
        Import.save(import_obj)
        gen_citizens = generate_citizens(10000, provide_relatives=False)
        db_citizens = [Citizen(import_id=import_obj,
                               citizen_id=citizen.citizen_id,
                               town=citizen.town,
                               street=citizen.street,
                               appartement=citizen.appartement,
                               name=citizen.name,
                               birth_date=datetime.datetime.strptime(citizen.birth_date, "%d.%m.%Y"),
                               gender=citizen.gender,
                               building=citizen.building) for citizen in gen_citizens]
        Citizen.objects.bulk_create(db_citizens)
        ages = {}
        for citizen in db_citizens:
            today = datetime.date.today()
            if citizen.town in ages.keys():
                ages[citizen.town].append(today.year - citizen.birth_date.year - ((today.month, today.day) < (citizen.birth_date.month, citizen.birth_date.day)))
            else:
                ages.update({citizen.town: [today.year - citizen.birth_date.year - ((today.month, today.day) < (citizen.birth_date.month, citizen.birth_date.day))]})

        s = datetime.datetime.now()
        response = self.client.get(self.url.format(import_obj.import_id))
        e = datetime.datetime.now()
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf8'))['data']
        self.assertEqual(type(response_data), list)
        self.assertEqual(len(response_data), len(ages.keys()))
        for town_info in response_data:
            self.assertEqual(round(town_info['p50'], 2), round(numpy.percentile(ages[town_info['town']], 50), 2))
            self.assertEqual(round(town_info['p75'], 2), round(numpy.percentile(ages[town_info['town']], 75), 2))
            self.assertEqual(round(town_info['p99'], 2), round(numpy.percentile(ages[town_info['town']], 99), 2))
        print("Percentile - {}".format((e-s).total_seconds()))
        self.assertLess((e-s).total_seconds(), 5.0)
