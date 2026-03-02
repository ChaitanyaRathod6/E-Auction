from django.contrib import admin
from .models import (Seller, Buyer, AdminProfile, Category, Item, Auction, Bid, Payment, Watchlist,
                     Notification, Review, Dispute, ActivityLog)
# Register your models here.
admin.site.register(Category)
admin.site.register(Seller)
admin.site.register(Buyer)
admin.site.register(AdminProfile)
admin.site.register(Item)
admin.site.register(Auction)
admin.site.register(Bid)
admin.site.register(Payment)
admin.site.register(Watchlist)
admin.site.register(Notification)
admin.site.register(Review)
admin.site.register(Dispute)
admin.site.register(ActivityLog)