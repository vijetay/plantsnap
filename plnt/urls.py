from django.urls import path
import plnt.views

urlpatterns = [
    path('',plnt.views.home,name = 'home'),

    path('home',plnt.views.home,name = 'home'),
    path('login/', plnt.views.login, name='login'),
    path('logout/', plnt.views.logout, name='logout'),

    path('register/', plnt.views.register, name='register'),

    path('user_home', plnt.views.user_home, name='user_home'),
    path('admin_home', plnt.views.admin_home, name='admin_home'),

    path('identify_plant_usr', plnt.views.identify_plant_usr, name='identify_plant_usr'),
    path('delete_plant_usr/<int:pk>/', plnt.views.delete_plant_usr, name='delete_plant_usr'),

    path('predict_dis_usr', plnt.views.predict_dis_usr, name='predict_dis_usr'),
    path('delete_plant_dis_usr/<int:pk>/', plnt.views.delete_plant_dis_usr, name='delete_plant_dis_usr'),

    path('plant_care_usr', plnt.views.plant_care_usr, name='plant_care_usr'),
    path('plant_care_add_usr', plnt.views.plant_care_add_usr, name='plant_care_add_usr'),
    path('plant_care_edit_usr/<int:pk>/', plnt.views.plant_care_edit_usr, name='plant_care_edit_usr'),
    path('plant_care_delete_usr/<int:pk>/', plnt.views.plant_care_delete_usr, name='plant_care_delete_usr'),

    path('plant_care_detail_usr/<int:pk>/', plnt.views.plant_care_detail_usr, name='plant_care_detail_usr'),

    path('prev_ident_usr', plnt.views.prev_ident_usr, name='prev_ident_usr'),
    path('delete_ident_usr/<int:pk>/', plnt.views.delete_ident_usr, name='delete_ident_usr'),

    path('plant_identif_adm', plnt.views.plant_identif_adm,name = 'plant_identif_adm'),
    path('plant_dis_adm',plnt.views.plant_dis_adm,name='plant_dis_adm'),

    path('users_adm', plnt.views.users_adm, name='users_adm'),
    path('toggle_user_adm/<int:uid>/', plnt.views.toggle_user_adm, name='toggle_user_adm'),
    path('delete_user_adm/<int:uid>/', plnt.views.delete_user_adm, name='delete_user_adm'),

    path("reminder_list_usr", plnt.views.reminder_list_usr, name="reminder_list_usr"),
    path("reminder_add_usr", plnt.views.reminder_add_usr, name="reminder_add_usr"),
    path("reminder_edit_usr/<int:pk>/", plnt.views.reminder_edit_usr, name="reminder_edit_usr"),
    path("reminder_delete_usr/<int:pk>/", plnt.views.reminder_delete_usr, name="reminder_delete_usr"),

    path('change_password_usr', plnt.views.change_password_usr, name='change_password_usr'),

    path("plant_chatbot_usr", plnt.views.plant_chatbot_usr, name="plant_chatbot_usr"),

    path("plant_chatbot_adm", plnt.views.plant_chatbot_adm, name="plant_chatbot_adm"),

    path('explore_plant_care/', plnt.views.explore_plant_care, name='explore_plant_care'),
    path('like/<int:pk>/', plnt.views.toggle_like, name='toggle_like'),
    path('save/<int:pk>/', plnt.views.toggle_save, name='toggle_save'),
    path('comment/<int:pk>/', plnt.views.add_comment, name='add_comment'),
    path('explore/', plnt.views.explore_plant_care, name='explore_plant_care'),
    path('saved/', plnt.views.saved_posts, name='saved_posts'),
]
