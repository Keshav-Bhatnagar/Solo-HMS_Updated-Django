from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db.models import Q, Value, CharField
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from datetime import date
from itertools import chain
from .models import Form, MessMenu, MessRules, TodayMenu, DiscussionMessage, LostItem, FoundItem, ClaimRequest, MarketplaceItem
from .forms import MessMenuForm, DiscussionForm, LostItemForm, FoundItemForm, ClaimRequestForm

def app2index(request):
    show = Form.objects.all()
    return render(request, 'index.html', {'show': show})

def base(request):
    return render(request, 'base.html')

def admin_form(request):
    try:
        if request.method == "POST":
            name = request.POST.get("name")
            event_date = request.POST.get("date")
            time = request.POST.get("time")
            venue = request.POST.get("venue")
            description = request.POST.get('description')
            organizer = request.POST.get('organizer')

            form = Form(name=name, date=event_date, time=time, venue=venue, description=description, organizer=organizer)
            form.save()
        
        today = date.today()
        upcoming_events = Form.objects.filter(date__gte=today).order_by('date')
        past_events = Form.objects.filter(date__lt=today).order_by('-date')

    except Exception as e:
        print("Error:", e)
        upcoming_events = []
        past_events = []

    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'admin_form.html', context)

def delete(request, id):
    data = Form.objects.get(id=id) 
    data.delete()
    return redirect('admin_form')

def update(request, id):
    data = Form.objects.get(id=id)
    if request.method == "POST":
        data.name = request.POST.get("name")
        data.date = request.POST.get("date")
        data.time = request.POST.get("time")
        data.venue = request.POST.get("venue")
        data.description = request.POST.get('description')
        data.organizer = request.POST.get('organizer')
        data.save()
        return redirect('admin_form')  
    return render(request, 'update.html', {'data': data})

def events(request):
    today = date.today()
    upcoming_events = Form.objects.filter(date__gte=today).order_by('date')
    past_events = Form.objects.filter(date__lt=today).order_by('-date')
    
    featured_event = upcoming_events.first()

    context = {
        'featured_event': featured_event,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'events.html', context)

def mess(request):
    today = date.today()  # Use dynamic date
    today_day = today.strftime("%A")
    
    # Fetch or create today's menu from MessMenu
    today_menu = TodayMenu.objects.filter(day=today_day).order_by('-created_at').first()
    if not today_menu:
        mess_menu = MessMenu.objects.filter(day=today_day).first()
        if mess_menu:
            today_menu = TodayMenu.objects.create(
                day=mess_menu.day,
                meal_type=mess_menu.meal_type,
                menu=mess_menu.menu
            )
    
    # Fetch weekly menu
    menus = MessMenu.objects.all()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Handle day filter
    day_filter = request.GET.get('day', '').capitalize()
    if day_filter in days:
        menus = menus.filter(day=day_filter)
    else:
        menus = menus.filter(day=today_day)

    # Fetch mess rules
    rules = MessRules.objects.all()
    
    context = {
        'today_menu': today_menu,
        'menus': menus,
        'days': days,
        'day_filter': day_filter.lower() if day_filter else '',
        'rules': rules,
    }
    return render(request, 'mess.html', context)

def set_today_menu(request, menu_id):
    menu = get_object_or_404(MessMenu, id=menu_id)
    TodayMenu.objects.update_or_create(
        day=menu.day,
        defaults={'meal_type': menu.meal_type, 'menu': menu.menu}
    )
    messages.success(request, f"Menu set for {menu.day} as today's menu.")
    return redirect('mess')

def update_mess_menu(request, menu_id):
    menu = get_object_or_404(MessMenu, id=menu_id)
    if request.method == "POST":
        form = MessMenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu updated successfully.")
            return redirect('mess')
    else:
        form = MessMenuForm(instance=menu)
    return render(request, 'update_mess_menu.html', {'form': form})

def delete_mess_menu(request, menu_id):
    menu = get_object_or_404(MessMenu, id=menu_id)
    menu.delete()
    messages.success(request, "Menu deleted successfully.")
    return redirect('/dashboard/?tab=mess')  # Replace 'mess' with the name of the page you're redirecting to

@login_required
def discussion_center(request):
    if request.method == 'POST':
        form = DiscussionForm(request.POST, user=request.user)
        if form.is_valid():
            DiscussionMessage.objects.create(
                user=request.user,
                message=form.cleaned_data['message'],
                is_notification=form.cleaned_data.get('is_notification', False)
            )
            return redirect('discussion_center')
    
    messages = DiscussionMessage.objects.all().order_by('-timestamp')[:50]
    return render(request, 'discussion.html', {
        'chat_messages': messages,
        'form': DiscussionForm(user=request.user)
    })

@require_POST
@login_required
def delete_notification(request, msg_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    message = get_object_or_404(DiscussionMessage, id=msg_id)
    message.delete()
    return redirect('admin_dashboard')

# Helper to check if user is staff
def is_staff(user):
    return user.is_staff

@login_required
def lost_and_found_dashboard(request):
    query_lost = request.GET.get('q_lost', '')
    category_lost = request.GET.get('category_lost', '')
    lost_items = LostItem.objects.all()
    if query_lost:
        lost_items = lost_items.filter(Q(title__icontains=query_lost) | Q(description__icontains=query_lost))
    if category_lost:
        lost_items = lost_items.filter(category=category_lost)

    query_found = request.GET.get('q_found', '')
    category_found = request.GET.get('category_found', '')
    found_items = FoundItem.objects.all()
    if query_found:
        found_items = found_items.filter(Q(title__icontains=query_found) | Q(description__icontains=query_found))
    if category_found:
        found_items = found_items.filter(category=category_found)

    recent_items = sorted(
        list(chain(
            LostItem.objects.order_by('-created_at')[:3].annotate(type=Value('lost', output_field=CharField())),
            FoundItem.objects.order_by('-created_at')[:3].annotate(type=Value('found', output_field=CharField()))
        )),
        key=lambda x: x.created_at,
        reverse=True
    )[:3]

    lost_form = LostItemForm(request.POST if 'report_lost' in request.POST else None)
    found_form = FoundItemForm(request.POST if 'report_found' in request.POST else None)

    if request.method == 'POST':
        if 'report_lost' in request.POST and lost_form.is_valid():
            lost_item = lost_form.save(commit=False)
            lost_item.user = request.user
            lost_item.save()
            messages.success(request, 'Lost item reported successfully.')
            return redirect('lost_and_found_dashboard')
        elif 'report_found' in request.POST and found_form.is_valid():
            found_item = found_form.save(commit=False)
            found_item.user = request.user
            found_item.save()
            messages.success(request, 'Found item reported successfully.')
            return redirect('lost_and_found_dashboard')
        else:
            if 'report_lost' in request.POST:
                messages.error(request, 'Please correct the errors in the lost item form.')
            elif 'report_found' in request.POST:
                messages.error(request, 'Please correct the errors in the found item form.')

    return render(request, 'lost_and_found_dashboard.html', {
        'lost_items': lost_items,
        'found_items': found_items,
        'recent_items': recent_items,
        'lost_form': lost_form,
        'found_form': found_form,
        'query_lost': query_lost,
        'query_found': query_found,
        'category_lost': category_lost,
        'category_found': category_found,
    })

@login_required
def claim_item(request, item_id):
    item = get_object_or_404(FoundItem, id=item_id)
    if item.is_claimed:
        messages.error(request, 'This item has already been claimed.')
        return redirect('lost_and_found_dashboard')
    if request.method == 'POST':
        form = ClaimRequestForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.item = item
            claim.save()
            messages.success(request, 'Claim submitted successfully.')
            return redirect('lost_and_found_dashboard')
    else:
        form = ClaimRequestForm()
    return render(request, 'claim_item.html', {'form': form, 'item': item})

@login_required
@user_passes_test(is_staff)
def manage_claims(request):
    claims = ClaimRequest.objects.filter(is_approved=False)
    return render(request, 'manage_claims.html', {'claims': claims})

@login_required
@user_passes_test(is_staff)
def approve_claim(request, claim_id):
    claim = get_object_or_404(ClaimRequest, id=claim_id)
    claim.is_approved = True
    claim.item.is_claimed = True
    claim.save()
    claim.item.save()
    messages.success(request, 'Claim approved successfully.')
    return redirect('manage_claims')

from .forms import MessRulesForm

def add_mess_rule(request):
    if request.method == 'POST':
        form = MessRulesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_mess_rule')  # Or wherever you want to redirect
    else:
        form = MessRulesForm()
    
    return render(request, 'add_mess_rule.html', {'form': form})

@login_required
def marketplace(request):
    category = request.GET.get('category', '')
    query = request.GET.get('q', '')
    
    items = MarketplaceItem.objects.filter(is_sold=False)
    
    if category:
        items = items.filter(category=category)
    if query:
        items = items.filter(Q(title__icontains=query) | Q(description__icontains=query))
        
    categories = [c[0] for c in MarketplaceItem.CATEGORY_CHOICES]
    
    return render(request, 'marketplace.html', {
        'items': items,
        'categories': categories,
        'selected_category': category,
        'query': query
    })

@login_required
def list_item(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        condition = request.POST.get('condition')
        image = request.FILES.get('image')
        
        item = MarketplaceItem.objects.create(
            seller=request.user,
            title=title,
            description=description,
            price=price,
            category=category,
            condition=condition,
            image=image
        )
        messages.success(request, 'Item listed successfully in the Institutional Marketplace.')
        return redirect('marketplace')
        
    return render(request, 'list_item.html', {
        'categories': MarketplaceItem.CATEGORY_CHOICES,
        'conditions': MarketplaceItem.CONDITION_CHOICES
    })
