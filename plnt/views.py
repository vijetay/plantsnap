from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from . models import *
from django.contrib.auth.models import User, auth
from django.http import HttpResponse, JsonResponse
import requests
from django.db.models import Q
from datetime import datetime, timedelta, date
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import cv2, os
import numpy as np
from .plant_care_data import PLANT_CARE_DATA
import base64
#from tensorflow.keras.models import load_model

model1 = None

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    'plnt',
    'plants_dis.h5'
)

def get_model():
    global model1
    if model1 is None:
        model1 = load_model(MODEL_PATH, compile=False)
    return model1


def home(request):
    return render(request, "home.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = auth.authenticate(request, username=username, password=password)
        if user is None:
            try:
                blocked_user = User.objects.get(username=username)
                if not blocked_user.is_active:
                    messages.error(
                        request,
                        "Your account has been blocked. Please contact the administrator."
                    )
                else:
                    messages.error(request, "Invalid username or password")
            except User.DoesNotExist:
                messages.error(request, "Invalid username or password")

            return redirect("login")
        if user is not None:
            if not user.is_active:
                messages.error(request,"Your account has been blocked. Please contact the administrator.")
                return redirect("login")
            kmk = Registration.objects.get(user=user)
            auth.login(request, user)
            if kmk.user_role == 'admin':
                request.session['logg'] = int(kmk.id)
                return redirect("admin_home")
            elif kmk.user_role == 'user':
                request.session['logg'] = int(kmk.id)
                tmp = TempPlantImage.objects.filter(reg = kmk)
                if tmp:
                    for t in tmp:
                        t.image.delete(save=True)
                        t.delete()
                return redirect("user_home")
            else:
                messages.error(request, "Invalid username or password")
                return redirect("login")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")
    return render(request, "login.html")


def register(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Check passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        # Check username exists
        if User.objects.filter(username = username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        # Check email exists
        if User.objects.filter(email = email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        # Create user
        user = User.objects.create_user(
            username = username,
            email = email,
            password = password1
        )
        user.save()

        t = Registration()
        t.user_role = 'user'
        t.user = user
        t.password = password1
        t.save()

        messages.success(request, "Registration successful. Please login.")
        return redirect("home")
    else:
        return render(request, 'register.html')


@login_required(login_url='home')
def change_password_usr(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        user = request.user
        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return redirect("change_password_usr")
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("change_password_usr")
        user.set_password(new_password)
        user.save()
        hyh = Registration.objects.get(user = user)
        hyh.password = new_password
        hyh.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password changed successfully.")
        return redirect("user_home")
    return render(request, "change_password_usr.html")



@login_required(login_url='home')
def user_home(request):
    now = timezone.now()
    alert_datetime = now + timedelta(days=2)

    reminders = Reminder.objects.filter(
        reg_id=request.session['logg'],
        reminder_datetime__gte=now,
        reminder_datetime__lte=alert_datetime
    ).order_by("reminder_datetime")

    return render(request, "user_home.html", {"reminders": reminders})



@login_required(login_url='home')
def identify_plant_usr(request):
    kmk = Registration.objects.get(id=request.session['logg'])

    context = {
        'temp_image': None,
        'common_name': None,
        'scientific_name': None,
        'confidence': None,
        'error': None
    }

    # 🔍 IDENTIFY
    if request.method == 'POST' and request.POST.get('action') == 'identify':
        image = request.FILES.get('plant_image')

        if image:
            temp = TempPlantImage.objects.create(image=image, reg = kmk)

            API_KEY = "2b10ytJBbsrYw8w5mRGqy70NXO"
            endpoint = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"

            try:
                with open(temp.image.path, 'rb') as f:
                    response = requests.post(
                        endpoint,
                        files={'images': f},
                        timeout=30
                    )
                result = response.json()

                if result.get('results'):
                    top = max(result['results'], key=lambda r: r.get('score', 0))
                    species = top.get('species', {})

                    context.update({
                        'temp_image': temp,
                        'common_name': species.get('commonNames', ['Unknown'])[0],
                        'scientific_name': species.get('scientificName', 'Unknown'),
                        'confidence': round(top.get('score', 0) * 1000, 2),
                    })
                else:
                    context['error'] = "No plant identified"

            except Exception as e:
                context['error'] = str(e)

    # 💾 SAVE
    elif request.method == 'POST' and request.POST.get('action') == 'save':
        temp_id = request.POST.get('temp_id')
        temp = TempPlantImage.objects.get(id=temp_id)

        saved = PlantImage.objects.create(
            image=temp.image,
            common_name=request.POST.get('common_name'),
            scientific_name=request.POST.get('scientific_name'),
            confidence=request.POST.get('confidence'),
            reg=kmk
        )
        tmp = TempPlantImage.objects.filter(reg=kmk)
        if tmp:
            for t in tmp:
                t.delete()

        return redirect('identify_plant_usr')

    return render(request, 'identify_plant_usr.html', context)


@login_required(login_url='home')
def delete_plant_usr(request, pk):
    image = get_object_or_404(PlantImage, pk=pk)
    if request.method == 'POST':
        image.delete()
    return redirect('identify_plant_usr')


@login_required(login_url='home')
def prev_ident_usr(request):
    user = Registration.objects.get(id=request.session['logg'])

    plants = PlantImage.objects.filter(
        reg=user
    ).order_by('-uploaded_at')

    return render(request, 'prev_ident_usr.html', {
        'plants': plants
    })


@login_required(login_url='home')
def delete_ident_usr(request, pk):
    user = Registration.objects.get(id=request.session['logg'])
    plant = get_object_or_404(
        PlantImage,
        id=pk,
        reg=user
    )
    plant.image.delete(save=True)
    plant.delete()
    return redirect('prev_ident_usr')

'''
@login_required(login_url='home')
def predict_dis_usr(request):
    saved_image = None
    disease = None
    plant = None

    if request.method == 'POST' and request.FILES.get('plant_image'):
        saved_image = PlantDisease.objects.create(
            image=request.FILES['plant_image']
        )

        img_path = saved_image.image.path
        img_arr = cv2.imread(img_path)

        if img_arr is None:
            return render(request, 'predict_dis_usr.html', {
                'error': 'Invalid image file'
            })

        img_res = cv2.resize(img_arr, (224, 224))
        img_final = img_res.reshape((1, 224, 224, 3)) / 255.0

        #y_pred = model1.predict(img_final)
        #model = get_model()
        #y_pred = model.predict(img_final)

    
        class_index = int(np.argmax(y_pred, axis=1)[0])

        disease_map = {
            0: 'Apple___Apple_scab',
            1: 'Apple___Black_rot',
            2: 'Apple___Cedar_apple_rust',
            3: 'Apple___healthy',
            4: 'Blueberry___healthy',
            5: 'Cherry_(including_sour)___Powdery_mildew',
            6: 'Cherry_(including_sour)___healthy',
            7: 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
            8: 'Corn_(maize)___Common_rust',
            9: 'Corn_(maize)___Northern_Leaf_Blight',
            10: 'Corn_(maize)___healthy',
            11: 'Grape___Black_rot',
            12: 'Grape___Esca(Black_Measles)',
            13: 'Grape___Leaf_blight(Isariopsis_Leaf_Spot)',
            14: 'Grape___healthy',
            15: 'Orange___Haunglongbing(Citrus_greening)',
            16: 'Peach___Bacterial_spot',
            17: 'Peach___healthy',
            18: 'Pepper,bell___Bacterial_spot',
            19: 'Pepper,bell___healthy',
            20: 'Potato___Early_blight',
            21: 'Potato___Late_blight',
            22: 'Potato___healthy',
            23: 'Raspberry___healthy',
            24: 'Soybean___healthy',
            25: 'Squash___Powdery_mildew',
            26: 'Strawberry___Leaf_scorch',
            27: 'Strawberry___healthy',
            28: 'Tomato___Bacterial_spot',
            29: 'Tomato___Early_blight',
            30: 'Tomato___Late_blight',
            31: 'Tomato___Leaf_Mold',
            32: 'Tomato___Septoria_leaf_spot',
            33: 'Tomato___Spider_mites Two-spotted_spider_mite',
            34: 'Tomato___Target_Spot',
            35: 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
            36: 'Tomato___Tomato_mosaic_virus',
            37: 'Tomato___healthy',
        }

        def format_disease_label(label):
            plant, disease = label.split("___")
            plant = plant.replace("_", " ").replace("(including sour)", "").strip()
            disease = disease.replace("_", " ").strip()
            return plant.title(), disease.title()

        raw_label = disease_map.get(class_index, "Unknown___Unknown")
        plant, disease = format_disease_label(raw_label)

        saved_image.plant = plant
        saved_image.disease = disease
        saved_image.save()

    return render(request, 'predict_dis_usr.html', {
        'saved_image': saved_image,
        'disease': disease,
        'plant': plant
    })
'''

def image_to_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode("utf-8")


@login_required(login_url='home')
def predict_dis_usr(request):
    saved_image = None
    plant = None
    disease = None
    error = None

    if request.method == "POST" and request.FILES.get("plant_image"):
        saved_image = PlantDisease.objects.create(
            image=request.FILES["plant_image"],
            reg_id=request.session["logg"]
        )

        img_path = saved_image.image.path

        try:
            plantnet_url = (
                "https://my-api.plantnet.org/v2/identify/all"
                f"?api-key={settings.PLANTNET_API_KEY}"
            )

            with open(img_path, "rb") as img:
                plantnet_resp = requests.post(
                    plantnet_url,
                    files={"images": img},
                    timeout=30
                )

            plantnet_data = plantnet_resp.json()

            if plantnet_data.get("results"):
                best = max(
                    plantnet_data["results"],
                    key=lambda r: r.get("score", 0)
                )
                species = best.get("species", {})
                plant = species.get("commonNames", ["Unknown"])[0]
            else:
                plant = "Unknown Plant"

            img_b64 = image_to_base64(img_path)

            disease_resp = requests.post(
                "https://api.plant.id/v2/health_assessment",
                headers={
                    "Api-Key": settings.DISEASE_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "images": [img_b64],
                    "modifiers": ["crops_fast"],
                    "plant_language": "en",
                    "disease_details": ["description", "treatment"]
                },
                timeout=30
            )

            disease_data = disease_resp.json()

            diseases = disease_data.get(
                "health_assessment", {}
            ).get(
                "diseases", []
            )

            if diseases:
                disease = diseases[0]["name"]
            else:
                disease = "Healthy / No disease detected"

            # Save results
            saved_image.plant = plant
            saved_image.disease = disease
            saved_image.save()

        except Exception as e:
            error = str(e)

    return render(request, "predict_dis_usr.html", {
        "saved_image": saved_image,
        "plant": plant,
        "disease": disease,
        "error": error
    })


@login_required(login_url='home')
def delete_plant_dis_usr(request, pk):
    image = get_object_or_404(PlantDisease, pk=pk)
    if request.method == 'POST':
        image.image.delete(save=True)
        image.delete()
    return redirect('predict_dis_usr')


@login_required(login_url='home')
def plant_care_usr(request):
    cares = PlantCare.objects.filter(reg_id=request.session['logg'])

    today = date.today()

    for care in cares:
        cd = care.care_details or {}

        # 🌿 WATERING
        w = cd.get("watering", {})
        if w.get("last_watered") and w.get("frequency_days"):
            last = datetime.strptime(w["last_watered"], "%Y-%m-%d").date()
            next_date = last + timedelta(days=int(w["frequency_days"]))
            care.next_watering = next_date
            care.watering_status = (
                "overdue" if today > next_date else
                "due" if today == next_date else
                "ok"
            )
        else:
            care.next_watering = None
            care.watering_status = None

        # 🌱 FERTILIZER
        f = cd.get("fertilizer", {})
        if f.get("last_fertilized") and f.get("frequency_days"):
            last = datetime.strptime(f["last_fertilized"], "%Y-%m-%d").date()
            next_date = last + timedelta(days=int(f["frequency_days"]))
            care.next_fertilizer = next_date
            care.fertilizer_status = (
                "overdue" if today > next_date else
                "due" if today == next_date else
                "ok"
            )
        else:
            care.next_fertilizer = None
            care.fertilizer_status = None

    return render(request, "plant_care_usr.html", {"cares": cares})


@login_required(login_url='home')
def plant_care_add_usr(request):
    if request.method == "POST":
        data = {
            "light": request.POST.get("light"),
            "temperature": request.POST.get("temperature"),
            "humidity": request.POST.get("humidity"),

            "watering": {
                "frequency": request.POST.get("watering_frequency"),
                "quantity": request.POST.get("watering_quantity"),
                "method": request.POST.get("watering_method"),
                "frequency_days": int(request.POST.get("watering_frequency_days") or 0),
                "last_watered": request.POST.get("last_watered"),
            },

            "soil": {
                "type": request.POST.get("soil_type"),
                "ph": request.POST.get("ph_range"),
            },

            "fertilizer": {
                "type": request.POST.get("fertilizer_type"),
                "composition": request.POST.get("fertilizer_composition"),
                "frequency": request.POST.get("fertilizer_frequency"),
                "method": request.POST.get("fertilizer_method"),
                "frequency_days": int(request.POST.get("fertilizer_frequency_days") or 0),
                "last_fertilized": request.POST.get("last_fertilized"),
            },

            "maintenance": {
                "pruning": request.POST.get("pruning"),
                "weeding": request.POST.get("weeding"),
                "mulching": request.POST.get("mulching"),
                "support": request.POST.get("support"),
            },

            "pest_disease": request.POST.get("pest_disease"),

            "seasonal_care": {
                "summer": request.POST.get("summer_care"),
                "monsoon": request.POST.get("monsoon_care"),
                "winter": request.POST.get("winter_care"),
            },

            "precautions": request.POST.get("precautions"),
        }

        care = PlantCare.objects.create(
            common_name=request.POST.get("common_name"),
            scientific_name=request.POST.get("scientific_name"),
            description=request.POST.get("description"),
            image=request.FILES.get("image"),
            care_details=data,
            reg_id=request.session.get("logg")
        )

        for prop in request.POST.getlist("properties"):
            PlantProperties.objects.create(
                property=prop,
                prop_care=care
            )

        return redirect("plant_care_usr")

    return render(request, "plant_care_form_usr.html")


@login_required(login_url='home')
def plant_care_edit_usr(request, pk):
    care = get_object_or_404(
        PlantCare,
        pk=pk,
        reg_id=request.session['logg']
    )

    if request.method == "POST":

        care.common_name = request.POST.get("common_name")
        care.scientific_name = request.POST.get("scientific_name")
        care.description = request.POST.get("description")

        care.care_details = {
            "light": request.POST.get("light"),
            "temperature": request.POST.get("temperature"),
            "humidity": request.POST.get("humidity"),

            "watering": {
                "frequency": request.POST.get("watering_frequency"),
                "quantity": request.POST.get("watering_quantity"),
                "method": request.POST.get("watering_method"),
                "frequency_days": int(request.POST.get("watering_frequency_days") or 0),
                "last_watered": request.POST.get("last_watered"),
            },

            "soil": {
                "type": request.POST.get("soil_type"),
                "ph": request.POST.get("ph_range"),
            },

            "fertilizer": {
                "type": request.POST.get("fertilizer_type"),
                "composition": request.POST.get("fertilizer_composition"),
                "frequency": request.POST.get("fertilizer_frequency"),
                "method": request.POST.get("fertilizer_method"),
                "frequency_days": int(request.POST.get("fertilizer_frequency_days") or 0),
                "last_fertilized": request.POST.get("last_fertilized"),
            },

            "maintenance": {
                "pruning": request.POST.get("pruning"),
                "weeding": request.POST.get("weeding"),
                "mulching": request.POST.get("mulching"),
                "support": request.POST.get("support"),
            },

            "pest_disease": request.POST.get("pest_disease"),

            "seasonal_care": {
                "summer": request.POST.get("summer_care"),
                "monsoon": request.POST.get("monsoon_care"),
                "winter": request.POST.get("winter_care"),
            },

            "precautions": request.POST.get("precautions"),
        }

        if request.FILES.get("image"):
            care.image = request.FILES["image"]

        care.save()

        # 🔄 Update properties
        care.properties.all().delete()
        for prop in request.POST.getlist("properties"):
            PlantProperties.objects.create(
                property=prop,
                prop_care=care
            )

        return redirect("plant_care_usr")

    return render(request, "plant_care_form_usr.html", {"care": care})


@login_required(login_url='home')
def plant_care_delete_usr(request, pk):
    care = get_object_or_404(PlantCare, pk=pk, reg_id=request.session['logg'])
    care.image.delete(save=True)
    care.delete()
    return redirect('plant_care_usr')


@login_required(login_url='home')
def plant_care_detail_usr(request, pk):
    care = get_object_or_404(PlantCare,pk=pk,reg_id=request.session['logg'])
    return render(request, 'plant_care_detail_usr.html', {'care': care})


@login_required(login_url='home')
def admin_home(request):
    return render(request,'admin_home.html')


@login_required(login_url='home')
def plant_identif_adm(request):
    query = request.GET.get('q', '').strip()
    plants = PlantImage.objects.select_related('reg').all().order_by('-uploaded_at')
    if query:
        plants = plants.filter(
            Q(common_name__icontains=query) |
            Q(scientific_name__icontains=query) |
            Q(confidence__icontains=query) |
            Q(reg__user__username__icontains=query)
        )
    context = {
        'plants': plants,
        'query': query
    }
    return render(request, 'plant_identif_adm.html', context)


@login_required(login_url='home')
def plant_dis_adm(request):
    query = request.GET.get('q', '').strip()

    diseases = PlantDisease.objects.select_related('reg').all().order_by('-uploaded_at')

    if query:
        diseases = diseases.filter(
            Q(disease__icontains=query) | Q(reg__user__username__icontains=query)
        )

    context = {
        'diseases': diseases,
        'query': query
    }
    return render(request, 'plant_dis_adm.html', context)


@login_required(login_url='home')
def users_adm(request):
    query = request.GET.get('q', '').strip()

    users = User.objects.filter(
        is_superuser=False,
        is_staff=False
    ).exclude(
        id=request.user.id
    ).order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    return render(request, 'users_adm.html', {
        'users': users,
        'query': query
    })


@login_required(login_url='home')
def toggle_user_adm(request, uid):
    user = get_object_or_404(User, id=uid)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
    return redirect('users_adm')


@login_required(login_url='home')
def delete_user_adm(request, uid):
    user = get_object_or_404(User, id=uid)
    user.delete()
    return redirect('users_adm')


@login_required(login_url='home')
def reminder_list_usr(request):
    reminders = Reminder.objects.filter(
        reg_id=request.session['logg']
    ).order_by("reminder_datetime")
    return render(request, "reminder_list_usr.html", {"reminders": reminders})



@login_required(login_url='home')
def reminder_add_usr(request):
    if request.method == "POST":
        Reminder.objects.create(
            reg_id=request.session['logg'],
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            reminder_datetime=request.POST.get("reminder_datetime")
        )
        return redirect("reminder_list_usr")

    return render(request, "reminder_form_usr.html")



@login_required(login_url='home')
def reminder_edit_usr(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, reg_id=request.session['logg'])

    if request.method == "POST":
        reminder.title = request.POST.get("title")
        reminder.description = request.POST.get("description")
        reminder.reminder_datetime = request.POST.get("reminder_datetime")
        reminder.save()
        return redirect("reminder_list_usr")

    return render(request, "reminder_form_usr.html", {"reminder": reminder})



@login_required(login_url='home')
def reminder_delete_usr(request, pk):
    reminder = get_object_or_404(Reminder,pk=pk,reg_id=request.session['logg'])
    reminder.delete()
    return redirect("reminder_list_usr")


@csrf_exempt
def plant_chatbot_usr(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user_message = request.POST.get("message", "").strip().lower()

    if not user_message:
        return JsonResponse({"reply": "Please ask something about plants 🌱"})

    for key, plant in PLANT_CARE_DATA.items():
        if key in user_message:

            # 🌱 SOIL
            if "soil" in user_message:
                return JsonResponse({
                    "reply": f"""
                    <b>🌱 {plant['name']} – Soil</b><br>
                    <b>Soil Type:</b> {plant['soil']}
                    """
                })

            # 💧 WATER
            if "water" in user_message or "watering" in user_message:
                return JsonResponse({
                    "reply": f"""
                    <b>💧 {plant['name']} – Watering</b><br>
                    {plant['water']}
                    """
                })

            # 🌞 SUNLIGHT
            if "sun" in user_message or "sunlight" in user_message:
                return JsonResponse({
                    "reply": f"""
                    <b>🌞 {plant['name']} – Sunlight</b><br>
                    {plant['sun']}
                    """
                })

            # 🌿 FERTILIZER
            if "fertilizer" in user_message or "manure" in user_message:
                return JsonResponse({
                    "reply": f"""
                    <b>🌿 {plant['name']} – Fertilizer</b><br>
                    {plant['fertilizer']}
                    """
                })

            # 🌡 TEMPERATURE
            if "temperature" in user_message:
                return JsonResponse({
                    "reply": f"""
                    <b>🌡 {plant['name']} – Temperature</b><br>
                    {plant['temperature']}
                    """
                })

            # 💦 HUMIDITY
            if "humidity" in user_message:
                return JsonResponse({
                    "reply": f"""
                    <b>💦 {plant['name']} – Humidity</b><br>
                    {plant['humidity']}
                    """
                })

            # 🦠 DISEASE / SYMPTOMS
            if "disease" in user_message or "problem" in user_message or "symptom" in user_message:
                problems_html = "".join(
                    f"<li><b>{p['symptom']}:</b> {p['cause']}</li>"
                    for p in plant["problems_symptoms"]
                )

                return JsonResponse({
                    "reply": f"""
                    <b>🦠 {plant['name']} – Common Problems</b>
                    <ul>{problems_html}</ul>
                    """
                })

            # 🌿 DEFAULT SUMMARY
            return JsonResponse({
                "reply": f"""
                <b>🌿 {plant['name']} Plant Care</b><br>
                <b>Scientific Name:</b> {plant['scientific']}<br>
                <b>Watering:</b> {plant['water']}<br>
                <b>Sunlight:</b> {plant['sun']}<br><br>
                <i>Try asking: soil, fertilizer, disease, temperature, humidity 🌱</i>
                """
            })

    return JsonResponse({
        "reply": (
            "🌱 I couldn’t identify the plant.<br>"
            "Try: <i>blue pea soil</i>, <i>rose fertilizer</i>, <i>sunflower disease</i>"
        )
    })



@csrf_exempt
def plant_chatbot_adm(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user_message = request.POST.get("message", "").strip().lower()

    if not user_message:
        return JsonResponse({"reply": "Please ask something about plants 🌱"})

    for key, plant in PLANT_CARE_DATA.items():
        if key in user_message:
            reply = (
                f"🌿 **{plant['name']} Plant Care**\n"
                f"• **Scientific Name:** {plant['scientific']}\n"
                f"• **Watering:** {plant['water']}\n"
                f"• **Sunlight:** {plant['sun']}\n\n"
                f"Ask me about fertilizer, diseases, or pruning 🌱"
            )
            return JsonResponse({"reply": reply})

    return JsonResponse({
        "reply": (
            "🌱 I couldn’t identify that plant.\n"
            "Try asking like: *Neem plant care*, *Rose watering*, *Tulsi sunlight* 🌿"
        )
    })


def logout(request):
    auth.logout(request)
    request.session.flush()
    return redirect('home')

# ======================
# PUBLIC DETAIL VIEW
# ======================

@login_required(login_url='home')
def explore_plant_care(request):
    reg = Registration.objects.get(id=request.session['logg'])

    posts = PlantCare.objects.exclude(
        reg=reg
    ).select_related(
        'reg', 'reg__user'
    ).prefetch_related(
        'likes', 'comments', 'saves'
    ).order_by('-uploaded_at')

    return render(request, 'explore_plant_care.html', {
        'posts': posts
    })



@login_required(login_url='home')
def saved_posts(request):
    reg = Registration.objects.get(id=request.session['logg'])

    posts = PlantCare.objects.filter(
        saves__reg=reg
    ).select_related(
        'reg', 'reg__user'
    ).prefetch_related(
        'likes', 'comments', 'saves'
    )

    return render(request, 'saved_posts.html', {
        'posts': posts
    })


@login_required(login_url='home')
def toggle_save(request, pk):
    care = get_object_or_404(PlantCare, pk=pk)
    reg = Registration.objects.get(id=request.session['logg'])

    obj, created = PlantCareSave.objects.get_or_create(care=care, reg=reg)
    if not created:
        obj.delete()

    return redirect(request.META.get('HTTP_REFERER'))



@login_required(login_url='home')
def toggle_like(request, pk):
    care = get_object_or_404(PlantCare, pk=pk)
    reg = Registration.objects.get(id=request.session['logg'])

    obj, created = PlantCareLike.objects.get_or_create(care=care, reg=reg)
    if not created:
        obj.delete()

    return redirect(request.META.get('HTTP_REFERER'))



@login_required(login_url='home')
def add_comment(request, pk):
    care = get_object_or_404(PlantCare, pk=pk)
    reg = Registration.objects.get(id=request.session['logg'])

    if request.method == "POST":
        text = request.POST.get("comment")
        if text:
            PlantCareComment.objects.create(
                care=care,
                reg=reg,
                comment=text
            )

    return redirect(request.META.get('HTTP_REFERER'))





