class ImportNotFound(Exception):

    def __init__(self, import_id):
        self.message = "Cannot find import with id - {}".format(import_id)


class CitizenNotFound(Exception):

    def __init__(self, citizen_id):
        self.message = "Cannot find citizen with id - {}".format(citizen_id)


class BadRelativesGiven(Exception):

    def __init__(self, citizen_id, rel_id):
        self.message = "Bad relatives for citizen with id - {}. Not found citizen id - {}".format(citizen_id, rel_id)


class RelativesNotFound(Exception):

    def __init__(self):
        self.message = "Cannot find some citizens"


class NotSymmetricalRelatives(Exception):

    def __init__(self, first_citizen_id, second_citizen_id):
        self.message = "Not symmetrical relatives given. {0} citizen has relative {1} " \
                       "citizen. But {1} citizen has not relative {0} " \
                       "citizen".format(first_citizen_id, second_citizen_id)