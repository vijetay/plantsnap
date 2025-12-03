import tensorflow as tf
import numpy as np
from django.http import JsonResponse
from .models import PlantImage

# load your model ONCE when server starts
MODEL = tf.keras.models.load_model("model/plant_identifier.h5")

CLASS_NAMES = ["rose", "sunflower", "tulsi", "money plant"]  # update with your own classes

def predict_image(img_path):
    img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224,224))
    arr = tf.keras.preprocessing.image.img_to_array(img)
    arr = np.expand_dims(arr, 0) / 255.0

    pred = MODEL.predict(arr)[0]
    idx = np.argmax(pred)
    return CLASS_NAMES[idx], float(pred[idx])

@csrf_exempt
def upload(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"})

    img = request.FILES.get("file")
    if not img:
        return JsonResponse({"error": "No file uploaded"})

    # Save image to database
    obj = PlantImage.objects.create(image=img)

    # run model prediction
    common_name, confidence = predict_image(obj.image.path)

    obj.common_name = common_name
    obj.scientific_name = "Unknown"
    obj.confidence = confidence
    obj.save()

    return JsonResponse({
        "results": [{
            "id": obj.id,
            "image_url": obj.image.url,
            "common_name": obj.common_name,
            "scientific_name": obj.scientific_name,
            "confidence": obj.confidence,
        }]
    })
