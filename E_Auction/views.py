from django.http import HttpResponse  
from django.shortcuts import render
from Dashboard.models import Category, Auction
from django.utils import timezone
from django.db.models import Count

def home(request):
    categories = Category.objects.all()[:4]
    all_categories = Category.objects.all()
    
    live_auctions = Auction.objects.filter(
        status='ACTIVE',
        end_time__gt=timezone.now()
    ).select_related('item', 'item__category').annotate(
        bid_count=Count('bids')
    ).order_by('end_time')[:3]

    return render(request, 'e-auction/home.html', {
        'categories': categories,
        'all_categories': all_categories,
        'live_auctions': live_auctions,
    })


