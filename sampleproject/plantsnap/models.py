from django.db import models
from django.conf import settings

# Use settings.AUTH_USER_MODEL string directly in ForeignKey
class Plant(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    common_name = models.CharField(max_length=255, null=True, blank=True)
    scientific_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.common_name or self.scientific_name or f"Plant {self.pk}"


class PlantImage(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to="plants/")
    confidence = models.FloatField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} - {self.plant or 'unlinked'}"


class CareSchedule(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    task = models.CharField(max_length=200)
    date = models.DateField()
    interval_days = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.task} for {self.plant}"


class GrowthRecord(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    date = models.DateField()
    height_cm = models.FloatField()

    def __str__(self):
        return f"{self.plant} - {self.height_cm}cm @ {self.date}"


class DiseaseRecord(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="diseases/")
    disease = models.CharField(max_length=255, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    advice = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.disease} ({self.confidence})"
