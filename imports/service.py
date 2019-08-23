from imports.dto import CitizenDTO
from imports.models import Import, Citizen
from django.db import transaction, connection
from imports.exceptions import ImportNotFound, CitizenNotFound, BadRelativesGiven, RelativesNotFound, NotSymmetricalRelatives
from datetime import date
import numpy


@transaction.atomic
def handle_add_import(citizens, relatives):
    new_import = Import()
    Import.save(new_import)
    for citizen in citizens:
        citizen.import_id = new_import

    if len(citizens) > 0:
        cur = connection.cursor()
        fields = ['"{}"'.format(field.name) for field in Citizen._meta.fields][1:]
        placeholders = ",".join(['({})'.format(','.join(['%s']*len(fields)))]*len(citizens))
        sql = 'insert into {} ({}) VALUES {} RETURNING "id", "citizen_id"'.format(Citizen._meta.db_table, ','.join(fields), placeholders)
        models_values = [field_value for citizen in citizens for field_value in citizen.get_insert_values()]
        cur.execute(sql, models_values)

        db_citizen_ids_map = {citizen_id: db_cit_id for db_cit_id, citizen_id in cur.fetchall()}

        placeholders_len = 0
        models_values = []
        for citizen_id, relative in relatives.items():
            placeholders_len += len(relative)
            for rel_id in relative:
                models_values.append(db_citizen_ids_map[citizen_id])
                models_values.append(db_citizen_ids_map[rel_id])
        if placeholders_len > 0:
            placeholders = ",".join(["(%s, %s)"]*placeholders_len)
            sql = "insert into imports_citizen_relatives (from_citizen_id, to_citizen_id) VALUES {}".format(placeholders)
            cur.execute(sql, models_values)

    return {'import_id': new_import.import_id}


@transaction.atomic
def handle_change_citizen(import_id, citizen_id, new_citizen_info, new_relatives):
    if not Import.objects.filter(import_id=import_id).exists():
        raise ImportNotFound(import_id)
    try:
        citizen = Citizen.objects.get(citizen_id=citizen_id, import_id=import_id)
    except Citizen.DoesNotExist:
        raise CitizenNotFound(citizen_id)
    if new_relatives is not None:
        relative_citizens = Citizen.objects.filter(import_id=import_id, citizen_id__in=new_relatives)
        if relative_citizens.count() != len(new_relatives):
            raise RelativesNotFound()
        citizen.relatives.set(relative_citizens)

    if new_citizen_info.town:
        citizen.town = new_citizen_info.town
    if new_citizen_info.street:
        citizen.street = new_citizen_info.street
    if new_citizen_info.building:
        citizen.building = new_citizen_info.building
    if new_citizen_info.appartement is not None:
        citizen.appartement = new_citizen_info.appartement
    if new_citizen_info.name:
        citizen.name = new_citizen_info.name
    if new_citizen_info.birth_date:
        citizen.birth_date = new_citizen_info.birth_date
    if new_citizen_info.gender:
        citizen.gender = new_citizen_info.gender
    citizen.save()
    return CitizenDTO(citizen)


@transaction.atomic
def handle_get_import(import_id):
    if not Import.objects.filter(import_id=import_id).exists():
        raise ImportNotFound(import_id)
    citizens = Citizen.objects.filter(import_id_id=import_id).all()
    sql = 'select from_citizen_id, citizen_id to_id ' \
          'from imports_citizen_relatives, imports_citizen cit ' \
          'WHERE cit.id = to_citizen_id and import_id=%s'
    cur = connection.cursor()
    cur.execute(sql, [import_id])
    relative_map = {citizen.id: [] for citizen in citizens}
    for from_id, to_citizen_id in cur.fetchall():
        relative_map[from_id].append(to_citizen_id)

    return [CitizenDTO(citizen, relative_map[citizen.id]) for citizen in citizens]


@transaction.atomic
def handle_birth_days(import_id):
    if not Import.objects.filter(import_id=import_id).exists():
        raise ImportNotFound(import_id=import_id)
    citizens = Citizen.objects.filter(import_id_id=import_id).all()
    sql = 'select from_citizen_id, birth_date to_id ' \
          'from imports_citizen_relatives, imports_citizen cit ' \
          'WHERE cit.id = to_citizen_id and import_id=%s'
    cur = connection.cursor()
    cur.execute(sql, [import_id])
    result = {str(month): [] for month in range(1, 13)}
    relative_birth_date_map = {citizen.id: [] for citizen in citizens}
    for from_id, to_birth_date in cur.fetchall():
        relative_birth_date_map[from_id].append(to_birth_date)

    for citizen in citizens:
        buf_res = [0] * 12
        for relative_birth_date in relative_birth_date_map[citizen.id]:
            buf_res[relative_birth_date.month - 1] += 1
        for i in range(len(buf_res)):
            if buf_res[i] != 0:
                result[str(i + 1)].append({"citizen_id": citizen.citizen_id, "presents": buf_res[i]})
    return result


@transaction.atomic
def handle_percentile(import_id):
    if not Import.objects.filter(import_id=import_id).exists():
        raise ImportNotFound(import_id=import_id)
    citizens = Citizen.objects.filter(import_id_id=import_id).all()
    town_map = {}
    for citizen in citizens:
        if citizen.town in town_map.keys():
            town_map[citizen.town].append(calculate_age(citizen.birth_date))
        else:
            town_map.update({citizen.town: [calculate_age(citizen.birth_date)]})
    return [{"town": town,
             "p50": round(numpy.percentile(ages, 50), 2),
             "p75": round(numpy.percentile(ages, 75), 2),
             "p99": round(numpy.percentile(ages, 99), 2)
             } for town, ages in town_map.items()]


def calculate_age(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


# Собственная реализация функции расчета перцентиля,
# которая работает в 2 раза медленнее numpy.percentile (неожиданно),
# но работает корректно на массиве из целых чисел (а вот это реально неожиданно)
# оставил ее, потому что жалко, т.к. время на нее все-таки тратил
def percentile(data, k):
    data = sorted(data)
    index = (len(data) - 1) * k / 100
    if index % 1 == 0:
        return data[int(index)]
    low_index = index // 1
    fractional = round(index % 1, 2)
    return round(data[int(low_index)] + fractional * (data[int(low_index + 1)] - data[int(low_index)]), 2)
