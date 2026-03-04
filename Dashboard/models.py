from django.db import models
from core.models import User
from django.utils import timezone


# =========================
# ROLE PROFILES
# =========================

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    seller_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_items_sold = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.Email


class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    buyer_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def __str__(self):
        return self.user.Email


class AdminProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPER', 'Super Admin'),
        ('MOD', 'Moderator'),
        ('SUB', 'Sub Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MOD')

    def __str__(self):
        return f"{self.user.Email} ({self.role})"


# =========================
# CATEGORY
# =========================

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================
# ITEM
# =========================

class Item(models.Model):
    CONDITION_CHOICES = [
        ('NEW', 'New'),
        ('USED', 'Used'),
        ('REFURB', 'Refurbished'),
    ]

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")

    name = models.CharField(max_length=200)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)

    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# =========================
# AUCTION
# =========================

class Auction(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ENDED', 'Ended'),
        ('CANCELLED', 'Cancelled'),
    ]

    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="auction")

    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2)

    current_price = models.DecimalField(max_digits=10, decimal_places=2)

    bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)

    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    winner = models.ForeignKey(
        Buyer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_auctions"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Auction - {self.item.name}"


# =========================
# BID
# =========================

class Bid(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('OUTBID', 'Outbid'),
        ('WINNING', 'Winning'),
        ('LOST', 'Lost'),
    ]

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='bids')

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    bid_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bid_time']

    def __str__(self):
        return f"{self.buyer.user.Email} - {self.amount}"


# =========================
# PAYMENT
# =========================

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    METHOD_CHOICES = [
        ('CARD', 'Credit Card'),
        ('PAYPAL', 'PayPal'),
        ('UPI', 'UPI'),
        ('NETBANK', 'Net Banking'),
    ]

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='payments')
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"


# =========================
# WATCHLIST
# =========================

class Watchlist(models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='watchlists')
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='watchlists')

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['buyer', 'auction'],
                name='unique_watchlist_entry'
            )
        ]

    def __str__(self):
        return f"{self.buyer.user.Email} → {self.auction}"


# =========================
# NOTIFICATION
# =========================

class Notification(models.Model):

    NOTIFICATION_TYPE_CHOICES = [
        ('BID_PLACED', 'Bid Placed'),
        ('OUTBID', 'Outbid'),
        ('AUCTION_ENDED', 'Auction Ended'),
        ('PAYMENT', 'Payment'),
        ('GENERAL', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='GENERAL'
    )

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, null=True, blank=True)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, null=True, blank=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user.Email}"


# =========================
# REVIEW
# =========================

class Review(models.Model):
    rating = models.PositiveIntegerField()
    comment = models.TextField()

    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews_given"
    )

    reviewee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews_received"
    )

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.Email}"


# =========================
# DISPUTE
# =========================

class Dispute(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE)

    reason = models.TextField()
    status = models.CharField(max_length=20, default="OPEN")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dispute on {self.auction}"


# =========================
# ACTIVITY LOG
# =========================

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.Email} - {self.action}"


        