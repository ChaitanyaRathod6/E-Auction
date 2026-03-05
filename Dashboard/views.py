from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import ItemForm, AuctionForm, BidForm,SellerProfileForm,BuyerProfileForm,AdminProfileForm,CategoryForm,AuctionQuickCreateForm,PaymentForm,WatchlistForm,NotificationForm,NotificationMarkReadForm,ReviewForm,DisputeForm,DisputeStatusUpdateForm,ActivityLogForm,AuctionSearchForm
from .models import Auction,Bid
from core.models import User
from django.utils import timezone
from .decorators import role_required
from django.shortcuts import get_object_or_404
from .models import Seller, Buyer, AdminProfile, Category, Item, Auction, Bid, Payment, Watchlist, Notification, Review, Dispute, ActivityLog
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Avg, Q
from datetime import timedelta
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
    ).select_related("item", "item__seller")

    return render(request, "Dashboard/auction_list.html", {
        "auctions": auctions
    })


@login_required
def auction_detail(request, pk):
    auction = get_object_or_404(Auction, pk=pk)

    if auction.end_time <= timezone.now():
        auction.status = "ENDED"
        auction.save()

    if request.method == "POST":
        print("=== POST HIT ===")
        print("Status:", auction.status)
        print("End time:", auction.end_time)
        print("Now:", timezone.now())
        print("bid_amount raw:", request.POST.get("bid_amount"))

        try:
            buyer = request.user.buyer
            print("Buyer:", buyer)
        except Exception as e:
            print("BUYER ERROR:", e)
            messages.error(request, "Only registered buyers can place bids.")
            return redirect("auction_detail", pk=auction.pk)

        bid_amount = request.POST.get("bid_amount")
        if bid_amount:
            bid_amount = float(bid_amount)
            min_required = float(auction.current_price) + float(auction.bid_increment)
            print("bid_amount:", bid_amount)
            print("min_required:", min_required)
            print("status check passes?", auction.status == "ACTIVE")

            if auction.status != "ACTIVE":
                print("FAILED: auction not active")
                messages.error(request, "This auction is no longer active.")
                return redirect("auction_detail", pk=auction.pk)

            if bid_amount < min_required:
                print("FAILED: bid too low")
                messages.error(request, f"Your bid must be at least ₹{min_required}")
                return redirect("auction_detail", pk=auction.pk)

            Bid.objects.create(auction=auction, buyer=buyer, amount=bid_amount)
            auction.current_price = bid_amount
            auction.save()
            print("BID CREATED SUCCESSFULLY")
            messages.success(request, "Bid placed successfully!")
            return redirect("auction_detail", pk=auction.pk)
        else:
            print("FAILED: bid_amount is empty")

    bids = auction.bids.all().order_by('-amount')
    return render(request, "Dashboard/auction_detail.html", {
        "auction": auction,
        "bids": bids,
    })

@login_required
def seller_profile(request):
    try:
        seller = request.user.seller
    except ObjectDoesNotExist:
        messages.error(request, "You don't have a seller profile.")
        return redirect('become_seller')

    if request.method == "POST":
        # ✅ Save User model fields directly
        request.user.First_name = request.POST.get('First_name')
        request.user.Last_name = request.POST.get('Last_name')
        request.user.Mobile_number = request.POST.get('Mobile_number')
        request.user.Gender = request.POST.get('Gender')
        request.user.save()

        # ✅ Save Seller model fields via form
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
    }
    return render(request, "Dashboard/seller_profile.html", context)

@login_required
def buyer_profile(request):
    try:
        buyer = request.user.buyer
    except ObjectDoesNotExist:
        messages.error(request, "You don't have a buyer profile.")
        return redirect('home')

    # ← PASTE HERE, replacing your existing if request.method == "POST": block
    if request.method == "POST":
        print("=== FILES ===", request.FILES)
        print("=== profile_photo in FILES ===", request.FILES.get('profile_photo'))
        
        request.user.First_name = request.POST.get('First_name')
        request.user.Last_name = request.POST.get('Last_name')
        request.user.Mobile_number = request.POST.get('Mobile_number')
        request.user.Gender = request.POST.get('Gender')

        if request.FILES.get('profile_photo'):
            request.user.profile_photo = request.FILES['profile_photo']
            print("=== photo set to ===", request.user.profile_photo)

        request.user.save()
        print("=== saved ===", request.user.profile_photo)
        print("=== url ===", request.user.profile_photo.url if request.user.profile_photo else "NO PHOTO")

        form = BuyerProfileForm(request.POST, request.FILES, instance=buyer)
        if form.is_valid():
            form.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("buyer_profile")
    else:
        form = BuyerProfileForm(instance=buyer)

    context = {
        "form": form,
        "buyer": buyer,
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
def manage_auctions(request):
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
    qs = Auction.objects.select_related('item','item__seller__user','item__category').prefetch_related('bids')
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    context = {
        'auctions': qs.order_by('-created_at'),
        'total_auctions': Auction.objects.count(),
        'active_auctions': Auction.objects.filter(status='ACTIVE').count(),
        'ended_auctions': Auction.objects.filter(status='ENDED').count(),
        'cancelled_auctions': Auction.objects.filter(status='CANCELLED').count(),
    }
    return render(request, 'Dashboard/manage_auctions.html', context)

@login_required
def manage_items(request):
    if request.method == "POST":
        if request.POST.get('action') == 'delete_item':
            Item.objects.filter(id=request.POST.get('item_id')).delete()
            messages.success(request, 'Item deleted.')
        return redirect('manage_items')
    qs = Item.objects.select_related('seller__user', 'category')
    if request.GET.get('condition'):
        qs = qs.filter(condition=request.GET['condition'])
    context = {
        'items': qs.order_by('-created_at'),
        'total_items': Item.objects.count(),
        'new_items': Item.objects.filter(condition='NEW').count(),
        'used_items': Item.objects.filter(condition='USED').count(),
        'refurb_items': Item.objects.filter(condition='REFURB').count(),
    }
    return render(request, 'Dashboard/manage_items.html', context)

@login_required
def manage_bids(request):
    context = {
        'bids': Bid.objects.select_related('buyer__user','auction__item').order_by('-bid_time'),
        'total_bids': Bid.objects.count(),
        'winning_bids': Bid.objects.filter(status='WINNING').count(),
        'outbid_bids': Bid.objects.filter(status='OUTBID').count(),
        'lost_bids': Bid.objects.filter(status='LOST').count(),
    }
    return render(request, 'Dashboard/manage_bids.html', context)

@login_required
def manage_payments(request):
    if request.method == "POST":
        p = Payment.objects.get(id=request.POST.get('payment_id'))
        p.status = request.POST.get('new_status')
        p.save()
        messages.success(request, 'Payment status updated.')
        return redirect('manage_payments')
    qs = Payment.objects.select_related('buyer__user','auction__item')
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    context = {
        'payments': qs.order_by('-payment_date'),
        'total_payments': Payment.objects.count(),
        'completed_payments': Payment.objects.filter(status='COMPLETED').count(),
        'pending_payments': Payment.objects.filter(status='PENDING').count(),
        'failed_payments': Payment.objects.filter(status='FAILED').count(),
    }
    return render(request, 'Dashboard/manage_payments.html', context)

@login_required
def manage_disputes(request):
    if request.method == "POST":
        d = Dispute.objects.get(id=request.POST.get('dispute_id'))
        d.status = request.POST.get('new_status')
        d.save()
        messages.success(request, 'Dispute status updated.')
        return redirect('manage_disputes')
    qs = Dispute.objects.select_related('raised_by','auction__item')
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    context = {
        'disputes': qs.order_by('-created_at'),
        'total_disputes': Dispute.objects.count(),
        'open_disputes': Dispute.objects.filter(status='OPEN').count(),
        'resolved_disputes': Dispute.objects.filter(status='RESOLVED').count(),
        'closed_disputes': Dispute.objects.filter(status='CLOSED').count(),
    }
    return render(request, 'Dashboard/manage_disputes.html', context)

@login_required
def manage_notifications(request):
    if request.method == "POST" and request.POST.get('action') == 'send':
        msg = request.POST.get('message')
        ntype = request.POST.get('notification_type', 'GENERAL')
        uid = request.POST.get('user_id')
        if uid == 'all':
            for u in User.objects.all():
                Notification.objects.create(user=u, message=msg, notification_type=ntype)
            messages.success(request, f'Notification sent to all users.')
        else:
            Notification.objects.create(user=User.objects.get(id=uid), message=msg, notification_type=ntype)
            messages.success(request, 'Notification sent.')
        return redirect('manage_notifications')
    context = {
        'notifications': Notification.objects.select_related('user').order_by('-created_at'),
        'all_users': User.objects.all(),
    }
    return render(request, 'Dashboard/manage_notifications.html', context)

@login_required
def manage_reviews(request):
    if request.method == "POST":
        Review.objects.filter(id=request.POST.get('review_id')).delete()
        messages.success(request, 'Review deleted.')
        return redirect('manage_reviews')
    qs = Review.objects.select_related('reviewer','reviewee','auction__item')
    if request.GET.get('rating'):
        qs = qs.filter(rating=request.GET['rating'])
    avg = Review.objects.aggregate(a=Avg('rating'))['a']
    context = {
        'reviews': qs.order_by('-created_at'),
        'total_reviews': Review.objects.count(),
        'five_star': Review.objects.filter(rating=5).count(),
        'one_star': Review.objects.filter(rating=1).count(),
        'avg_rating': round(avg, 1) if avg else 0,
    }
    return render(request, 'Dashboard/manage_reviews.html', context)

@login_required
def manage_watchlist(request):
    qs = Watchlist.objects.select_related('buyer__user','auction__item__category')
    most = qs.values('auction__item__name').annotate(c=Count('id')).order_by('-c').first()
    context = {
        'watchlist': qs.order_by('-added_at'),
        'total_watchlist': qs.count(),
        'unique_buyers': qs.values('buyer').distinct().count(),
        'unique_auctions': qs.values('auction').distinct().count(),
        'most_watched': most['auction__item__name'][:15] + '…' if most else '-',
    }
    return render(request, 'Dashboard/manage_watchlist.html', context)

@login_required
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
 