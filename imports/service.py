from imports.dto import CitizenDTO
from imports.models import Import, Citizen
from django.db import transaction
from imports.exceptions import ImportNotFound, CitizenNotFound, BadRelativesGiven, RelativesNotFound, NotSymmetricalRelatives
from datetime import date


@transaction.atomic
def handle_add_import(citizens, relatives):
    new_import = Import()
    Import.save(new_import)
    relative_map = {}
    for citizen in citizens:
        citizen.import_id = new_import
        Citizen.save(citizen)
        relative_map.update({citizen.citizen_id: citizen.id})

    for citizen in citizens:
        for rel_id in relatives[citizen.citizen_id]:
            if citizen.citizen_id not in relatives[rel_id]:
                raise NotSymmetricalRelatives(citizen.citizen_id, rel_id)
            try:
                citizen.relatives.add(relative_map[rel_id])
            except KeyError:
                raise BadRelativesGiven(citizen.citizen_id, rel_id)

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
    if new_citizen_info.appartement:
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
    try:
        import_entity = Import.objects.get(import_id=import_id)
    except Import.DoesNotExist:
        raise ImportNotFound(import_id)
    return [CitizenDTO(citizen) for citizen in import_entity.citizen_set.all()]


@transaction.atomic
def handle_birth_days(import_id):
    try:
        import_entity = Import.objects.get(import_id=import_id)
    except Import.DoesNotExist:
        raise ImportNotFound(import_id=import_id)
    citizens = import_entity.citizen_set.all()
    result = {str(month): [] for month in range(1, 13)}
    for citizen in citizens:
        buf_res = [0] * 12
        for relative_citizen in citizen.relatives.all():
            buf_res[relative_citizen.birth_date.month - 1] += 1
        for i in range(len(buf_res)):
            if buf_res[i] != 0:
                result[str(i + 1)].append({"citizen_id": citizen.citizen_id, "presents": buf_res[i]})
    return result


@transaction.atomic
def handle_percentile(import_id):
    try:
        import_entity = Import.objects.get(import_id=import_id)
    except Import.DoesNotExist:
        raise ImportNotFound(import_id=import_id)
    citizens = import_entity.citizen_set.all()
    town_map = {}
    for citizen in citizens:
        if citizen.town in town_map.keys():
            town_map[citizen.town].append(calculate_age(citizen.birth_date))
        else:
            town_map.update({citizen.town: [calculate_age(citizen.birth_date)]})
    return [{"town": town,
             "p50": percentile(ages, 50),
             "p75": percentile(ages, 75),
             "p99": percentile(ages, 99),
             } for town, ages in town_map.items()]


def calculate_age(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


def percentile(data, k):
    data = sorted(data)
    index = (len(data) - 1) * k / 100
    if index % 1 == 0:
        return data[int(index)]
    low_index = index // 1
    fractional = round(index % 1, 2)
    return round(data[int(low_index)] + fractional * (data[int(low_index + 1)] - data[int(low_index)]), 2)
