from django.contrib import admin
from .models import Plant, PlantImage, CareSchedule, GrowthRecord, DiseaseRecord

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ("id", "common_name", "scientific_name", "owner", "created_at")
    search_fields = ("common_name", "scientific_name")

@admin.register(PlantImage)
class PlantImageAdmin(admin.ModelAdmin):
    list_display = ("id", "plant", "owner", "uploaded_at")

@admin.register(CareSchedule)
class CareScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "plant", "task", "date", "interval_days", "owner")

@admin.register(GrowthRecord)
class GrowthRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "plant", "date", "height_cm", "owner")

@admin.register(DiseaseRecord)
class DiseaseRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "disease", "confidence", "owner", "created_at")
