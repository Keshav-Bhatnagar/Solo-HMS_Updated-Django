from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from django.conf import settings
from app2.models import MessMenu, TodayMenu
from app2 import views as app2_views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('hostel/<int:hostel_id>/floors/', views.get_floors, name='get_floors'),
    path('get_room_details/', views.get_room_details, name='get_room_details'),
    path('book_room/', views.book_room, name='book_room'),
    path('rooms/', views.room_allocation, name='room_allocation'),
    path('allocation/', views.room_allocation, name='room_allocation'),
    path('get_available_rooms/', views.get_available_rooms, name='get_available_rooms'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/update_profile_pic/', views.update_profile_pic, name='update_profile_pic'),
    path('payment/', views.payment_page, name='payment'),
    path('payment/create-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('payment/success/<str:transaction_id>/', views.payment_success, name='payment_success'),
    path('post-allocation/', views.post_allocation, name='post_allocation'),
    path('complaint/', views.complaint_maintenance, name='complaint_maintenance'),
    path('feedback/', views.feedback, name='feedback'),
    path('terms/', views.terms_conditions, name='terms_conditions'),
    path('dashboard/', views.dashboard, name='admin_dashboard'),
    path('about/', views.about, name='about'),
    path('profile/', views.profiles, name='profiles'),
    path('requests/', views.view_requests, name='view_requests'),
    path('allocations/', views.view_allocations, name='view_allocations'),
    path('allocation/approve/<int:allocation_id>/', views.approve_allocation, name='approve_allocation'),
    path('allocation/reject/<int:allocation_id>/', views.reject_allocation, name='reject_allocation'),
    path('allocation/cancel/<int:allocation_id>/', views.cancel_allocation, name='cancel_allocation'),
    
    path('user/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('staff_signup/', views.staff_signup_view, name='staff_signup'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('hosteldetails/', views.hostel_details, name='hostel_details'),
    path('users/', views.view_users, name='view_users'),
    path('events/update/<int:event_id>/', views.update_event, name='update'),
    path('events/delete/<int:event_id>/', views.delete_event, name='delete'),
    
    path('mess/set_today/<int:menu_id>/', views.set_today_menu, name='set_today_menu'),
    path('mess/update/<int:menu_id>/', views.update_mess_menu, name='update_mess_menu'),
    path('mess/delete/<int:menu_id>/', views.delete_mess_menu, name='delete_mess_menu'),
    path('notification/delete/<int:msg_id>/', views.delete_notification, name='delete_notification'),
    path('complaint/update_status/<int:request_id>/', views.update_complaint_status, name='update_complaint_status'),
    
    path('claims/manage/', app2_views.manage_claims, name='manage_claims'),
    path('claims/approve/<int:claim_id>/', app2_views.approve_claim, name='approve_claim'),
    path('room_change/request/', views.room_change_request, name='room_change_request'),
    path('room_change/update/<int:request_id>/', views.update_room_change_status, name='update_room_change_status'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)