import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

PLANTNET_API_KEY = "2b10ytJBbsrYw8w5mRGqy70NXO"
ENDPOINT = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"

@csrf_exempt
def identify_plant(request):
    if request.method == "POST":
        img_file = request.FILES["image"]

        # save temporarily
        file_path = default_storage.save("temp/" + img_file.name, img_file)

        with default_storage.open(file_path, "rb") as f:
            files = {
                "images": (img_file.name, f, "image/jpeg")
            }
            data = {}

            response = requests.post(ENDPOINT, files=files, data=data)
            result = response.json()

        # parse top result
        if "results" in result and len(result["results"]) > 0:
            top_result = max(result["results"], key=lambda r: r.get("score", 0))

            species = top_result.get("species", {})
            common_names = species.get("commonNames", ["Unknown"])
            scientific = species.get("scientificName", "Unknown")
            score = round(top_result.get("score", 0), 2)

            return JsonResponse({
                "common_name": common_names[0],
                "scientific_name": scientific,
                "confidence": score,
                "raw": result
            })

        return JsonResponse({"error": "No results found"}, status=404)

    return JsonResponse({"error": "POST only"}, status=400)
