from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Registration(models.Model):
    password = models.CharField(max_length=200, null=True)
    user_role = models.CharField(max_length=200, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)


class PlantImage(models.Model):
    image = models.ImageField(null=True)
    common_name = models.CharField(max_length=200, null=True)
    scientific_name = models.CharField(max_length=200, null=True)
    confidence = models.FloatField(null=True)
    reg = models.ForeignKey(Registration, on_delete=models.CASCADE, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class TempPlantImage(models.Model):
    image = models.ImageField(null=True)
    reg = models.ForeignKey(Registration, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PlantDisease(models.Model):
    image = models.ImageField(null=True)
    disease = models.CharField(max_length=200, null=True)
    plant = models.CharField(max_length=200, null=True)
    reg = models.ForeignKey(Registration, on_delete=models.CASCADE, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class PlantCare(models.Model):
    image = models.ImageField(null=True)
    common_name = models.CharField(max_length=200, null=True)
    scientific_name = models.CharField(max_length=200, null=True)
    description = models.TextField(max_length=600, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    care_details = models.JSONField(null=True, blank=True)
    reg = models.ForeignKey(Registration, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.common_name or str(self.id)


class PlantProperties(models.Model):
    property = models.CharField(max_length=200, null=True)
    prop_care = models.ForeignKey(PlantCare, on_delete=models.CASCADE, related_name='properties', null=True)

    def __str__(self):
        return self.property


'''class Reminder(models.Model):
    title = models.CharField(max_length=100, null=True)
    description = models.TextField(blank=True, null=True)
    reminder_date = models.DateField(null=True)
    reg = models.ForeignKey(Registration,on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.title and self.reminder_date:
            return f"{self.title} - {self.reminder_date}"
'''

# ======================
# SOCIAL FEATURES
# ======================

class PlantCareLike(models.Model):
    care = models.ForeignKey(PlantCare, on_delete=models.CASCADE, related_name="likes")
    reg = models.ForeignKey(Registration, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('care', 'reg')


class PlantCareComment(models.Model):
    care = models.ForeignKey(PlantCare, on_delete=models.CASCADE, related_name="comments")
    reg = models.ForeignKey(Registration, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class PlantCareSave(models.Model):
    care = models.ForeignKey(
        PlantCare,
        on_delete=models.CASCADE,
        related_name="saves"
    )
    reg = models.ForeignKey(Registration, on_delete=models.CASCADE)



from django.utils import timezone

class Reminder(models.Model):
    reg = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    title = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    reminder_datetime = models.DateTimeField(
        default=timezone.now
    )

    email_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or "Reminder"
