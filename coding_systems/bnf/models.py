from django.db import models


class Chapter(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    name = models.CharField(max_length=100)


class Section(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    name = models.CharField(max_length=100)


class Paragraph(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    name = models.CharField(max_length=100)


class Subparagraph(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    name = models.CharField(max_length=100)


class ChemicalSubstance(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    name = models.CharField(max_length=100)


class Product(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    name = models.CharField(max_length=100)


class Presentation(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    name = models.CharField(max_length=100)
