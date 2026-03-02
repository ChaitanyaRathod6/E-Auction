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
        bid_amount = request.POST.get("bid_amount")

        if bid_amount:
            bid_amount = float(bid_amount)

            if auction.status == "ACTIVE":

                new_price = float(auction.current_price) + bid_amount

                Bid.objects.create(
                auction=auction,
                buyer=request.user.buyer,
                amount=bid_amount
                )

                auction.current_price = new_price
                auction.save()

                return redirect("auction_detail", pk=auction.pk)
    bids = auction.bids.all()

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
        form = SellerProfileForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("seller_profile")
    else:
        form = SellerProfileForm(instance=seller)
    
    # Pass user and seller to template
    context = {
        "form": form,
        "user": request.user,  # Add this
        "seller": seller,       # Add this
    }
    
    return render(request, "Dashboard/seller_profile.html", context)

def buyer_profile(request):
    if request.method == "POST":
        form = BuyerProfileForm(request.POST, instance=request.user.buyer)

        if form.is_valid():
            form.save()
            return redirect("buyer_profile")
    else:
        form = BuyerProfileForm(instance=request.user.buyer)    
    return render(request,"Dashboard/buyer_profile.html")   

def admin_profile(request):
    if request.method == "POST":
        form = AdminProfileForm(request.POST, instance=request.user.adminprofile)

        if form.is_valid():
            form.save()
            return redirect("admin_profile")
    else:
        form = AdminProfileForm(instance=request.user.adminprofile)
    return render(request,"Dashboard/admin_profile.html", {"form": form})

def category_management(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("category_management")
    else:
        form = CategoryForm()    
    return render(request,"Dashboard/category_management.html")

 