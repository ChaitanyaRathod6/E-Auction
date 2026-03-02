from django import forms
from .models import Auction,Item,Seller, Buyer, AdminProfile, Category, Bid, Payment, Watchlist, Notification, Review, Dispute, ActivityLog
from django.core.exceptions import ValidationError


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ("user","seller_rating", "total_items_sold")
        widgets = {
            'seller_rating': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0', 'max': '5'}),
            'total_items_sold': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
        }


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ('buyer_rating',)
        widgets = {
            'buyer_rating': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0', 'max': '5'}),
        }


class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ('role',)
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


# =========================
# CATEGORY FORMS
# =========================

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Description'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A category with this name already exists.")
        return name


# =========================
# ITEM FORMS
# =========================

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('name', 'category', 'description', 'condition', 'shipping_cost')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Item name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Detailed description'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.seller = kwargs.pop('seller', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.seller:
            instance.seller = self.seller
        if commit:
            instance.save()
        return instance


# =========================
# AUCTION FORMS
# =========================

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ('starting_price', 'reserve_price', 'current_price', 
                 'bid_increment', 'end_time', 'status')
        widgets = {
            'starting_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'reserve_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'current_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'bid_increment': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        starting_price = cleaned_data.get('starting_price')
        reserve_price = cleaned_data.get('reserve_price')
        current_price = cleaned_data.get('current_price')
        end_time = cleaned_data.get('end_time')

        if reserve_price and starting_price and reserve_price <= starting_price:
            raise ValidationError("Reserve price must be greater than starting price.")

        if current_price and starting_price and current_price < starting_price:
            raise ValidationError("Current price cannot be less than starting price.")

        if end_time and end_time <= timezone.now():
            raise ValidationError("End time must be in the future.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.item:
            instance.item = self.item
        if commit:
            instance.save()
        return instance


class AuctionQuickCreateForm(forms.Form):
    """Simplified form for quick auction creation (from dashboard)"""
    item_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Rolex Daytona'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Item description'})
    )
    condition = forms.ChoiceField(
        choices=Item.CONDITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    starting_price = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'})
    )
    reserve_price = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'})
    )
    bid_increment = forms.DecimalField(
        max_digits=10, decimal_places=2, initial=1.00,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '1.00'})
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'})
    )
    shipping_cost = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'})
    )

    def clean(self):
        cleaned_data = super().clean()
        starting = cleaned_data.get('starting_price')
        reserve = cleaned_data.get('reserve_price')
        
        if reserve and starting and reserve <= starting:
            raise ValidationError("Reserve price must be greater than starting price.")
        
        return cleaned_data


# =========================
# BID FORMS
# =========================

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ('amount',)
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        self.buyer = kwargs.pop('buyer', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if not self.auction:
            raise ValidationError("Auction not specified.")
        
        if self.auction.status != 'ACTIVE':
            raise ValidationError("This auction is no longer active.")
        
        if self.auction.end_time <= timezone.now():
            raise ValidationError("This auction has ended.")
        
        min_allowed = self.auction.current_price + self.auction.bid_increment
        
        if amount < min_allowed:
            raise ValidationError(f"Bid must be at least {min_allowed}")
        
        return amount

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.auction:
            instance.auction = self.auction
        if self.buyer:
            instance.buyer = self.buyer
        
        if commit:
            instance.save()
            # Update auction current price
            self.auction.current_price = instance.amount
            self.auction.save()
            
        return instance


# =========================
# PAYMENT FORMS
# =========================

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('payment_method', 'amount')
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        self.buyer = kwargs.pop('buyer', None)
        super().__init__(*args, **kwargs)
        
        if self.auction:
            self.fields['amount'].initial = self.auction.current_price

    def clean(self):
        cleaned_data = super().clean()
        if self.auction and self.auction.status != 'ENDED':
            raise ValidationError("Payment can only be made for ended auctions.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.auction:
            instance.auction = self.auction
        if self.buyer:
            instance.buyer = self.buyer
        if commit:
            instance.save()
        return instance


# =========================
# WATCHLIST FORMS
# =========================

class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = []  # No fields, just uses buyer and auction from kwargs

    def __init__(self, *args, **kwargs):
        self.buyer = kwargs.pop('buyer', None)
        self.auction = kwargs.pop('auction', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        if Watchlist.objects.filter(buyer=self.buyer, auction=self.auction).exists():
            raise ValidationError("This auction is already in your watchlist.")
        return super().clean()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.buyer = self.buyer
        instance.auction = self.auction
        if commit:
            instance.save()
        return instance


# =========================
# NOTIFICATION FORMS
# =========================

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ('user', 'message', 'notification_type', 'auction', 'bid')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'auction': forms.Select(attrs={'class': 'form-select'}),
            'bid': forms.Select(attrs={'class': 'form-select'}),
        }


class NotificationMarkReadForm(forms.Form):
    """Simple form to mark notifications as read"""
    notification_ids = forms.ModelMultipleChoiceField(
        queryset=Notification.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )


# =========================
# REVIEW FORMS
# =========================

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-input', 
                'min': '1', 
                'max': '5',
                'step': '1'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea', 
                'rows': 4,
                'placeholder': 'Share your experience...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.reviewer = kwargs.pop('reviewer', None)
        self.reviewee = kwargs.pop('reviewee', None)
        self.auction = kwargs.pop('auction', None)
        super().__init__(*args, **kwargs)

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise ValidationError("Rating must be between 1 and 5.")
        return rating

    def clean(self):
        if Review.objects.filter(
            reviewer=self.reviewer, 
            auction=self.auction
        ).exists():
            raise ValidationError("You have already reviewed this auction.")
        return super().clean()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.reviewer = self.reviewer
        instance.reviewee = self.reviewee
        instance.auction = self.auction
        if commit:
            instance.save()
        return instance


# =========================
# DISPUTE FORMS
# =========================

class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ('reason',)
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-textarea', 
                'rows': 5,
                'placeholder': 'Please describe the issue in detail...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        self.raised_by = kwargs.pop('raised_by', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.auction = self.auction
        instance.raised_by = self.raised_by
        if commit:
            instance.save()
        return instance


class DisputeStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


# =========================
# ACTIVITY LOG FORMS
# =========================

class ActivityLogForm(forms.ModelForm):
    class Meta:
        model = ActivityLog
        fields = ('user', 'action')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'action': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
        }


# =========================
# SEARCH/FILTER FORMS
# =========================

class AuctionSearchForm(forms.Form):
    """Form for searching/filtering auctions"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Search auctions...'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Min price'})
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Max price'})
    )
    condition = forms.ChoiceField(
        choices=[('', 'Any')] + Item.CONDITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Any')] + Auction.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('newest', 'Newest'),
            ('ending_soon', 'Ending Soon'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('most_bids', 'Most Bids'),
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise ValidationError("Minimum price cannot be greater than maximum price.")
        
        return cleaned_data
