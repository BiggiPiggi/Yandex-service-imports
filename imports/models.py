from django.db import models


class Import(models.Model):
    import_id = models.AutoField(primary_key=True)


class Citizen(models.Model):
    import_id = models.ForeignKey(to=Import, db_column='import_id', on_delete=models.CASCADE)
    citizen_id = models.IntegerField()
    town = models.CharField(max_length=256)
    street = models.CharField(max_length=256)
    building = models.CharField(max_length=256)
    appartement = models.IntegerField()
    name = models.CharField(max_length=256)
    birth_date = models.DateField()
    gender = models.CharField(max_length=16)

    relatives = models.ManyToManyField(to='self', symmetrical=True)

    def get_insert_values(self):
        return self.import_id.import_id, self.citizen_id, self.town, self.street, self.building, self.appartement, self.name, self.birth_date.strftime('%Y-%m-%d'), self.gender

    class Meta:
        unique_together = (('import_id', 'citizen_id'),)
