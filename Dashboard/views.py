from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import ItemForm, AuctionForm, BidForm,SellerProfileForm,BuyerProfileForm,AdminProfileForm,CategoryForm,AuctionQuickCreateForm,PaymentForm,WatchlistForm,NotificationForm,NotificationMarkReadForm,ReviewForm,DisputeForm,DisputeStatusUpdateForm,ActivityLogForm,AuctionSearchForm
from .models import Auction,Bid
from core.models import User
from django.utils import timezone
from .decorators import role_required
from django.shortcuts import get_object_or_404
from .models import Seller, Buyer, AdminProfile, Category, Item, Auction, Bid, Payment, Watchlist, Notification, Review, Dispute, ActivityLog
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Avg, Q
from datetime import timedelta
from Dashboard.decorators import role_required
from django.contrib import messages 
from django.db.models import Sum
from django.contrib.auth import logout
# Create your views here.
@role_required(allowed_roles=['Admin'])
def AdminDashboard(request):
    return render(request,"Dashboard/AdminDashboard.html")

@role_required(allowed_roles=['Buyer'])
def BuyerDashboard(request):
    return render(request,"Dashboard/BuyerDashboard.html")

@role_required(allowed_roles=['Seller'])
def SellerDashboard(request):
    return render(request,"Dashboard/SellerDashboard.html")

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


def auction_list(request):
    auctions = Auction.objects.filter(
        status="ACTIVE",
        end_time__gt=timezone.now()
    ).select_related("item", "item__seller", "item__category").annotate(bid_count=Count('bids'))

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

    return render(request, "Dashboard/auction_list.html", {
        "auctions": auctions,
        "current_sort": sort,
        "current_category": category,
        "categories": Category.objects.all(),
    })


@login_required
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
            Notification.objects.create(
                user=winning_bid.buyer.user,
                message=f"Congratulations! You won '{auction.item.name}' with ₹{winning_bid.amount}. Please complete your payment.",
                notification_type='AUCTION_ENDED'
            )

            # Notify seller
            Notification.objects.create(
                user=auction.item.seller.user,
                message=f"Your auction for '{auction.item.name}' has ended. Winner: {winning_bid.buyer.user.First_name} {winning_bid.buyer.user.Last_name} with ₹{winning_bid.amount}.",
                notification_type='AUCTION_ENDED'
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
            Notification.objects.create(
                user=auction.item.seller.user,
                message=f"A new bid of ₹{bid_amount} was placed on your auction '{auction.item.name}'.",
                notification_type='BID_PLACED',
                auction=auction
            )

            # Notify current buyer their bid was placed successfully
            Notification.objects.create(
                user=buyer.user,
                message=f"Your bid of ₹{bid_amount} on '{auction.item.name}' was placed successfully.",
                notification_type='BID_PLACED',
                auction=auction
            )

            # Notify outbid buyer ONLY if it's a different person
            if outbid_bid and outbid_bid.buyer != buyer:
                Notification.objects.create(
                    user=outbid_bid.buyer.user,
                    message=f"You have been outbid on '{auction.item.name}'. Current bid is ₹{bid_amount}.",
                    notification_type='OUTBID',
                    auction=auction
                )

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
                Category.objects.create(name=name, description=description)
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

    existing_payment = Payment.objects.filter(auction=auction, buyer=buyer).first()
    if existing_payment:
        messages.info(request, "You have already made a payment for this auction.")
        return redirect('BuyerDashboard')

    if request.method == "POST":
        payment_method = request.POST.get('payment_method')
        Payment.objects.create(
            auction=auction,
            buyer=buyer,
            amount=winning_bid.amount,
            payment_method=payment_method,
            status='COMPLETED'
        )
        Notification.objects.create(
            user=auction.item.seller.user,
            message=f"Payment of ₹{winning_bid.amount} received for your auction '{auction.item.name}'.",
            notification_type='PAYMENT',
            auction=auction
        )
        messages.success(request, f"Payment of ₹{winning_bid.amount} completed successfully!")
        return redirect('manage_payments')

    return render(request, 'Dashboard/make_payment.html', {
        'auction': auction,
        'winning_bid': winning_bid,
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
    # Default prefs (you can store these in your User model or a separate UserSettings model)
    notif_prefs = {
        'bid_placed': True,
        'outbid': True,
        'auction_won': True,
        'payment': True,
        'dispute': True,
    }
    privacy_prefs = {
        'public_profile': True,
        'show_bids': False,
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'notifications':
            # Save notification preferences to session (or DB if you add a model)
            request.session['notif_bid_placed'] = 'notif_bid' in request.POST
            request.session['notif_outbid'] = 'notif_outbid' in request.POST
            request.session['notif_won'] = 'notif_won' in request.POST
            request.session['notif_payment'] = 'notif_payment' in request.POST
            request.session['notif_dispute'] = 'notif_dispute' in request.POST
            messages.success(request, '🔔 Notification preferences saved!')

        elif action == 'privacy':
            request.session['public_profile'] = 'public_profile' in request.POST
            request.session['show_bids'] = 'show_bids' in request.POST
            messages.success(request, '🔒 Privacy settings saved!')

        elif action == 'delete_account':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('home')

        return redirect('settings_page')

    # Load from session if previously saved
    notif_prefs = {
        'bid_placed': request.session.get('notif_bid_placed', True),
        'outbid': request.session.get('notif_outbid', True),
        'auction_won': request.session.get('notif_won', True),
        'payment': request.session.get('notif_payment', True),
        'dispute': request.session.get('notif_dispute', True),
    }
    privacy_prefs = {
        'public_profile': request.session.get('public_profile', True),
        'show_bids': request.session.get('show_bids', False),
    }

    return render(request, 'Dashboard/settings.html', {
        'notif_prefs': notif_prefs,
        'privacy_prefs': privacy_prefs,
    })
