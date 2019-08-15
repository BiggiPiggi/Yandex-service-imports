import json
from json import JSONDecodeError

from django.core.exceptions import ValidationError
from django.http import HttpResponse, Http404, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt

from imports.dto import DataResponse, CitizenDTOEncoder
from imports.service import *
import logging
import datetime
logger = logging.getLogger(__name__)

date_format = '%d.%m.%Y'


@csrf_exempt
def imports(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf8'))
        except JSONDecodeError as e:
            logger.debug("Can't parse request body json. {}".format(e.msg))
            return HttpResponse(status=400)
        except Exception:
            logger.debug("Can't parse request body json.")
            return HttpResponse(status=400)
        if type(data) is not dict:
            logger.debug("Request body is not json object. {}".format(data))
            return HttpResponse(status=400)
        if 'citizens' not in data.keys():
            logger.debug("No found citizens key in incoming json. {}".format(data))
            return HttpResponse(status=400)
        data = data['citizens']
        if data is None or type(data) is not list:
            logger.debug("No citizens provided or they are not in list. {}".format(data))
            return HttpResponse(status=400)
        try:
            citizens, relative_map = validate(data=data)
        except (ValidationError, NotSymmetricalRelatives, BadRelativesGiven) as e:
            logger.debug("Validation failed. Message - {}".format(e.message))
            return HttpResponse(e.message, status=400)

        # May be handle some additional exceptions

        import_id = handle_add_import(citizens, relative_map)
        data = DataResponse(import_id)
        logger.debug("Success request processing. Import_id - {}".format(import_id['import_id']))
        return HttpResponse(json.dumps(data.__dict__), status=201)
    else:
        logger.debug("Only allowed POST Http method. Given - {}".format(request.method))
        return HttpResponseNotAllowed(permitted_methods='POST')


@csrf_exempt
def imports_change(request, import_id, citizen_id):
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
        except Exception:
            logger.debug("Can't parse request body json")
            return HttpResponse(status=400)
        if type(data) is not dict:
            logger.debug("Request body is not json object. {}".format(data))
            return HttpResponse(status=400)
        try:
            citizen, relatives = validate_citizen(data, full=False)
        except ValidationError as e:
            logger.debug("Validation failed. {}".format(e.message))
            return HttpResponse(e.message, status=400)

        try:
            response = handle_change_citizen(import_id, citizen_id, citizen, relatives)
        except (ImportNotFound, CitizenNotFound, RelativesNotFound) as e:
            logger.debug(e.message)
            return HttpResponse(e.message, status=404)
        data = DataResponse(response)
        return HttpResponse(json.dumps(data.__dict__, cls=CitizenDTOEncoder, ensure_ascii=False).encode('utf8'), status=200)
    else:
        logger.debug("Only allowed PATCH Http method. Given - {}".format(request.method))
        return HttpResponseNotAllowed(permitted_methods='PATCH')


@csrf_exempt
def imports_all(request, import_id):
    if request.method == 'GET':
        try:
            response = handle_get_import(import_id)
        except ImportNotFound as e:
            logger.debug(e.message)
            return HttpResponse("No such import found", status=404)
        data = DataResponse(response)
        return HttpResponse(json.dumps(data.__dict__, cls=CitizenDTOEncoder, ensure_ascii=False).encode('utf8'), status=200)
    else:
        logger.debug("Only allowed GET Http method. Given - {}".format(request.method))
        return HttpResponseNotAllowed(permitted_methods='GET')


@csrf_exempt
def imports_birthdays(request, import_id):
    if request.method == 'GET':
        try:
            response = handle_birth_days(import_id)
        except ImportNotFound as e:
            logger.debug(e.message)
            return HttpResponse(e.message, status=404)
        data = DataResponse(response)
        return HttpResponse(json.dumps(data.__dict__, ensure_ascii=False).encode('utf8'), status=200)
    else:
        return HttpResponseNotAllowed(permitted_methods='GET')


@csrf_exempt
def imports_percentile(request, import_id):
    if request.method == 'GET':
        try:
            response = handle_percentile(import_id)
        except ImportNotFound as e:
            logger.debug(e.message)
            return HttpResponse(e.message, status=404)
        data = DataResponse(response)
        return HttpResponse(json.dumps(data.__dict__, ensure_ascii=False).encode('utf8'), status=200)
    else:
        return HttpResponseNotAllowed(permitted_methods='GET')


def validate(data):
    relative_map = {}
    citizens = []
    for citizen in data:
        citizen, relatives = validate_citizen(citizen=citizen)
        citizens.append(citizen)
        if citizen.citizen_id not in relative_map.keys():
            relative_map.update({citizen.citizen_id: relatives})
        else:
            raise ValidationError("not unique citizen_id into one date batch")
    for citizen_id, relatives in relative_map.items():
        for rel_id in relatives:
            if rel_id not in relative_map.keys():
                raise BadRelativesGiven(citizen_id, rel_id)
            if citizen_id not in relative_map[rel_id]:
                raise NotSymmetricalRelatives(citizen_id, rel_id)

    return citizens, relative_map


def validate_citizen(citizen, full=True):
    citizen_keys = citizen.keys()
    is_there_data = False

    if 'citizen_id' in citizen_keys:
        if full:
            if not citizen['citizen_id']:
                raise ValidationError("citizen_id not specified")
            if type(citizen['citizen_id']) is int and citizen['citizen_id'] > 0:
                citizen_id = citizen['citizen_id']
            else:
                raise ValidationError("citizen_id must be positive integer")
        else:
            raise ValidationError("citizen_id must not be specified")
    elif full:
        raise ValidationError("citizen_id not specified")
    else:
        citizen_id = None

    town = check_field(citizen, 'town', full=full)
    if town:
        is_there_data = True

    street = check_field(citizen, 'street', full=full)
    if street:
        is_there_data = True

    building = check_field(citizen, 'building', full=full)
    if building:
        is_there_data = True

    appartement = check_field(citizen, 'appartement', full=full, check_int=True)
    if appartement:
        is_there_data = True

    name = check_field(citizen, 'name', full=full)
    if name:
        is_there_data = True

    birth_date = check_field(citizen, 'birth_date', full=full, is_date=True)
    if birth_date:
        is_there_data = True

    gender = check_field(citizen, 'gender', full=full)
    if gender is not None:
        if gender != 'male' and gender != 'female':
            raise ValidationError("Invalid gender - {}. Must be only 'male' or 'female'".format(gender))
        is_there_data = True

    if 'relatives' in citizen.keys():
        if citizen['relatives'] is not None:
            relatives = citizen['relatives']
            if type(relatives) is not list:
                raise ValidationError(message="relatives must be list")
            for rel_id in relatives:
                if type(rel_id) is not int:
                    raise ValidationError(message="relatives must be integers")
            if len(set(relatives)) != len(relatives):
                raise ValidationError("duplicate relatives ids given")
            is_there_data = True
        else:
            raise ValidationError("{} not specified".format('relatives'))
    elif full:
        raise ValidationError("{} not specified".format('relatives'))
    else:
        relatives = None

    if not is_there_data and not full:
        raise ValidationError(message="No one field is provided. Must be at least one")

    return (Citizen(citizen_id=citizen_id,
                    town=town,
                    street=street,
                    building=building,
                    appartement=appartement,
                    name=name,
                    birth_date=birth_date,
                    gender=gender), relatives)


def check_field(citizen, field_name, full=True, check_int=False, is_date=False):
    if field_name in citizen.keys():
        if citizen[field_name]:
            if check_int and type(citizen[field_name]) is not int:
                raise ValidationError("{} must be integer".format(field_name))
            if not check_int:
                if type(citizen[field_name]) is not str:
                    raise ValidationError("{} must be string".format(field_name))
                else:
                    if len(citizen[field_name].strip()) == 0:
                        raise ValidationError("{} must be not empty string".format(field_name))
            if is_date:
                try:
                    result = datetime.datetime.strptime(citizen[field_name], date_format)
                    if result > datetime.datetime.now():
                        raise ValidationError("Future '{}' date given".format(field_name))
                except ValueError:
                    raise ValidationError(message="{} invalid format. Must be '{}'".format(field_name, date_format))
            else:
                result = citizen[field_name]
        else:
            raise ValidationError("{} not specified".format(field_name))
    elif full:
        raise ValidationError("{} not specified".format(field_name))
    else:
        result = None
    return result
