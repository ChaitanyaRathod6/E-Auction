from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import ItemForm, AuctionForm, BidForm,SellerProfileForm,BuyerProfileForm,AdminProfileForm,CategoryForm,AuctionQuickCreateForm,PaymentForm,WatchlistForm,NotificationForm,NotificationMarkReadForm,ReviewForm,DisputeForm,DisputeStatusUpdateForm,ActivityLogForm,AuctionSearchForm
from .models import Auction,Bid
from core.models import User
from django.utils import timezone
from .decorators import role_required
from django.shortcuts import get_object_or_404
from .models import Seller, Buyer, AdminProfile, Category, Item, Auction, Bid, Payment, Watchlist, Notification, Review, Dispute, ActivityLog,UserSettings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Avg, Q
from datetime import timedelta
from Dashboard.decorators import role_required
from django.contrib import messages 
from django.db.models import Sum
from django.contrib.auth import logout
import stripe
from Dashboard.emails import (
    send_bid_placed_email,
    send_outbid_email,
    send_auction_won_email,
    send_payment_received_email,
    send_auction_ended_seller_email,
)
from django.db.models import Q,Sum,Count
# Create your views here.
@login_required
@role_required(allowed_roles=['Admin'])
def AdminDashboard(request):
    from django.db.models import Sum, Count
    from datetime import timedelta
    from django.utils import timezone
    import json

    now = timezone.now()

    # Weekly GMV (last 7 days)
    weekly_gmv = []
    weekly_labels = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        total = Payment.objects.filter(
            status='COMPLETED',
            payment_date__date=day.date()
        ).aggregate(total=Sum('amount'))['total'] or 0
        weekly_gmv.append(float(total))
        weekly_labels.append(day.strftime('%a'))

    # Monthly GMV (last 6 months)
    monthly_gmv = []
    monthly_labels = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        total = Payment.objects.filter(
            status='COMPLETED',
            payment_date__gte=month_start,
            payment_date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_gmv.append(float(total))
        monthly_labels.append(month_start.strftime('%b'))

    # Volume by Category
    category_data = Category.objects.annotate(
        auction_count=Count('items__auction')
    ).values('name', 'auction_count').order_by('-auction_count')[:5]
    cat_labels = [c['name'][:8] for c in category_data]
    cat_values = [c['auction_count'] for c in category_data]
    max_cat = max(cat_values) if cat_values else 1

    total_gmv = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0
    active_auctions = Auction.objects.filter(status='ACTIVE').count()
    total_users = User.objects.count()
    open_disputes = Dispute.objects.filter(status='OPEN').count()
    total_auctions = Auction.objects.count()
    recent_activity = Notification.objects.select_related('user', 'auction').order_by('-created_at')[:5]
    recent_auctions = Auction.objects.select_related('item__category', 'item__seller__user').annotate(bid_count=Count('bids')).order_by('-created_at')[:5]
    pending_disputes = Dispute.objects.filter(status='OPEN').select_related('raised_by', 'auction__item').order_by('-created_at')[:4]

    # Top Buyers
    top_buyers = Buyer.objects.annotate(
    total_spent=Sum('payments__amount', filter=Q(payments__status='COMPLETED')),
    total_bids=Count('bids')
    ).filter(total_spent__isnull=False).order_by('-total_spent')[:5]

# Top Sellers
    top_sellers = Seller.objects.annotate(
    total_earned=Sum('items__auction__payments__amount', filter=Q(items__auction__payments__status='COMPLETED')),
    total_auctions=Count('items__auction')
    ).filter(total_earned__isnull=False).order_by('-total_earned')[:5]

# Most Active Categories
    active_categories = Category.objects.annotate(
    total_auctions=Count('items__auction'),
    total_bids=Count('items__auction__bids'),
    total_revenue=Sum('items__auction__payments__amount', filter=Q(items__auction__payments__status='COMPLETED'))
    ).order_by('-total_bids')[:5]


    context = {
        'total_gmv': total_gmv,
        'active_auctions': active_auctions,
        'total_users': total_users,
        'open_disputes': open_disputes,
        'total_auctions': total_auctions,
        'recent_activity': recent_activity,
        'recent_auctions': recent_auctions,
        'pending_disputes': pending_disputes,
        'weekly_gmv': json.dumps(weekly_gmv),
        'weekly_labels': json.dumps(weekly_labels),
        'monthly_gmv': json.dumps(monthly_gmv),
        'monthly_labels': json.dumps(monthly_labels),
        'cat_labels': json.dumps(cat_labels),
        'cat_values': json.dumps(cat_values),
        'max_cat': max_cat,
        'top_buyers': top_buyers,
        'top_sellers': top_sellers,
        'active_categories': active_categories,
    }
    return render(request, 'Dashboard/AdminDashboard.html', context)

@login_required
@role_required(allowed_roles=['Buyer'])
def BuyerDashboard(request):
    buyer = request.user.buyer

    # Won auctions that need payment
    won_unpaid = Bid.objects.filter(
    buyer=buyer,
    status='WINNING',
    auction__status='ENDED'
).exclude(
    auction__payments__buyer=buyer,
    auction__payments__status__in=['COMPLETED', 'REFUNDED', 'REFUND_REQUESTED']
).select_related('auction__item__category', 'auction__item__seller__user')

    # Active bids
    active_bids = Bid.objects.filter(
        buyer=buyer,
        auction__status='ACTIVE'
    ).select_related('auction__item__category').order_by('-bid_time')

    # Past bids
    past_bids = Bid.objects.filter(
        buyer=buyer,
        auction__status='ENDED'
    ).select_related('auction__item__category').order_by('-bid_time')[:10]

    # Live auctions
    from django.db.models import Count
    live_auctions = Auction.objects.filter(
        status='ACTIVE',
        end_time__gt=timezone.now()
    ).annotate(bid_count=Count('bids')).order_by('end_time')[:6]

    # Watchlist
    watchlist = Watchlist.objects.filter(
        buyer=buyer
    ).select_related('auction__item').order_by('-added_at')[:5]

    # Recent notifications
    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    # Recent payments
    recent_payments = Payment.objects.filter(
        buyer=buyer,
        status='COMPLETED'
    ).select_related('auction__item').order_by('-payment_date')[:3]

    # Stats
    total_bids = Bid.objects.filter(buyer=buyer).count()
    won_auctions = Bid.objects.filter(buyer=buyer, status='WINNING').count()
    total_spent = Payment.objects.filter(
        buyer=buyer, status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or 0
    watchlist_count = Watchlist.objects.filter(buyer=buyer).count()

    return render(request, 'Dashboard/BuyerDashboard.html', {
        'won_unpaid': won_unpaid,
        'active_bids': active_bids,
        'past_bids': past_bids,
        'live_auctions': live_auctions,
        'watchlist': watchlist,
        'recent_notifications': recent_notifications,
        'recent_payments': recent_payments,
        'total_bids': total_bids,
        'won_auctions': won_auctions,
        'total_spent': total_spent,
        'watchlist_count': watchlist_count,
    })

@login_required
@role_required(allowed_roles=['Seller'])
def SellerDashboard(request):
    try:
        seller = request.user.seller
    except:
        return redirect('home')

    auctions = Auction.objects.filter(
        item__seller=seller
    ).select_related('item__category').annotate(
        bid_count=Count('bids')
    ).order_by('end_time')

    live_auctions = auctions.filter(status='ACTIVE', end_time__gt=timezone.now())[:5]

    total_earnings = Payment.objects.filter(
    auction__item__seller=seller, status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or 0

    refunded_amount = Payment.objects.filter(
    auction__item__seller=seller, status='REFUNDED'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_earnings = total_earnings - refunded_amount

    # ← ADD THIS — ended auctions waiting for buyer payment
    pending_payments = Bid.objects.filter(
    auction__item__seller=seller,
    status='WINNING',
    auction__status='ENDED'
).exclude(
    auction__payments__status__in=['COMPLETED', 'REFUNDED', 'REFUND_REQUESTED']
).select_related(
    'auction__item__category',
    'buyer__user'
).order_by('-auction__end_time')

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    pending_payments_count = Payment.objects.filter(auction__item__seller=seller, status='PENDING').count()
    open_disputes_count = Dispute.objects.filter(auction__item__seller=seller, status='OPEN').count()
    unread_bids = Bid.objects.filter(auction__item__seller=seller, auction__status='ACTIVE').count()
    unread_reviews = Review.objects.filter(seller=seller, is_read=False).count() if hasattr(Review, 'is_read') else 0

    context = {
        'seller': seller,
        'live_auctions': live_auctions,
        'total_earnings': total_earnings,
        'active_auctions': auctions.filter(status='ACTIVE').count(),
        'items_sold': auctions.filter(status='ENDED').count(),
        'categories': Category.objects.all(),
        'pending_payments': pending_payments,
        'unread_notifications': unread_notifications,
        'pending_payments_count': pending_payments_count,
        'open_disputes_count': open_disputes_count,
        'unread_bids': unread_bids,
    }
    return render(request, 'Dashboard/SellerDashboard.html', context)

def  privacypolicy(request):
    return render(request,"Dashboard/privacypolicy.html")

def  termsofservice(request):
    return render(request,"Dashboard/termsofservice.html")

def ContactUs(request): 
    return render(request,"Dashboard/contactus.html")

def HelpCenter(request):
    return render(request,"Dashboard/helpcenter.html")

def Security(request):
    return render(request,"Dashboard/security.html")  
  
def Community(request):
    return render(request,"Dashboard/community.html") 
   
def Support(request):
    return render(request,"Dashboard/support.html")  

def   AboutUs(request):
    return render(request,"Dashboard/aboutus.html")

def Careers(request):
    return render(request,"Dashboard/careers.html")

def HowItWorks(request):
    return render(request,"Dashboard/howitworks.html")


@login_required
def create_auction(request):
    if request.method == 'POST':
        item_form = ItemForm(request.POST, request.FILES)
        auction_form = AuctionForm(request.POST)

        if item_form.is_valid() and auction_form.is_valid():

            item = item_form.save(commit=False)
            item.seller = request.user.seller
            item.save()

            auction = auction_form.save(commit=False)
            auction.item = item
            auction.seller = request.user.seller
            auction.current_price = auction.starting_price
            auction.save()

            return redirect('SellerDashboard')

        else:
            print(item_form.errors)
            print(auction_form.errors)

    else:
        item_form = ItemForm()
        auction_form = AuctionForm()

    return render(request, 'Dashboard/create_auction.html', {
        'item_form': item_form,
        'auction_form': auction_form
    })


from django.core.paginator import Paginator

def auction_list(request):
    auctions = Auction.objects.filter(
        status="ACTIVE",
        end_time__gt=timezone.now()
    ).select_related("item", "item__seller", "item__category").annotate(bid_count=Count('bids'))

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        auctions = auctions.filter(
            Q(item__name__icontains=search) |
            Q(item__description__icontains=search) |
            Q(item__category__name__icontains=search)
        )

    # Category filter
    category = request.GET.get('category', '')
    if category:
        auctions = auctions.filter(item__category__name=category)

    # Sort
    sort = request.GET.get('sort', 'ending')
    if sort == 'price_low':
        auctions = auctions.order_by('current_price')
    elif sort == 'price_high':
        auctions = auctions.order_by('-current_price')
    elif sort == 'most_bids':
        auctions = auctions.order_by('-bid_count')
    elif sort == 'newest':
        auctions = auctions.order_by('-created_at')
    else:
        auctions = auctions.order_by('end_time')

    # Pagination — 12 auctions per page
    paginator = Paginator(auctions, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "Dashboard/auction_list.html", {
        "auctions": page_obj,          # ← now sends page_obj not auctions
        "page_obj": page_obj,
        "current_sort": sort,
        "current_category": category,
        "current_search": search,
        "categories": Category.objects.all(),
    })

def should_notify(user, notification_type):
    return True
def auction_detail(request, pk):
    auction = get_object_or_404(Auction, pk=pk)

    # Auto-end auction and determine winner
    if auction.end_time <= timezone.now() and auction.status == 'ACTIVE':
        auction.status = "ENDED"
        auction.save()

        winning_bid = Bid.objects.filter(auction=auction).order_by('-amount').first()

        if winning_bid:
            winning_bid.status = 'WINNING'
            winning_bid.save()

            Bid.objects.filter(auction=auction).exclude(id=winning_bid.id).update(status='LOST')

            # Notify winner
            if should_notify(winning_bid.buyer.user, 'AUCTION_ENDED'):
                Notification.objects.create(
                    user=winning_bid.buyer.user,
                    message=f"Congratulations! You won '{auction.item.name}' with ₹{winning_bid.amount}. Please complete your payment.",
                    notification_type='AUCTION_ENDED',
                    auction=auction
                )


            if winning_bid:
                winning_bid.status = 'WINNING'
                winning_bid.save()
                Bid.objects.filter(auction=auction).exclude(id=winning_bid.id).update(status='LOST')

                if should_notify(winning_bid.buyer.user, 'AUCTION_ENDED'):
                    Notification.objects.create(
                    user=winning_bid.buyer.user,
                    message=f"Congratulations! You won '{auction.item.name}' with ₹{winning_bid.amount}.",
                    notification_type='AUCTION_ENDED',
                    auction=auction
                    )
                send_auction_won_email(winning_bid.buyer.user, auction, winning_bid.amount)  # ← add

                if should_notify(auction.item.seller.user, 'AUCTION_ENDED'):
                    Notification.objects.create(
                    user=auction.item.seller.user,
                    message=f"Your auction for '{auction.item.name}' has ended.",
                    notification_type='AUCTION_ENDED',
                    auction=auction
                    )
                send_auction_ended_seller_email(  # ← add
                    auction.item.seller.user,
                    auction,
                    winning_bid.buyer.user,
                    winning_bid.amount
                    )

            # Notify seller
            if should_notify(auction.item.seller.user, 'AUCTION_ENDED'):
                Notification.objects.create(
                    user=auction.item.seller.user,
                    message=f"Your auction for '{auction.item.name}' has ended. Winner: {winning_bid.buyer.user.First_name} {winning_bid.buyer.user.Last_name} with ₹{winning_bid.amount}.",
                    notification_type='AUCTION_ENDED',
                    auction=auction
                )

    if request.method == "POST":
        try:
            buyer = request.user.buyer
        except Exception as e:
            messages.error(request, "Only registered buyers can place bids.")
            return redirect("auction_detail", pk=auction.pk)

        bid_amount = request.POST.get("bid_amount")
        if bid_amount:
            bid_amount = float(bid_amount)
            min_required = float(auction.current_price) + float(auction.bid_increment)

            if auction.status != "ACTIVE":
                messages.error(request, "This auction is no longer active.")
                return redirect("auction_detail", pk=auction.pk)

            if bid_amount < min_required:
                messages.error(request, f"Your bid must be at least ₹{min_required}")
                return redirect("auction_detail", pk=auction.pk)

            # Get outbid buyer BEFORE updating status
            outbid_bid = Bid.objects.filter(auction=auction, status='WINNING').first()

            # Mark previous winning bid as OUTBID
            Bid.objects.filter(auction=auction, status='WINNING').update(status='OUTBID')

            Bid.objects.create(auction=auction, buyer=buyer, amount=bid_amount, status='WINNING')
            auction.current_price = bid_amount
            auction.save()

            # Notify seller of new bid
            if should_notify(auction.item.seller.user, 'BID_PLACED'):
                Notification.objects.create(
                    user=auction.item.seller.user,
                    message=f"A new bid of ₹{bid_amount} was placed on your auction '{auction.item.name}'.",
                    notification_type='BID_PLACED',
                    auction=auction
                )

            # Notify current buyer their bid was placed successfully
            if should_notify(buyer.user, 'BID_PLACED'):
                Notification.objects.create(
                    user=buyer.user,
                    message=f"Your bid of ₹{bid_amount} on '{auction.item.name}' was placed successfully.",
                    notification_type='BID_PLACED',
                    auction=auction
                )

            # Notify outbid buyer ONLY if it's a different person
            if outbid_bid and outbid_bid.buyer != buyer:
                if should_notify(outbid_bid.buyer.user, 'OUTBID'):
                    Notification.objects.create(
                        user=outbid_bid.buyer.user,
                        message=f"You have been outbid on '{auction.item.name}'. Current bid is ₹{bid_amount}.",
                        notification_type='OUTBID',
                        auction=auction
                    )
                    send_outbid_email(outbid_bid.buyer.user, auction, bid_amount)  # ← inside same if block
            send_bid_placed_email(buyer.user, auction, bid_amount)    

            # After outbid notification
                    

            messages.success(request, "Bid placed successfully!")
            return redirect("auction_detail", pk=auction.pk)

    bids = auction.bids.all().order_by('-amount')
    winner = Bid.objects.filter(auction=auction, status='WINNING').first()

    return render(request, "Dashboard/auction_detail.html", {
        "auction": auction,
        "bids": bids,
        "winner": winner,
        "end_time_ms": int(auction.end_time.timestamp() * 1000),
    })

@login_required
def seller_profile(request):
    try:
        seller = request.user.seller
    except ObjectDoesNotExist:
        messages.error(request, "You don't have a seller profile.")
        return redirect('become_seller')

    if request.method == "POST":
        request.user.First_name = request.POST.get('First_name')
        request.user.Last_name = request.POST.get('Last_name')
        request.user.Mobile_number = request.POST.get('Mobile_number')
        request.user.Gender = request.POST.get('Gender')
        request.user.save()

        form = SellerProfileForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect("seller_profile")
    else:
        form = SellerProfileForm(instance=seller)

    context = {
        "form": form,
        "seller": seller,
        "total_auctions": Auction.objects.filter(item__seller=seller).count(),  # ← ADD
        "total_sold":     Auction.objects.filter(item__seller=seller, status='ENDED').count(),  # ← ADD
    }
    return render(request, "Dashboard/seller_profile.html", context)

@login_required
def buyer_profile(request):
    try:
        buyer = request.user.buyer
    except ObjectDoesNotExist:
        messages.error(request, "You don't have a buyer profile.")
        return redirect('home')

    if request.method == "POST":
        request.user.First_name = request.POST.get('First_name')
        request.user.Last_name = request.POST.get('Last_name')
        request.user.Mobile_number = request.POST.get('Mobile_number')
        request.user.Gender = request.POST.get('Gender')

        if request.FILES.get('profile_photo'):
            request.user.profile_photo = request.FILES['profile_photo']

        request.user.save()

        form = BuyerProfileForm(request.POST, request.FILES, instance=buyer)
        if form.is_valid():
            form.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("buyer_profile")
    else:
        form = BuyerProfileForm(instance=buyer)

    # Get all watchlisted auctions for this buyer
    watchlist = Watchlist.objects.filter(buyer=buyer).select_related('auction')
    watchlist_count = watchlist.count()

    context = {
        "form": form,
        "buyer": buyer,
        "won_auctions": Bid.objects.filter(buyer=buyer, status='WINNING').count(),
        "watchlist": watchlist,
        "watchlist_count": watchlist_count,
    }
    return render(request, "Dashboard/buyer_profile.html", context)

@login_required
def admin_profile(request):
    try:
        adminprofile = request.user.adminprofile
    except ObjectDoesNotExist:
        messages.error(request, "You don't have an admin profile.")
        return redirect('home')

    if request.method == "POST":
        # ✅ Save User model fields
        request.user.First_name = request.POST.get('First_name')
        request.user.Last_name = request.POST.get('Last_name')
        request.user.Mobile_number = request.POST.get('Mobile_number')
        request.user.Gender = request.POST.get('Gender')

        # ✅ Save profile photo if uploaded
        if request.FILES.get('profile_photo'):
            request.user.profile_photo = request.FILES['profile_photo']

        # ✅ Save everything in one call AFTER setting all fields
        request.user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("admin_profile")

    # ✅ Pass counts for the stats cards
    from Dashboard.models import Auction   # adjust app name if different
          # adjust app name if different

    context = {
        "adminprofile": adminprofile,
        "total_users": User.objects.count(),
        "total_auctions": Auction.objects.count(),
    }
    return render(request, "Dashboard/admin_profile.html", context)

@login_required
@role_required(allowed_roles=['Admin'])
def manage_categories(request):
    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            if name:
                category = Category.objects.create(name=name, description=description)
                if request.FILES.get('image'):
                    category.image = request.FILES['image']
                    category.save()
                messages.success(request, f'Category "{name}" added successfully!')
            else:
                messages.error(request, 'Category name is required.')

        elif action == 'edit':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            try:
                category = Category.objects.get(id=category_id)
                category.name = name
                category.description = description
                if request.FILES.get('image'):
                    category.image = request.FILES['image']
                category.save()
                messages.success(request, f'Category "{name}" updated successfully!')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')

        elif action == 'delete':
            category_id = request.POST.get('category_id')
            try:
                category = Category.objects.get(id=category_id)
                name = category.name
                category.delete()
                messages.success(request, f'Category "{name}" deleted.')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')

        return redirect('manage_categories')

    categories = Category.objects.all().order_by('-created_at')
    return render(request, 'Dashboard/category_management.html', {'categories': categories})



@login_required
@role_required(allowed_roles=['Admin', 'Seller'])
def manage_auctions(request):
    # ✅ Keep POST handling from your original
    if request.method == "POST":
        action = request.POST.get('action')
        auction = Auction.objects.get(id=request.POST.get('auction_id'))
        if action == 'end':
            auction.status = 'ENDED'
        elif action == 'cancel':
            auction.status = 'CANCELLED'
        auction.save()
        messages.success(request, f'Auction "{auction.item.name}" updated.')
        return redirect('manage_auctions')

    # ✅ Filter by role
    if request.user.Role == 'Admin':
        qs = Auction.objects.select_related('item', 'item__seller__user', 'item__category').prefetch_related('bids')
    else:  # Seller sees only their own
        qs = Auction.objects.select_related('item', 'item__seller__user', 'item__category').prefetch_related('bids').filter(item__seller=request.user.seller)

    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])

    context = {
        'auctions': qs.order_by('-created_at'),
        'total_auctions': qs.count(),           # ✅ counts based on filtered qs
        'active_auctions': qs.filter(status='ACTIVE').count(),
        'ended_auctions': qs.filter(status='ENDED').count(),
        'cancelled_auctions': qs.filter(status='CANCELLED').count(),
    }
    return render(request, 'Dashboard/manage_auctions.html', context)

@login_required
@role_required(allowed_roles=['Admin', 'Seller'])
def manage_items(request):
    # ✅ Keep POST handling
    if request.method == "POST":
        if request.POST.get('action') == 'delete_item':
            Item.objects.filter(id=request.POST.get('item_id')).delete()
            messages.success(request, 'Item deleted.')
        return redirect('manage_items')

    # ✅ Filter by role
    if request.user.Role == 'Admin':
        qs = Item.objects.select_related('seller__user', 'category')
    else:  # Seller sees only their own items
        qs = Item.objects.select_related('seller__user', 'category').filter(
            seller=request.user.seller
        )

    if request.GET.get('condition'):
        qs = qs.filter(condition=request.GET['condition'])

    context = {
        'items': qs.order_by('-created_at'),
        'total_items': qs.count(),                              # ✅ filtered counts
        'new_items': qs.filter(condition='NEW').count(),
        'used_items': qs.filter(condition='USED').count(),
        'refurb_items': qs.filter(condition='REFURB').count(),
    }
    return render(request, 'Dashboard/manage_items.html', context)

@login_required
@role_required(allowed_roles=['Admin', 'Buyer'])
def manage_bids(request):
    if request.user.Role == 'Admin':
        # Admin sees ALL bids
        bids = Bid.objects.select_related('buyer__user', 'auction__item').order_by('-bid_time')
    elif request.user.Role == 'Buyer':
        # Buyer sees ONLY their own bids
        bids = Bid.objects.select_related('buyer__user', 'auction__item').filter(
            buyer=request.user.buyer  # use your actual related name
        ).order_by('-bid_time')

    context = {
        'bids': bids,
        'total_bids': bids.count(),
        'winning_bids': bids.filter(status='WINNING').count(),
        'outbid_bids': bids.filter(status='OUTBID').count(),
        'lost_bids': bids.filter(status='LOST').count(),
    }
    return render(request, 'Dashboard/manage_bids.html', context)

@login_required
@role_required(allowed_roles=['Admin', 'Seller', 'Buyer'])
def manage_payments(request):
    # ✅ Keep POST handling
    if request.method == "POST":
        p = Payment.objects.get(id=request.POST.get('payment_id'))
        p.status = request.POST.get('new_status')
        p.save()
        messages.success(request, 'Payment status updated.')
        return redirect('manage_payments')

    # ✅ Filter by role
    if request.user.Role == 'Admin':
        qs = Payment.objects.select_related('buyer__user', 'auction__item')
    elif request.user.Role == 'Buyer':
        qs = Payment.objects.select_related('buyer__user', 'auction__item').filter(
            buyer=request.user.buyer
        )
    else:  # Seller sees payments for their auctions
        qs = Payment.objects.select_related('buyer__user', 'auction__item').filter(
            auction__item__seller=request.user.seller
        )

    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])

    context = {
        'payments': qs.order_by('-payment_date'),
        'total_payments': qs.count(),                               # ✅ filtered counts
        'completed_payments': qs.filter(status='COMPLETED').count(),
        'pending_payments': qs.filter(status='PENDING').count(),
        'failed_payments': qs.filter(status='FAILED').count(),
        'refunded_payments': qs.filter(status='REFUNDED').count(),
    }
    return render(request, 'Dashboard/manage_payments.html', context)

@login_required
@role_required(allowed_roles=['Admin', 'Seller', 'Buyer'])
def manage_disputes(request):
    # ✅ Keep POST handling
    if request.method == "POST":
        d = Dispute.objects.get(id=request.POST.get('dispute_id'))
        d.status = request.POST.get('new_status')
        d.save()
        messages.success(request, 'Dispute status updated.')
        return redirect('manage_disputes')

    # ✅ Filter by role
    if request.user.Role == 'Admin':
        qs = Dispute.objects.select_related('raised_by', 'auction__item')
    elif request.user.Role == 'Buyer':
        qs = Dispute.objects.select_related('raised_by', 'auction__item').filter(
            raised_by=request.user
        )
    else:  # Seller sees disputes on their auctions
        qs = Dispute.objects.select_related('raised_by', 'auction__item').filter(
            auction__item__seller=request.user.seller
        )

    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])

    context = {
        'disputes': qs.order_by('-created_at'),
        'total_disputes': qs.count(),                               # ✅ filtered counts
        'open_disputes': qs.filter(status='OPEN').count(),
        'resolved_disputes': qs.filter(status='RESOLVED').count(),
        'closed_disputes': qs.filter(status='CLOSED').count(),
    }
    return render(request, 'Dashboard/manage_disputes.html', context)

@login_required
@role_required(allowed_roles=['Admin', 'Seller', 'Buyer'])
def manage_notifications(request):
    # ✅ Only Admin can send notifications
    if request.method == "POST" and request.user.Role == 'Admin':
        if request.POST.get('action') == 'send':
            msg = request.POST.get('message')
            ntype = request.POST.get('notification_type', 'GENERAL')
            uid = request.POST.get('user_id')
            if uid == 'all':
                for u in User.objects.all():
                    Notification.objects.create(user=u, message=msg, notification_type=ntype)
                messages.success(request, 'Notification sent to all users.')
            else:
                Notification.objects.create(user=User.objects.get(id=uid), message=msg, notification_type=ntype)
                messages.success(request, 'Notification sent.')
            return redirect('manage_notifications')

    # ✅ Filter by role
    if request.user.Role == 'Admin':
        notifications = Notification.objects.select_related('user').order_by('-created_at')
        all_users = User.objects.all()  # Admin can send to anyone
    else:  # Buyer or Seller sees only their own
        notifications = Notification.objects.select_related('user').filter(
            user=request.user
        ).order_by('-created_at')
        all_users = None  # Buyer/Seller cannot send notifications

    context = {
        'notifications': notifications,
        'all_users': all_users,
    }
    return render(request, 'Dashboard/manage_notifications.html', context)


@login_required
@role_required(allowed_roles=['Admin', 'Seller', 'Buyer'])
def manage_reviews(request):
    # ✅ Only Admin can delete reviews
    if request.method == "POST":
        if request.user.Role == 'Admin':
            Review.objects.filter(id=request.POST.get('review_id')).delete()
            messages.success(request, 'Review deleted.')
        return redirect('manage_reviews')

    # ✅ Filter by role
    if request.user.Role == 'Admin':
        qs = Review.objects.select_related('reviewer', 'reviewee', 'auction__item')
    elif request.user.Role == 'Buyer':
        qs = Review.objects.select_related('reviewer', 'reviewee', 'auction__item').filter(
            reviewer=request.user
        )
    else:  # Seller sees reviews about them
        qs = Review.objects.select_related('reviewer', 'reviewee', 'auction__item').filter(
            reviewee=request.user
        )

    if request.GET.get('rating'):
        qs = qs.filter(rating=request.GET['rating'])

    avg = qs.aggregate(a=Avg('rating'))['a']   # ✅ avg from filtered qs
    context = {
        'reviews': qs.order_by('-created_at'),
        'total_reviews': qs.count(),            # ✅ filtered counts
        'five_star': qs.filter(rating=5).count(),
        'one_star': qs.filter(rating=1).count(),
        'avg_rating': round(avg, 1) if avg else 0,
    }
    return render(request, 'Dashboard/manage_reviews.html', context)

@login_required
@role_required(allowed_roles=['Admin', 'Buyer'])
def manage_watchlist(request):
    # ✅ Filter by role
    if request.user.Role == 'Admin':
        qs = Watchlist.objects.select_related('buyer__user', 'auction__item__category')
    else:  # Buyer sees only their own watchlist
        qs = Watchlist.objects.select_related('buyer__user', 'auction__item__category').filter(
            buyer=request.user.buyer
        )

    most = qs.values('auction__item__name').annotate(c=Count('id')).order_by('-c').first()

    context = {
        'watchlist': qs.order_by('-added_at'),
        'total_watchlist': qs.count(),                          # ✅ filtered counts
        'unique_buyers': qs.values('buyer').distinct().count(),
        'unique_auctions': qs.values('auction').distinct().count(),
        'most_watched': most['auction__item__name'][:15] + '…' if most else '-',
    }
    return render(request, 'Dashboard/manage_watchlist.html', context)

@login_required
@role_required(allowed_roles=['Admin'])
def manage_activity_log(request):
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    context = {
        'logs': ActivityLog.objects.select_related('user').order_by('-timestamp'),
        'total_logs': ActivityLog.objects.count(),
        'today_logs': ActivityLog.objects.filter(timestamp__date=today).count(),
        'this_week_logs': ActivityLog.objects.filter(timestamp__gte=week_ago).count(),
        'unique_users_logged': ActivityLog.objects.values('user').distinct().count(),
    }
    return render(request, 'Dashboard/manage_activity_log.html', context)


from django.db.models import Count, Max

@login_required
@role_required(allowed_roles=['Seller'])
def seller_manage_bids(request):
    seller = request.user.seller

    # All auctions by this seller, with their bids prefetched
    auctions_with_bids = Auction.objects.filter(
        item__seller=seller
    ).select_related(
        'item__category', 'item__seller__user'
    ).prefetch_related(
        'bids__buyer__user'
    ).order_by('-created_at')

    # Stats
    all_bids = Bid.objects.filter(auction__item__seller=seller)
    highest  = all_bids.aggregate(h=Max('amount'))['h'] or 0

    context = {
        'auctions_with_bids':    auctions_with_bids,
        'total_bids':            all_bids.count(),
        'active_auctions_count': auctions_with_bids.filter(status='ACTIVE').count(),
        'unique_bidders':        all_bids.values('buyer').distinct().count(),
        'highest_bid':           highest,
    }
    return render(request, 'Dashboard/seller_manage_bids.html', context)   

@login_required
def dashboard_redirect(request):
    if request.user.Role == 'Admin':
        return redirect('AdminDashboard')
    elif request.user.Role == 'Seller':
        return redirect('SellerDashboard')
    elif request.user.Role == 'Buyer':
        return redirect('BuyerDashboard')
    else:
        return redirect('home') 

from django.conf import settings
@login_required
@role_required(allowed_roles=['Buyer'])
def make_payment(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id, status='ENDED')
    
    try:
        buyer = request.user.buyer
    except:
        messages.error(request, "Buyer profile not found.")
        return redirect('home')

    winning_bid = Bid.objects.filter(auction=auction, buyer=buyer).order_by('-amount').first()
    highest_bid = Bid.objects.filter(auction=auction).order_by('-amount').first()
    
    if not winning_bid or winning_bid != highest_bid:
        messages.error(request, "You did not win this auction.")
        return redirect('BuyerDashboard')

    existing_payment = Payment.objects.filter(
    auction=auction, buyer=buyer, status='COMPLETED'
    ).first()
    if existing_payment:
        messages.info(request, "You have already paid for this auction.")
        return redirect('BuyerDashboard')
    
    
    return render(request, 'Dashboard/make_payment.html', {
        'auction': auction,
        'winning_bid': winning_bid,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY
        
    })
       
 
@login_required
@role_required(allowed_roles=['Buyer'])
def toggle_watchlist(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    buyer = request.user.buyer
    print("=== TOGGLE WATCHLIST ===")
    print("auction:", auction)
    print("buyer:", buyer)
    watchlist_item = Watchlist.objects.filter(auction=auction, buyer=buyer).first()
    print("existing entry:", watchlist_item)
    if watchlist_item:
        watchlist_item.delete()
        messages.success(request, "Removed from watchlist.")
        print("=== REMOVED ===")
    else:
        Watchlist.objects.create(auction=auction, buyer=buyer)
        messages.success(request, "Added to watchlist.")
        print("=== ADDED ===")
    return redirect('auction_detail', pk=auction_id)


# ============================================================
# ADD THESE 2 VIEWS TO YOUR views.py
# ============================================================

@login_required
@role_required(allowed_roles=['Buyer'])
def submit_review(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id, status='ENDED')
    buyer = request.user.buyer

    # Must have won
    winning_bid = Bid.objects.filter(auction=auction, buyer=buyer, status='WINNING').first()
    if not winning_bid:
        messages.error(request, "You can only review auctions you won.")
        return redirect('manage_reviews')

    # Must have paid
    payment = Payment.objects.filter(auction=auction, buyer=buyer, status='COMPLETED').first()
    if not payment:
        messages.error(request, "Please complete payment before leaving a review.")
        return redirect('manage_payments')

    # Not already reviewed
    if Review.objects.filter(reviewer=request.user, auction=auction).exists():
        messages.error(request, "You have already reviewed this auction.")
        return redirect('manage_reviews')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            Review.objects.create(
                reviewer=request.user,
                reviewee=auction.item.seller.user,
                auction=auction,
                rating=int(rating),
                comment=comment
            )
            messages.success(request, "Review submitted successfully!")
            return redirect('manage_reviews')
        else:
            messages.error(request, "Please provide both a rating and a comment.")

    return render(request, 'Dashboard/submit_review.html', {
        'auction': auction,
        'winning_bid': winning_bid,
    })


@login_required
@role_required(allowed_roles=['Buyer'])
def raise_dispute(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id, status='ENDED')
    buyer = request.user.buyer

    # Must have won
    winning_bid = Bid.objects.filter(auction=auction, buyer=buyer, status='WINNING').first()
    if not winning_bid:
        messages.error(request, "You can only raise disputes for auctions you won.")
        return redirect('manage_disputes')

    # Must have paid
    payment = Payment.objects.filter(auction=auction, buyer=buyer, status='COMPLETED').first()
    if not payment:
        messages.error(request, "Please complete payment before raising a dispute.")
        return redirect('manage_payments')

    # Not already disputed
    if Dispute.objects.filter(raised_by=request.user, auction=auction).exists():
        messages.error(request, "You have already raised a dispute for this auction.")
        return redirect('manage_disputes')

    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            Dispute.objects.create(
                auction=auction,
                raised_by=request.user,
                reason=reason,
                status='OPEN'
            )
            # Notify all admins
            for admin in User.objects.filter(Role='Admin'):
                Notification.objects.create(
                    user=admin,
                    message=f"New dispute raised on '{auction.item.name}' by {request.user.First_name} {request.user.Last_name}.",
                    notification_type='GENERAL',
                    auction=auction
                )

            if should_notify(request.user, 'DISPUTE'):
                Notification.objects.create(
                    user=request.user,
                    message=f"Your dispute for '{auction.item.name}' has been submitted and is under review.",
                    notification_type='DISPUTE',
                    auction=auction
                )

# ADD THIS — Notify seller
            if should_notify(auction.item.seller.user, 'DISPUTE'):
                Notification.objects.create(
                    user=auction.item.seller.user,
                    message=f"A dispute has been raised by {request.user.First_name} {request.user.Last_name} for your auction '{auction.item.name}'.",
                    notification_type='DISPUTE',
                    auction=auction
                )

            messages.success(request, "Dispute raised successfully. Our team will review it.")
            return redirect('manage_disputes')
        else:
            messages.error(request, "Please provide a reason for the dispute.")

    return render(request, 'Dashboard/raise_dispute.html', {
        'auction': auction,
        'payment': payment,
        'winning_bid': winning_bid,
    })


@login_required
@role_required(allowed_roles=['Buyer'])
def purchase_history(request):
    buyer = request.user.buyer
    payments = Payment.objects.filter(
        buyer=buyer
    ).select_related('auction__item__seller__user').order_by('-payment_date')

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        payments = payments.filter(status=status)

    context = {
        'payments': payments,
        'total_spent': payments.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0,
        'total_purchases': payments.filter(status='COMPLETED').count(),
        'pending_payments': payments.filter(status='PENDING').count(),
        'current_status': status,
    }
    return render(request, 'Dashboard/purchase_history.html', context)



@login_required
def settings_page(request):

    # Get or create settings for this user
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'notifications':
            user_settings.notif_bid_placed = 'notif_bid' in request.POST
            user_settings.notif_outbid = 'notif_outbid' in request.POST
            user_settings.notif_auction_won = 'notif_won' in request.POST
            user_settings.notif_payment = 'notif_payment' in request.POST
            user_settings.notif_dispute = 'notif_dispute' in request.POST

            user_settings.save()
            messages.success(request, '🔔 Notification preferences saved!')

        elif action == 'privacy':
            user_settings.public_profile = 'public_profile' in request.POST
            user_settings.show_bids = 'show_bids' in request.POST

            user_settings.save()
            messages.success(request, '🔒 Privacy settings saved!')

        elif action == 'delete_account':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('home')

        return redirect('setting')

    return render(request, 'Dashboard/settings.html', {
        'notif_prefs': {
            'bid_placed': user_settings.notif_bid_placed,
            'outbid': user_settings.notif_outbid,
            'auction_won': user_settings.notif_auction_won,
            'payment': user_settings.notif_payment,
            'dispute': user_settings.notif_dispute,
        },
        'privacy_prefs': {
            'public_profile': user_settings.public_profile,
            'show_bids': user_settings.show_bids,
        },
    })

@login_required
def payment_success(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    try:
        buyer = request.user.buyer
    except:
        return redirect('home')

    winning_bid = Bid.objects.filter(
        auction=auction, buyer=buyer
    ).order_by('-amount').first()

    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_SECRET_KEY
        token = request.POST.get('stripeToken')
        amount_paise = int(winning_bid.amount * 100)

        try:
            # Charge the card
            charge = stripe.Charge.create(
                amount=amount_paise,
                currency='inr',
                description=f'Payment for {auction.item.name}',
                source=token,
            )

            # Save payment as completed
            Payment.objects.create(
                auction=auction,
                buyer=buyer,
                amount=winning_bid.amount,
                payment_method='CARD',
                status='COMPLETED'
            )

            # Notify seller
            Notification.objects.create(
                user=auction.item.seller.user,
                message=f"Payment of ₹{winning_bid.amount} received for '{auction.item.name}'.",
                notification_type='PAYMENT',
                auction=auction
            )

            user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
            if user_settings.notif_payment:
                Notification.objects.create(
                user=request.user,
                message=f"Your payment of ₹{winning_bid.amount} for '{auction.item.name}' was successful.",
                notification_type='PAYMENT',
                auction=auction
                )

            send_payment_received_email(
                auction.item.seller.user,
                auction,
                winning_bid.amount
            )    

            messages.success(request, f"Payment of ₹{winning_bid.amount} successful!")
            return redirect('manage_payments')

        except stripe.error.CardError as e:
            messages.error(request, f"Card error: {e.user_message}")
            return redirect('make_payment', auction_id=auction_id)

        except Exception as e:
            messages.error(request, "Payment failed. Please try again.")
            return redirect('make_payment', auction_id=auction_id)

    return redirect('make_payment', auction_id=auction_id)

@login_required
@role_required(allowed_roles=['Seller'])
def quick_create_auction(request):
    if request.method == 'POST':
        try:
            seller = request.user.seller
            category = Category.objects.get(id=request.POST.get('category'))
            
            # Create Item
            item = Item.objects.create(
                seller=seller,
                category=category,
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                condition=request.POST.get('condition'),
                shipping_cost=request.POST.get('shipping_cost'),
            )
            
            # Save image if uploaded
            if request.FILES.get('image'):
                item.image = request.FILES['image']
                item.save()

            # Create Auction
            starting_price = request.POST.get('starting_price')
            Auction.objects.create(
                item=item,
                starting_price=starting_price,
                reserve_price=request.POST.get('reserve_price'),
                current_price=starting_price,
                bid_increment=request.POST.get('bid_increment'),
                end_time=request.POST.get('end_time'),
                status='ACTIVE',
            )

            messages.success(request, f"Auction for '{item.name}' launched successfully!")
            return redirect('SellerDashboard')

        except Exception as e:
            messages.error(request, f"Error creating auction: {str(e)}")
            return redirect('SellerDashboard')

    return redirect('SellerDashboard')    


@login_required
@role_required(allowed_roles=['Buyer'])
def request_refund(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, buyer=request.user.buyer)
    
    if payment.status != 'COMPLETED':
        messages.error(request, "You can only request a refund for completed payments.")
        return redirect('manage_payments')
    
    payment.status = 'REFUND_REQUESTED'
    payment.save()
    
    # Notify seller
    Notification.objects.create(
        user=payment.auction.item.seller.user,
        message=f"{request.user.First_name} {request.user.Last_name} has requested a refund for '{payment.auction.item.name}' (₹{payment.amount}).",
        notification_type='PAYMENT',
        auction=payment.auction
    )
    
    # Notify all admins
    for admin in User.objects.filter(Role='Admin'):
        Notification.objects.create(
            user=admin,
            message=f"Refund requested by {request.user.First_name} {request.user.Last_name} for '{payment.auction.item.name}' (₹{payment.amount}).",
            notification_type='PAYMENT',
            auction=payment.auction
        )
    
    messages.success(request, "Refund request submitted successfully. We will review it shortly.")
    return redirect('manage_payments')


@login_required
@role_required(allowed_roles=['Seller', 'Admin'])
def approve_refund(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, status='REFUND_REQUESTED')

    # Seller can only refund their own auctions
    if request.user.Role == 'Seller':
        if payment.auction.item.seller.user != request.user:
            messages.error(request, "You can only approve refunds for your own auctions.")
            return redirect('manage_payments')

    try:
        payment.status = 'REFUNDED'
        payment.save()

        # Notify buyer
        Notification.objects.create(
            user=payment.buyer.user,
            message=f"Your refund of ₹{payment.amount} for '{payment.auction.item.name}' has been approved by the seller.",
            notification_type='PAYMENT',
            auction=payment.auction
        )

        # Notify admin
        for admin in User.objects.filter(Role='Admin'):
            Notification.objects.create(
                user=admin,
                message=f"Refund of ₹{payment.amount} approved by {request.user.First_name} {request.user.Last_name} for '{payment.auction.item.name}'.",
                notification_type='PAYMENT',
                auction=payment.auction
            )

        messages.success(request, f"Refund of ₹{payment.amount} approved successfully.")

    except Exception as e:
        messages.error(request, f"Refund failed: {str(e)}")

    return redirect('manage_payments')   


@login_required
@role_required(allowed_roles=['Admin'])
def manage_buyers(request):
    from django.db.models import Sum, Count, Q
    
    buyers = Buyer.objects.annotate(
        total_bids=Count('bids'),
        auctions_won=Count('bids', filter=Q(bids__status='WINNING')),
        total_spent=Sum('payments__amount', filter=Q(payments__status='COMPLETED'))
    ).select_related('user').order_by('-total_spent')
    
    total_won = Bid.objects.filter(status='WINNING').count()
    total_platform_spent = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0

    context = {
    'buyers': buyers,
    'total_buyers': buyers.count(),
    'total_won': total_won,
    'total_platform_spent': total_platform_spent,
    }
    return render(request, 'Dashboard/manage_buyers.html', context)    


@login_required
@role_required(allowed_roles=['Admin'])
def manage_sellers(request):
    sellers = Seller.objects.annotate(
        total_auctions=Count('items__auction'),
        total_sold=Count('items__auction', filter=Q(items__auction__status='ENDED')),
        total_earned=Sum('items__auction__payments__amount', filter=Q(items__auction__payments__status='COMPLETED'))
    ).filter(total_auctions__gte=1).select_related('user').order_by('-total_earned')

    total_platform_earned = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'sellers': sellers,
        'total_sellers': sellers.count(),
        'total_platform_earned': total_platform_earned,
    }
    return render(request, 'Dashboard/manage_sellers.html', context)


@login_required
@role_required(allowed_roles=['Admin'])
def manage_categories_analytics(request):
    categories = Category.objects.annotate(
        total_auctions=Count('items__auction'),
        total_bids=Count('items__auction__bids'),
        total_revenue=Sum('items__auction__payments__amount', filter=Q(items__auction__payments__status='COMPLETED'))
    ).order_by('-total_bids')

    context = {
        'categories': categories,
        'total_categories': categories.count(),
        'total_auctions_count': sum(c.total_auctions for c in categories),
    'total_bids_count': sum(c.total_bids for c in categories),
    }
    return render(request, 'Dashboard/manage_categories_analytics.html', context)    



from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.http import HttpResponse
import io

@login_required
@role_required(allowed_roles=['Buyer'])
def download_invoice(request, payment_id):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    import io

    payment = get_object_or_404(Payment, id=payment_id, buyer=request.user.buyer)

    buffer = io.BytesIO()
    w, h = A4
    c = canvas.Canvas(buffer, pagesize=A4)

    BG_MAIN      = colors.HexColor('#13102b')
    BG_CARD      = colors.HexColor('#1c1640')
    BG_DARKER    = colors.HexColor('#0f0c24')
    PRIMARY      = colors.HexColor('#2d1655')
    ACCENT       = colors.HexColor('#7c3aed')
    ACCENT_LIGHT = colors.HexColor('#c4b5fd')
    BORDER       = colors.HexColor('#2d1e50')
    TEXT_WHITE   = colors.HexColor('#f1f0f5')
    TEXT_MID     = colors.HexColor('#a89dc4')
    TEXT_LIGHT   = colors.HexColor('#6b5f85')
    GREEN        = colors.HexColor('#10b981')
    GREEN_DARK   = colors.HexColor('#064e3b')
    WHITE        = colors.white

    pid = payment.id
    shipping = float(payment.auction.item.shipping_cost or 0)
    subtotal = float(payment.amount) - shipping

    # Full dark background
    c.setFillColor(BG_MAIN)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Header band
    c.setFillColor(BG_DARKER)
    c.rect(0, h - 130, w, 130, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(0, h - 4, w, 4, fill=1, stroke=0)

    # Glow circles
    c.setFillColor(ACCENT)
    c.setFillAlpha(0.12)
    c.circle(w - 80, h - 30, 110, fill=1, stroke=0)
    c.setFillAlpha(0.08)
    c.circle(60, h - 110, 80, fill=1, stroke=0)
    c.setFillAlpha(1)

    # Brand
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 34)
    c.drawString(2*cm, h - 52, 'Auctora')
    c.setFillColor(ACCENT)
    c.rect(2*cm, h - 58, 90, 3, fill=1, stroke=0)
    c.setFillColor(TEXT_MID)
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, h - 72, "The World's Premier Auction Platform")

    # Invoice label
    c.setFillColor(ACCENT_LIGHT)
    c.setFont('Helvetica-Bold', 24)
    c.drawRightString(w - 2*cm, h - 52, 'INVOICE')
    c.setFillColor(PRIMARY)
    c.roundRect(w - 2*cm - 90, h - 82, 90, 22, 11, fill=1, stroke=0)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.8)
    c.roundRect(w - 2*cm - 90, h - 82, 90, 22, 11, fill=0, stroke=1)
    c.setFillColor(ACCENT_LIGHT)
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w - 2*cm - 45, h - 75, f'#{pid:06d}')
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(2*cm, h - 130, w - 2*cm, h - 130)

    # Status pill
    status_y = h - 158
    c.setFillColor(GREEN_DARK)
    c.roundRect(2*cm, status_y, 155, 22, 11, fill=1, stroke=0)
    c.setStrokeColor(GREEN)
    c.setLineWidth(0.8)
    c.roundRect(2*cm, status_y, 155, 22, 11, fill=0, stroke=1)
    c.setFillColor(GREEN)
    c.circle(2*cm + 16, status_y + 11, 5, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(2*cm + 26, status_y + 7, f'PAYMENT {payment.status}')
    c.setFillColor(TEXT_MID)
    c.setFont('Helvetica', 10)
    c.drawRightString(w - 2*cm, status_y + 7, f'Issued: {payment.payment_date.strftime("%d %B %Y")}')

    # Billed To card
    card_y = status_y - 90
    card_h = 75
    c.setFillColor(BG_CARD)
    c.roundRect(2*cm, card_y, 11.2*cm, card_h, 8, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.8)
    c.roundRect(2*cm, card_y, 11.2*cm, card_h, 8, fill=0, stroke=1)
    c.setFillColor(ACCENT)
    c.roundRect(2*cm, card_y, 4, card_h, 2, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(2*cm + 14, card_y + card_h - 14, 'BILLED TO')
    c.setFillColor(TEXT_WHITE)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(2*cm + 14, card_y + card_h - 30, f'{payment.buyer.user.First_name} {payment.buyer.user.Last_name}')
    c.setFillColor(TEXT_MID)
    c.setFont('Helvetica', 10)
    c.drawString(2*cm + 14, card_y + card_h - 45, payment.buyer.user.Email)
    c.drawString(2*cm + 14, card_y + card_h - 59, str(payment.buyer.user.Mobile_number or '—'))

    # Payment details card
    right_x = w/2 + 0.3*cm
    c.setFillColor(BG_CARD)
    c.roundRect(right_x, card_y, 11.2*cm, card_h, 8, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.8)
    c.roundRect(right_x, card_y, 11.2*cm, card_h, 8, fill=0, stroke=1)
    c.setFillColor(colors.HexColor('#4c1d95'))
    c.roundRect(right_x, card_y, 4, card_h, 2, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#4c1d95'))
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(right_x + 14, card_y + card_h - 14, 'PAYMENT DETAILS')
    prows = [
        ('Method', payment.get_payment_method_display()),
        ('Payment ID', f'#{pid:06d}'),
        ('Date', payment.payment_date.strftime('%d %B %Y')),
    ]
    ry = card_y + card_h - 30
    for lbl, val in prows:
        c.setFillColor(TEXT_LIGHT)
        c.setFont('Helvetica', 9)
        c.drawString(right_x + 14, ry, lbl + ':')
        c.setFillColor(TEXT_WHITE)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(right_x + 75, ry, val)
        ry -= 15

    # Item details table
    tbl_label_y = card_y - 28
    c.setFillColor(ACCENT_LIGHT)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(2*cm, tbl_label_y, 'ITEM DETAILS')
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.5)
    c.line(2*cm, tbl_label_y - 3, 2*cm + 72, tbl_label_y - 3)

    thead_y = tbl_label_y - 32
    c.setFillColor(colors.HexColor('#1a0e35'))
    c.roundRect(2*cm, thead_y, w - 4*cm, 26, 6, fill=1, stroke=0)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.8)
    c.roundRect(2*cm, thead_y, w - 4*cm, 26, 6, fill=0, stroke=1)

    col_x = [2*cm + 10, 6.5*cm, 10.5*cm, 13.8*cm, 15.8*cm]
    headers = ['ITEM', 'CATEGORY', 'CONDITION', 'AUC #', 'AMOUNT']
    c.setFillColor(ACCENT_LIGHT)
    c.setFont('Helvetica-Bold', 8.5)
    for i, ht in enumerate(headers):
        c.drawString(col_x[i], thead_y + 9, ht)

    trow_y = thead_y - 34
    c.setFillColor(BG_CARD)
    c.roundRect(2*cm, trow_y, w - 4*cm, 30, 4, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.6)
    c.roundRect(2*cm, trow_y, w - 4*cm, 30, 4, fill=0, stroke=1)

    condition = payment.auction.item.condition
    try:
        condition = payment.auction.item.get_condition_display()
    except:
        pass

    values = [
        payment.auction.item.name,
        payment.auction.item.category.name if payment.auction.item.category else '—',
        condition,
        f'#{payment.auction.id}',
        f'Rs. {float(payment.amount):,.2f}',
    ]
    for i, val in enumerate(values):
        if i == len(values) - 1:
            c.setFillColor(ACCENT_LIGHT)
            c.setFont('Helvetica-Bold', 12)
        else:
            c.setFillColor(TEXT_WHITE)
            c.setFont('Helvetica', 10)
        c.drawString(col_x[i], trow_y + 10, str(val))

    # Totals
    totals_y = trow_y - 24
    box_x = w - 2*cm - 8.5*cm
    box_w = 8.5*cm
    c.setFillColor(BG_CARD)
    c.roundRect(box_x, totals_y - 90, box_w, 90, 8, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.6)
    c.roundRect(box_x, totals_y - 90, box_w, 90, 8, fill=0, stroke=1)
    c.setFillColor(TEXT_MID)
    c.setFont('Helvetica', 10)
    c.drawString(box_x + 16, totals_y - 20, 'Subtotal')
    c.setFillColor(TEXT_WHITE)
    c.drawRightString(box_x + box_w - 16, totals_y - 20, f'Rs. {subtotal:,.2f}')
    c.setFillColor(TEXT_MID)
    c.drawString(box_x + 16, totals_y - 38, 'Shipping')
    c.setFillColor(TEXT_WHITE)
    c.drawRightString(box_x + box_w - 16, totals_y - 38, f'Rs. {shipping:,.2f}')
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(box_x + 16, totals_y - 50, box_x + box_w - 16, totals_y - 50)
    c.setFillColor(ACCENT)
    c.roundRect(box_x, totals_y - 90, box_w, 36, 8, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(box_x + 16, totals_y - 78, 'TOTAL PAID')
    c.setFont('Helvetica-Bold', 14)
    c.drawRightString(box_x + box_w - 16, totals_y - 78, f'Rs. {float(payment.amount):,.2f}')

    # Note
    c.setFillColor(ACCENT)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(2*cm, totals_y - 22, 'NOTE')
    note_lines = [
        'Thank you for your purchase on Auctora.',
        'This receipt confirms your payment was',
        'successfully processed.',
        'Keep this for your records.',
    ]
    c.setFillColor(TEXT_MID)
    c.setFont('Helvetica', 9)
    note_y = totals_y - 36
    for line in note_lines:
        c.drawString(2*cm, note_y, line)
        note_y -= 13

    # Footer
    c.setFillColor(BG_DARKER)
    c.rect(0, 0, w, 65, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(0, 65, w, 2, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.setFillAlpha(0.08)
    c.circle(30, 10, 50, fill=1, stroke=0)
    c.setFillAlpha(0.06)
    c.circle(w - 30, 50, 60, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(w/2, 47, 'Auctora International')
    c.setFillColor(ACCENT_LIGHT)
    c.setFont('Helvetica', 8.5)
    c.drawCentredString(w/2, 33, 'support@auctora.com  |  www.auctora.com')
    c.setFillColor(TEXT_LIGHT)
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(w/2, 19, 'This is a computer-generated receipt and does not require a signature.')

    c.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Auctora_Invoice_{pid:06d}.pdf"'
    return response

