from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.db.models import F, Sum, Count, Avg
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
import random
import json
import time
import re
import socket
import logging
import stripe
from datetime import date, datetime

from .models import CustomUser, Hostel, Room, Allocation, StudentProfile, FeePayment, ComplaintMaintenance, Feedback, EmailOTP, RoomChangeRequest
from .forms import SignupForm, StaffSignupForm, ProfileUpdateForm, RoomChangeRequestForm, ComplaintMaintenanceForm, FeedbackForm, EventForm, UserAdminEditForm
from app2.models import DiscussionMessage, MessMenu, TodayMenu, MessRules, Form, ClaimRequest
from app2.forms import MessMenuForm, MessRulesForm, DiscussionForm

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

def login_view(request):
    # Already authenticated users should not see the login page
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.GET.get('role', '')
        
        # Check if user exists but is inactive
        try:
            potential_user = CustomUser.objects.get(email=email)
            if not potential_user.is_active and not potential_user.is_superuser:
                send_otp_email(request, email)
                request.session['pending_otp_email'] = email
                messages.warning(request, "Your account is not verified. A new verification code has been sent.")
                return redirect('verify_otp')
        except CustomUser.DoesNotExist:
            pass

        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Check role BEFORE logging in
            if role == 'staff' and not (user.is_staff or user.is_superuser):
                messages.error(request, "Staff access requires authorized credentials.")
                return redirect('/login/?role=staff')
            login(request, user)
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('index')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'Rooms_login.html')



def send_otp_email(request, email):
    otp_code = str(random.randint(100000, 999999))
    # Clear old OTPs for this email
    EmailOTP.objects.filter(email=email).delete()
    EmailOTP.objects.create(email=email, otp_code=otp_code)
    
    subject = "Verify Your CampusNest Account"
    message = f"Hello,\n\nYour Institutional Verification Code is: {otp_code}\n\nThis code will expire shortly. If you did not request this, please ignore this email."
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        messages.success(request, f'Verification code sent to {email}.')
    except Exception as e:
        # Fallback for local dev if email is not configured
        messages.info(request, f"[DEV ONLY] Verification code for {email} is: {otp_code}")
    
    return otp_code

def signup_view(request):
    # Already authenticated users should not see the signup page
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        # Extract form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        roll_number = request.POST.get('roll_number', '').strip()
        terms = request.POST.get('terms')

        # Basic validations
        if not terms:
            messages.error(request, 'You must agree to the terms and conditions.')
            return render(request, 'Rooms_signup.html', {'form': SignupForm(request.POST)})

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'Rooms_signup.html', {'form': SignupForm(request.POST)})

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'Rooms_signup.html', {'form': SignupForm(request.POST)})

        if CustomUser.objects.filter(roll_number=roll_number).exists():
            messages.error(request, 'Roll number already registered.')
            return render(request, 'Rooms_signup.html', {'form': SignupForm(request.POST)})

        # Password validation
        try:
            if len(password1) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
            if not re.search(r'[A-Z]', password1):
                raise ValidationError('Password must contain at least one uppercase letter.')
            if not re.search(r'[a-z]', password1):
                raise ValidationError('Password must contain at least one lowercase letter.')
            if not re.search(r'[0-9]', password1):
                raise ValidationError('Password must contain at least one digit.')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
                raise ValidationError('Password must contain at least one special character.')

            # Create user (signal in models.py auto-creates StudentProfile)
            with transaction.atomic():
                user = CustomUser.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password1,
                    roll_number=roll_number
                )
            # Generate and Send OTP
            send_otp_email(request, email)
            
            request.session['pending_otp_email'] = email
            return redirect('verify_otp')

        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'Rooms_signup.html', {'form': SignupForm(request.POST)})
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'Rooms_signup.html', {'form': SignupForm(request.POST)})

    # For GET request, render empty form
    form = SignupForm()
    return render(request, 'Rooms_signup.html', {'form': form})



def index(request):
    return render(request, 'Rooms_index.html',)


# views.py

@require_GET
def get_floors(request, hostel_id):
    try:
        hostel = Hostel.objects.get(id=hostel_id)
        return JsonResponse({'total_floors': hostel.total_floors})
    except Hostel.DoesNotExist:
        return JsonResponse({'error': 'Hostel not found'}, status=404)

@require_GET
def get_room_details(request):
    hostel_id = request.GET.get('hostel_id')
    floor = request.GET.get('floor')
    ac_type = request.GET.get('ac_type')
    room_id = request.GET.get('room_id')
    
    if room_id:
        try:
            room = Room.objects.get(id=room_id)
            return JsonResponse(room_to_json(room))
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)
    
    rooms = Room.objects.filter(
        hostel_id=hostel_id,
        floor=floor,
        ac_type=ac_type
    )
    
    return JsonResponse({
        'rooms': [room_to_json(room) for room in rooms]
    })

def room_to_json(room):
    return {
        'id': room.id,
        'number': room.room_number,
        'type': room.room_type,
        'ac_type': room.ac_type,
        'beds_left': room.beds_left,
        'price': str(room.price),
        'amenities': room.amenities.split(',')
    }

@csrf_exempt
@require_POST
@transaction.atomic
def book_room(request):
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        user = request.user
        
        if not user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
            
        room = Room.objects.select_for_update().get(id=room_id)
        
        if room.beds_left <= 0:
            return JsonResponse({'error': 'No beds available'}, status=400)
            
        # Create allocation
        allocation = Allocation.objects.create(
            user=user,
            room=room,
            status='pending'
        )
        
        # Update bed count atomically
        room.occupied_beds += 1
        room.save()
        
        return JsonResponse({
            'success': True,
            'redirect': reverse('post_allocation'),
            'room': room_to_json(room),
            'allocation_id': allocation.id  # Fixed: Use the created allocation instance
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@transaction.atomic
def room_allocation(request):
    # Handle POST request for room allocation
    if request.method == 'POST':
        if request.user.allocations.filter(status__in=['pending', 'confirmed']).exists():
            messages.error(request, "You already have an active room allocation!")
            return redirect('room_allocation')
        try:
            with transaction.atomic():
                # Get form data with proper validation
                hostel_id = request.POST.get('hostel')
                room_number = request.POST.get('room_number')
                student_name = request.POST.get('student_name')
                student_roll_no = request.POST.get('student_roll_no')

                if not all([hostel_id, room_number, student_name, student_roll_no]):
                    messages.error(request, "All fields are required")
                    return redirect('room_allocation')

                # Get the specific room with hostel context
                room = Room.objects.select_for_update().get(
                    hostel_id=hostel_id,
                    room_number=room_number
                )

                # Check bed availability
                if room.beds_left <= 0:
                    messages.error(request, "No beds available in this room")
                    return redirect('room_allocation')

                # Create allocation
                room_id = request.POST.get('room_id')  # Adjust based on your form
                room = Room.objects.get(id=room_id)
                Allocation.objects.create(
                    user=request.user,
                    room=room,
                    status='pending',
                )

                # Update bed count atomically
                room.occupied_beds = F('occupied_beds') + 1
                room.save(update_fields=['occupied_beds'])

                messages.success(request, 
                    f"Room {room_number} allocated successfully for {student_name}!"
                )
                return redirect('profiles')

        except Room.DoesNotExist:
            messages.error(request, "Invalid room selection")
        except Room.MultipleObjectsReturned:
            messages.error(request, "Database error: Duplicate rooms detected")
        except Exception as e:
            messages.error(request, f"Allocation failed: {str(e)}")

        return redirect('room_allocation')

    # Handle GET request for showing available rooms
    hostels = Hostel.objects.all()
    selected_hostel = request.GET.get('hostel')
    selected_floor = request.GET.get('floor')
    selected_ac_type = request.GET.get('ac_type')

    # Base query with available beds
    rooms = Room.objects.annotate(
        available_beds=F('total_beds') - F('occupied_beds')
    ).filter(available_beds__gt=0)

    # Apply filters
    if selected_hostel:
        rooms = rooms.filter(hostel_id=selected_hostel)
    if selected_floor:
        rooms = rooms.filter(floor=selected_floor)
    if selected_ac_type:
        rooms = rooms.filter(ac_type=selected_ac_type)

    # Categorize rooms
    room_types = {
        'four': '4-Sharing',
        'double': 'Double Sharing',
        'single': 'Single Seater'
    }

    categorized_rooms = {
        rt: {
            'available': rooms.filter(room_type=rt),
            'booked': Room.objects.filter(
                room_type=rt,
                total_beds=F('occupied_beds')
            )
        } for rt in room_types
    }

    return render(request, 'Rooms_room_allocation.html', {
        'hostels': hostels,
        'selected_hostel': selected_hostel,
        'selected_floor': selected_floor,
        'selected_ac_type': selected_ac_type,
        'categorized_rooms': categorized_rooms,
        'room_types': room_types
    })
@require_GET
def get_available_rooms(request):
    try:
        rooms = Room.objects.all().annotate(
            available_beds=F('total_beds') - F('occupied_beds')
        )
        
        # Apply filters
        hostel_id = request.GET.get('hostel')
        floor = request.GET.get('floor')
        ac_type = request.GET.get('ac_type')

        if hostel_id:
            rooms = rooms.filter(hostel_id=hostel_id)
        if floor:
            rooms = rooms.filter(floor=floor)
        if ac_type:
            rooms = rooms.filter(ac_type=ac_type)

        room_data = [{
            'id': room.id,
            'number': room.room_number,
            'type': room.room_type,
            'ac_type': room.ac_type,
            'beds_left': room.available_beds,
            'price': str(room.price)
        } for room in rooms]

        print(f"Returning rooms: {room_data}")  # Debug print
        return JsonResponse({'rooms': room_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
       
@login_required   
@require_GET
def get_floors(request, hostel_id):
    try:
        hostel = Hostel.objects.get(id=hostel_id)
        floors = [str(i+1) for i in range(hostel.total_floors)]
        return JsonResponse({'floors': floors})
    except Hostel.DoesNotExist:
        return JsonResponse({'error': 'Hostel not found'}, status=404)

def profiles(request):
    # Get the latest allocation for the user
    
    allocation = request.user.allocations.filter(models.Q(status='confirmed') | models.Q(status='pending')).order_by('-allocation_date').first()

    student_profile = getattr(request.user, 'student_profile', None)
    profile_completion = calculate_profile_completion(request.user, student_profile)
    stats = {
        'bookings': request.user.allocations.count(),
        'complaints': request.user.complaintmaintenance_set.count(),  # Fixed
        'payments': request.user.payments.count(),
    }
    form = ProfileUpdateForm(instance=student_profile)
    
    return render(request, 'Rooms_profile.html', {
        'form': form,
        'student_profile': student_profile,
        'allocation': allocation,
        'profile_completion': profile_completion,
        'stats': stats,
    })
def calculate_profile_completion(user, profile):
    fields = [
        user.get_full_name(),
        profile.bio if profile else None,
        profile.contact_number if profile else None,
        profile.profile_picture if profile else None,
    ]
    filled = sum(1 for field in fields if field)
    return (filled / len(fields)) * 100

# views.py (edit_profile view)

@login_required
def edit_profile(request):
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=student_profile
        )
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'contact_number': form.cleaned_data['contact_number'],
                    'bio': form.cleaned_data['bio']
                })
            messages.success(request, 'Your profile has been updated!')
            return redirect('profiles')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()  # Convert form errors to JSON
                }, status=400)
            # For non-AJAX POST, render the form with errors
            return render(request, 'Rooms_edit_profile.html', {'form': form})
    else:
        form = ProfileUpdateForm(instance=student_profile)
    
    return render(request, 'Rooms_edit_profile.html', {'form': form})
# views.py

@login_required
@csrf_exempt
def update_profile_pic(request):
    if request.method == 'POST':
        try:
            profile = request.user.student_profile
            profile.profile_picture = request.FILES.get('profile_picture')
            profile.save()
            return JsonResponse({
                'success': True,
                'new_url': profile.profile_picture.url
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



def hostel_details(request):
    hostels = Hostel.objects.all()
    return render(request, 'Rooms_hostel_details.html', {'hostels': hostels})



@login_required
def payment_page(request):
    try:
        allocation = request.user.allocations.select_related('room').latest('allocation_date')
        
        if allocation.status == 'pending':
            messages.warning(request, "Your room allocation is awaiting administrator approval. You can pay once approved.")
            return redirect('profiles')
            
        if allocation.status == 'rejected':
            messages.error(request, "Your allocation request has been rejected. Please contact the hostel office.")
            return redirect('profiles')

        if allocation.status == 'confirmed' and allocation.fee_payments.filter(status='completed').exists():
            messages.info(request, "Your payment is already completed.")
            return redirect('profiles')

        amount_due = allocation.room.price * 6

        return render(request, 'Rooms_payment_page.html', {
            'amount_due': amount_due,
            'allocation': allocation,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY
        })

    except Allocation.DoesNotExist:
        messages.error(request, 'No room allocation found. Book a room first.')
        return redirect('room_allocation')
    except Exception as e:
        logger.error(f"Payment System Error: {str(e)}", exc_info=True)
        messages.error(request, 'Payment system temporarily unavailable')
        return redirect('index')


@login_required
@csrf_exempt
def create_payment_intent(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        allocation = request.user.allocations.select_related('room').latest('allocation_date')
        amount_due = allocation.room.price * 6

        # Convert amount to smallest currency unit (e.g. paisa for INR or cents)
        # Using INR for CampusNest
        amount_in_cents = int(amount_due * 100)

        # Generate unique internal transaction ID
        transaction_id = f"TXN{int(time.time())}{random.randint(1000, 9999)}"

        # Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='inr',
            automatic_payment_methods={'enabled': True},
            metadata={
                'transaction_id': transaction_id,
                'user_id': request.user.id,
                'allocation_id': allocation.id
            }
        )

        # Create Pending Payment Record
        FeePayment.objects.create(
            user=request.user,
            allocation=allocation,
            amount=amount_due,
            transaction_id=transaction_id,
            status='pending'
        )

        return JsonResponse({
            'clientSecret': intent['client_secret'],
            'transactionId': transaction_id
        })
    except Exception as e:
        logger.error(f"Stripe intent error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=403)

@login_required
@transaction.atomic
def payment_success(request, transaction_id):
    payment = get_object_or_404(FeePayment, transaction_id=transaction_id, user=request.user)
    
    if payment.status == 'pending':
        payment.status = 'completed'
        payment.save()
        
        allocation = payment.allocation
        allocation.status = 'confirmed'
        allocation.save()

    auth_code = f"STRIPE-{random.randint(100000, 999999)}"
    return render(request, 'Rooms_payment_success.html', {
        'payment': payment,
        'virtual_account': f"VA{random.randint(10000000, 99999999)}",
        'payment_gateway': "Stripe API",
        'auth_code': auth_code,
    })

@login_required
def post_allocation(request):
    allocation = request.user.allocations.latest('allocation_date')
    return render(request, 'Rooms_post_allocation.html', {
        'allocation': allocation,
    })


@login_required
def complaint_maintenance(request):
    if request.method == 'POST':
        form = ComplaintMaintenanceForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            messages.success(request, 'Your request has been submitted!')
            return redirect('complaint_maintenance')
    else:
        form = ComplaintMaintenanceForm()
    
    requests = ComplaintMaintenance.objects.filter(user=request.user)
    return render(request, 'Rooms_complaint_and_maintenance.html', {
        'form': form,
        'requests': requests
    })

@login_required
def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('feedback')
    else:
        form = FeedbackForm()
    
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    return render(request, 'Rooms_feedback.html', {
        'form': form,
        'feedbacks': feedbacks
    })

def terms_conditions(request):
    return render(request, 'Rooms_terms_and_conditions.html')




@login_required
@transaction.atomic
def approve_allocation(request, allocation_id):
    if not request.user.is_staff:
        return redirect('index')
    
    allocation = get_object_or_404(Allocation, id=allocation_id)
    if allocation.status == 'pending':
        allocation.status = 'approved'
        allocation.save()
        messages.success(request, f"Allocation for {allocation.user.email} approved. Ready for payment.")
    
    return redirect('/dashboard/?tab=allocations')

@login_required
@transaction.atomic
def reject_allocation(request, allocation_id):
    if not request.user.is_staff:
        return redirect('index')
    
    allocation = get_object_or_404(Allocation, id=allocation_id)
    if allocation.status in ['pending', 'approved']:
        # Free up the bed
        room = allocation.room
        room.occupied_beds = F('occupied_beds') - 1
        room.save()
        
        allocation.status = 'rejected'
        allocation.save()
        messages.warning(request, f"Allocation for {allocation.user.email} rejected.")
    
    return redirect('/dashboard/?tab=allocations')


@login_required
def dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('index')
    
    active_tab = request.GET.get('tab', 'overview')
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Common statistics
    total_users = CustomUser.objects.filter(is_staff=False).count()
    available_rooms = Room.objects.exclude(total_beds__lte=F('occupied_beds')).count()
    pending_requests = ComplaintMaintenance.objects.filter(status='pending').count()
    total_revenue = FeePayment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    avg_service_rating = Feedback.objects.aggregate(Avg('service_rating'))['service_rating__avg'] or 0
    allocation_stats = Allocation.objects.values('status').annotate(count=Count('status'))
    status_counts = {item['status']: item['count'] for item in allocation_stats}
    status_counts = {item['status']: item['count'] for item in allocation_stats}
    pending_allocations = status_counts.get('pending', 0)
    approved_allocations = status_counts.get('approved', 0)
    confirmed_allocations = status_counts.get('confirmed', 0)
    cancelled_allocations = status_counts.get('cancelled', 0)
    rejected_allocations = status_counts.get('rejected', 0)
    upcoming_events = Form.objects.filter(date__gte=date.today()).count()
    occupancy_rate = Room.objects.aggregate(total_beds=Sum('total_beds'), occupied=Sum('occupied_beds'))
    occupancy_percentage = (occupancy_rate['occupied'] / occupancy_rate['total_beds'] * 100) if occupancy_rate['total_beds'] else 0
    rating_progress_width = round((avg_service_rating / 5) * 100) if avg_service_rating else 0
    recent_complaints = ComplaintMaintenance.objects.order_by('-created_at')[:5]
    recent_payments = FeePayment.objects.order_by('-payment_date')[:5]
    
    
  

    context = {
        'active_tab': active_tab,
        'search_query': search_query,
        'status_filter': status_filter,
       
        'stats': {
            'total_users': total_users,
            'available_rooms': available_rooms,
            'pending_requests': pending_requests,
            'total_revenue': total_revenue,
            'avg_service_rating': round(avg_service_rating, 1),
            'pending_allocations': pending_allocations,
            'confirmed_allocations': confirmed_allocations,
            'approved_allocations': approved_allocations,
            'rejected_allocations': rejected_allocations,
            'cancelled_allocations': cancelled_allocations,
            'upcoming_events': upcoming_events,
            'occupancy_percentage': round(occupancy_percentage, 1),
            'rating_progress_width': rating_progress_width,
        },
        'recent_complaints': recent_complaints,
        'recent_payments': recent_payments,
    }
    context['allocation_data'] = {
        'pending': pending_allocations,
        'confirmed': confirmed_allocations,
        'rejected': rejected_allocations,
    }

    if active_tab == 'mess':
        
        search_query = request.GET.get('search', '')
        day_filter = request.GET.get('day', '').capitalize()
        menus = MessMenu.objects.all()
        today_day = datetime.today().strftime("%A")
        today_menus = MessMenu.objects.filter(day=today_day)
       
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        if search_query:
            menus = menus.filter(
                models.Q(menu__icontains=search_query) |
                models.Q(day__icontains=search_query) |
                models.Q(meal_type__icontains=search_query)
            )

        if day_filter:
            menus = menus.filter(day=day_filter)

        if not menus.exists() and day_filter:
            menus = MessMenu.objects.all()
            messages.info(request, f"No menus found for {day_filter}. Showing all menus.")

        if request.method == 'POST':
            form = MessMenuForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Menu item added successfully!')
                return redirect('/dashboard/?tab=mess')
            else:
                messages.error(request, 'Error adding menu item. Please check the form.')
        else:
            form = MessMenuForm()

        context.update({
            'day': days,
            'day_filter': day_filter,
            'menus': menus,
            'today_menus': today_menus,
            'search_query': search_query,
            'days': days,
            'form': form,
        })
    
    elif active_tab == 'users':
        search_query = request.GET.get('search', '')
        users = CustomUser.objects.filter(is_staff=False)
        if search_query:
            users = users.filter(email__icontains=search_query)
        context.update({'users': users, 'search_query': search_query})
        
    elif active_tab == 'requests':
        status_filter = request.GET.get('status')
        search_query = request.GET.get('search', '')
        requests = ComplaintMaintenance.objects.all()
        if status_filter:
            requests = requests.filter(status=status_filter)
        if search_query:
            requests = requests.filter(details__icontains=search_query)
        context.update({'requests': requests, 'status_filter': status_filter, 'search_query': search_query})
        
    elif active_tab == 'allocations':
        status_filter = request.GET.get('status')
        search_query = request.GET.get('search', '')
        allocations = Allocation.objects.select_related('room__hostel')
        if status_filter:
            allocations = allocations.filter(status=status_filter)
        if search_query:
            allocations = allocations.filter(room__room_number__icontains=search_query)
        context.update({'allocations': allocations, 'status_filter': status_filter, 'search_query': search_query})
        
    
    
    
    
    
    elif active_tab == 'change_room':
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        room_change_requests = RoomChangeRequest.objects.all()
        if search_query:
            room_change_requests = room_change_requests.filter(
                models.Q(user__email__icontains=search_query) |
                models.Q(reason__icontains=search_query) |
                models.Q(current_allocation__room__room_number__icontains=search_query) |
                models.Q(requested_room__room_number__icontains=search_query)
            )
        if status_filter:
            room_change_requests = room_change_requests.filter(status=status_filter)
        context.update({
            'room_change_requests': room_change_requests,
            'search_query': search_query,
            'status_filter': status_filter,
        })
    
    elif active_tab == 'events':
        events = Form.objects.all().order_by('date')
        context['events'] = events
    
    elif active_tab == 'add_event':
        if request.method == 'POST':
            form = EventForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Event added successfully!')
                return redirect('/dashboard/?tab=events')
            else:
                messages.error(request, 'Error adding event. Please check the form.')
        else:
            form = EventForm()
        context['form'] = form
        
    elif active_tab == 'notifications':
        message_id = request.GET.get('edit')
        delete_id = request.GET.get('delete')
        
        # Handle delete
        if delete_id and request.user.is_staff:
            try:
                DiscussionMessage.objects.get(id=delete_id).delete()
                messages.success(request, "Message deleted successfully")
                return redirect('/dashboard/?tab=notifications')
            except DiscussionMessage.DoesNotExist:
                messages.error(request, "Message not found")
                return redirect('/dashboard/?tab=notifications')
        
        # Handle POST for creating or editing messages
        if request.method == 'POST':
            if 'edit_id' in request.POST:
                try:
                    instance = DiscussionMessage.objects.get(id=request.POST['edit_id'])
                    form = DiscussionForm(request.POST, instance=instance, user=request.user)
                except DiscussionMessage.DoesNotExist:
                    messages.error(request, "Message not found")
                    return redirect('/dashboard/?tab=notifications')
            else:
                form = DiscussionForm(request.POST, user=request.user)
            
            if form.is_valid():
                obj = form.save(commit=False)
                if not obj.pk:  # Only set user for new messages
                    obj.user = request.user
                obj.save()
                messages.success(request, "Message saved successfully")
                return redirect('/dashboard/?tab=notifications')
            else:
                messages.error(request, "Error saving message")
        else:
            if message_id:
                try:
                    message = DiscussionMessage.objects.get(id=message_id)
                    form = DiscussionForm(instance=message, user=request.user)
                except DiscussionMessage.DoesNotExist:
                    messages.error(request, "Message not found")
                    form = DiscussionForm(user=request.user)
            else:
                form = DiscussionForm(user=request.user)
    
        chat_messages = DiscussionMessage.objects.all().order_by('-timestamp')[:50]
        context.update({
            'chat_messages': chat_messages,
            'discussion_form': form,
            'editing_message_id': message_id
        })
    elif active_tab == 'manage_claims':
     search_query = request.GET.get('search', '')
     claims = ClaimRequest.objects.filter(is_approved=False)
     if search_query:
         claims = claims.filter(
             models.Q(item__title__icontains=search_query) |
             models.Q(item__description__icontains=search_query) |
             models.Q(message__icontains=search_query)
         )
     context.update({'claims': claims, 'search_query': search_query})

    return render(request, 'Rooms_dashboard.html', context)



def about(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    return render(request, 'Rooms_about.html', {'feedbacks': feedbacks})



def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('index')  # Replace 'index' with the name of your homepage URL pattern


#! admin



@login_required
def staff_signup_view(request):
    # Restrict access to staff users only
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('index')

    if request.method == 'POST':
        form = StaffSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_otp_email(request, user.email)
            request.session['pending_otp_email'] = user.email
            return redirect('verify_otp')
    else:
        form = StaffSignupForm()

    return render(request, 'Rooms_staff_signup.html', {'form': form})




@login_required
def user_management(request):
    """Handle user management tab"""
    if not request.user.is_staff:
        return redirect('index')
    
    search_query = request.GET.get('search', '')
    users = CustomUser.objects.filter(is_staff=False)  # Only non-staff users
    if search_query:
        users = users.filter(email__icontains=search_query)

    return render(request, 'Rooms_dashboard.html', {
        'active_tab': 'users',
        'users': users,
        'search_query': search_query,
        'users_count': users.count()
    })

@login_required
def view_requests(request):
    return redirect('/dashboard/?tab=requests')

@login_required
def view_allocations(request):
    return redirect('/dashboard/?tab=allocations')

@login_required
def view_users(request):
    return redirect('/dashboard/?tab=users')

@login_required
def edit_user(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('index')
    
    target_user = get_object_or_404(CustomUser, id=user_id)
    # Ensure profile exists
    target_profile, created = StudentProfile.objects.get_or_create(user=target_user)
    
    if request.method == 'POST':
        user_form = UserAdminEditForm(request.POST, instance=target_user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=target_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()
                messages.success(request, f"User {target_user.email} updated successfully.")
                return redirect('/dashboard/?tab=users')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserAdminEditForm(instance=target_user)
        profile_form = ProfileUpdateForm(instance=target_profile)
    
    return render(request, 'Rooms_edit_user.html', {
        'target_user': target_user,
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def delete_user(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('index')
    
    user = get_object_or_404(CustomUser, id=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot delete superuser.")
    else:
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('/dashboard/?tab=users')





@login_required
def update_event(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to edit events.")
        return redirect('index')
    
    event = get_object_or_404(Form, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('/dashboard/?tab=events')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'Rooms_admin_form.html', {'form': form, 'update': True})

@login_required
def cancel_allocation(request, allocation_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('index')
    
    allocation = get_object_or_404(Allocation, id=allocation_id)
    with transaction.atomic():
        room = allocation.room
        if allocation.status == 'confirmed':
             room.occupied_beds = max(0, room.occupied_beds - 1)
             room.save()
        allocation.status = 'rejected' 
        allocation.save()
        
    messages.success(request, "Allocation cancelled successfully.")
    return redirect('/dashboard/?tab=allocations')

@login_required
def update_complaint_status(request, request_id):
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('index')
    
    complaint = get_object_or_404(ComplaintMaintenance, id=request_id)
    new_status = request.POST.get('status', 'resolved')
    complaint.status = new_status
    complaint.save()
    
    messages.success(request, f"Complaint status updated to {new_status}.")
    return redirect('/dashboard/?tab=requests')

@login_required
def delete_event(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete events.")
        return redirect('index')
    
    event = get_object_or_404(Form, id=event_id)
    event.delete()
    messages.success(request, 'Event deleted successfully!')
    return redirect('/dashboard/?tab=events')

@login_required
def set_today_menu(request, menu_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to modify menus.")
        return redirect('index')
    
    menu = get_object_or_404(MessMenu, id=menu_id)
    TodayMenu.objects.create(
        day=menu.day,
        meal_type=menu.meal_type,
        menu=menu.menu
    )
    messages.success(request, f"{menu.meal_type} set as today's menu!")
    return redirect('/dashboard/?tab=mess')

@login_required
def update_mess_menu(request, menu_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to edit menus.")
        return redirect('index')
    
    menu = get_object_or_404(MessMenu, id=menu_id)
    
    if request.method == 'POST':
        form = MessMenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('/dashboard/?tab=mess')
        else:
            messages.error(request, 'Failed to update menu item. Please check the form.')
    else:
        form = MessMenuForm(instance=menu)
    
    return render(request, 'Rooms_admin_form.html', {
        'form': form,
        'menu': menu,
        'update': True,
        'title': 'Update Mess Menu'
    })

@login_required
def delete_mess_menu(request, menu_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to delete menus.")
        return redirect('index')
    
    menu = get_object_or_404(MessMenu, id=menu_id)
    
    if request.method == 'POST':
        try:
            menu.delete()
            messages.success(request, 'Menu item deleted successfully!')
            return redirect('/dashboard/?tab=mess')
        except Exception as e:
            messages.error(request, f'Failed to delete menu item: {str(e)}')
            return redirect('/dashboard/?tab=mess')
    
    return render(request, 'Rooms_confirm_delete.html', {
        'menu': menu,
        'title': 'Delete Mess Menu',
        'message': f'Are you sure you want to delete the {menu.meal_type} menu for {menu.day}?'
    })

def delete_notification(request, msg_id):
    message = get_object_or_404(DiscussionMessage, id=msg_id)
    if request.method == "POST":
        message.delete()
        messages.success(request, "Notification deleted successfully.")
        return redirect('admin_dashboard')
    return render(request, 'confirm_delete_notification.html', {'message': message})



@login_required
def room_change_request(request):
    if not request.user.allocations.filter(status='confirmed').exists():
        messages.error(request, "You need a confirmed room allocation to request a change.")
        return redirect('profiles')

    hostels = Hostel.objects.all()

    if request.method == 'POST':
        form = RoomChangeRequestForm(request.POST)
        requested_room_id = request.POST.get('requested_room')
        if form.is_valid() and requested_room_id:
            try:
                requested_room = Room.objects.get(id=requested_room_id)
                with transaction.atomic():
                    # Check if requested room has available beds
                    if requested_room.beds_left <= 0:
                        messages.error(request, "The selected room is no longer available.")
                        return redirect('room_change_request')

                    # Check if user already has a pending request
                    if RoomChangeRequest.objects.filter(user=request.user, status='pending').exists():
                        messages.error(request, "You already have a pending room change request.")
                        return redirect('room_change_request')

                    # Create room change request
                    room_change = form.save(commit=False)
                    room_change.user = request.user
                    room_change.current_allocation = request.user.allocations.get(status='confirmed')
                    room_change.requested_room = requested_room
                    room_change.save()
                    messages.success(request, "Room change request submitted successfully!")
                    return redirect('profiles')
            except Room.DoesNotExist:
                messages.error(request, "Invalid room selected.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = RoomChangeRequestForm()

    return render(request, 'Rooms_room_change_request.html', {
        'form': form,
        'hostels': hostels,
    })



@login_required
def update_room_change_status(request, request_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to update room change requests.")
        return redirect('index')

    room_change = get_object_or_404(RoomChangeRequest, id=request_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'approved', 'rejected']:
            with transaction.atomic():
                if new_status == 'approved':
                    current_allocation = room_change.current_allocation
                    requested_room = room_change.requested_room

                    if requested_room.beds_left <= 0:
                        messages.error(request, "Requested room is no longer available.")
                        return redirect('admin_dashboard')

                    # Update current allocation
                    current_room = current_allocation.room
                    current_room.occupied_beds -= 1
                    current_room.save()

                    # Update allocation to new room
                    current_allocation.room = requested_room
                    current_allocation.status = 'confirmed'
                    current_allocation.allocation_date = timezone.now()
                    current_allocation.save()

                    # Update new room's occupied beds
                    requested_room.occupied_beds += 1
                    requested_room.save()

                room_change.status = new_status
                room_change.save()
                messages.success(request, f"Room change request {new_status}.")
        else:
            messages.error(request, "Invalid status selected.")

    return redirect('admin_dashboard')

def verify_otp(request):
    email = request.session.get('pending_otp_email')
    if not email:
        return redirect('signup')

    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        try:
            otp_record = EmailOTP.objects.get(email=email, otp_code=otp_entered)
            if otp_record.is_expired():
                messages.error(request, 'OTP expired. Please signup again.')
                return redirect('signup')
            
            # OTP Correct. Activate User.
            user = CustomUser.objects.get(email=email)
            user.is_active = True
            user.save()
            
            login(request, user)
            otp_record.delete() # Consume OTP
            del request.session['pending_otp_email']
            messages.success(request, 'Email verified successfully! Welcome to CampusNest.')
            return redirect('index')
            
        except EmailOTP.DoesNotExist:
            messages.error(request, 'Invalid verification code.')

    return render(request, 'Rooms_verify_otp.html', {'email': email})






