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
        item_form = ItemForm(request.POST)
        auction_form = AuctionForm(request.POST)

        if item_form.is_valid() and auction_form.is_valid():

            item = item_form.save(commit=False)
            item.seller = request.user.seller
            item.save()

            auction = auction_form.save(commit=False)
            
            auction.current_price = auction.starting_price
            auction.save()

            return redirect('SellerDashboard')

    else:
        item_form = ItemForm()
        auction_form = AuctionForm()

    return render(request, 'Dashboard/create_auction.html', {
        'item_form': item_form,
        'auction_form': auction_form
          }
    )


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

def category_management(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("category_management")
    else:
        form = CategoryForm()    
    return render(request,"Dashboard/category_management.html")

 