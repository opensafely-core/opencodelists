from django.db import models


class Chapter(models.Model):
    code = models.TextField(primary_key=True, max_length=15)
    name = models.TextField()


class Section(models.Model):
    code = models.TextField(primary_key=True, max_length=15)
    name = models.TextField()


class Paragraph(models.Model):
    code = models.TextField(primary_key=True)
    name = models.TextField()


class Subparagraph(models.Model):
    code = models.TextField(primary_key=True)
    name = models.TextField()


class ChemicalSubstance(models.Model):
    code = models.TextField(primary_key=True)
    name = models.TextField()


class Product(models.Model):
    code = models.TextField(primary_key=True)
    name = models.TextField()


class Presentation(models.Model):
    code = models.TextField(primary_key=True)
    name = models.TextField()
