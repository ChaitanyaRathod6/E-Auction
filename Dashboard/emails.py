from django.core.mail import send_mail
from django.conf import settings


def send_bid_placed_email(user, auction, amount):
    send_mail(
        subject=f'✅ Bid Placed — {auction.item.name}',
        message=f'''
Hi {user.First_name},

Your bid of ₹{amount} on "{auction.item.name}" was placed successfully.

Auction ends: {auction.end_time.strftime("%d %b %Y, %I:%M %p")}
Current price: ₹{auction.current_price}

Good luck!
— Auctora Team
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.Email],
        fail_silently=True,
    )


def send_outbid_email(user, auction, new_amount):
    send_mail(
        subject=f'⚠️ You have been outbid — {auction.item.name}',
        message=f'''
Hi {user.First_name},

You have been outbid on "{auction.item.name}".

New highest bid: ₹{new_amount}
Auction ends: {auction.end_time.strftime("%d %b %Y, %I:%M %p")}

Place a higher bid now to stay in the race!
— Auctora Team
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.Email],
        fail_silently=True,
    )


def send_auction_won_email(user, auction, amount):
    send_mail(
        subject=f'🏆 You Won — {auction.item.name}',
        message=f'''
Hi {user.First_name},

Congratulations! You won the auction for "{auction.item.name}" with ₹{amount}.

Please complete your payment as soon as possible.

Login to Auctora → Go to Payments → Pay Now

— Auctora Team
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.Email],
        fail_silently=True,
    )


def send_payment_received_email(seller, auction, amount):
    send_mail(
        subject=f'💰 Payment Received — {auction.item.name}',
        message=f'''
Hi {seller.First_name},

Payment of ₹{amount} has been received for your auction "{auction.item.name}".

Login to Auctora to view payment details.

— Auctora Team
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[seller.Email],
        fail_silently=True,
    )


def send_auction_ended_seller_email(seller, auction, winner, amount):
    send_mail(
        subject=f'🔔 Auction Ended — {auction.item.name}',
        message=f'''
Hi {seller.First_name},

Your auction for "{auction.item.name}" has ended.

Winner: {winner.First_name} {winner.Last_name}
Winning bid: ₹{amount}

The buyer has been notified to complete payment.

— Auctora Team
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[seller.Email],
        fail_silently=True,
    )

def send_refund_request_email(seller, buyer, auction, amount):
    try:
        send_mail(
        subject=f'💰 Refund Requested — {auction.item.name}',
        message=f'''
        Hi {seller.First_name},

        {buyer.First_name} {buyer.Last_name} has requested a refund for "{auction.item.name}".

        Refund Amount: ₹{amount}

        Please login to Auctora and go to Payments to review and approve or reject this request.

        — Auctora Team
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[seller.Email],
        fail_silently=False,
        )
    except Exception as e:
        print("Error sending refund request email:", e)


def send_refund_approved_email(buyer, auction, amount):
    send_mail(
        subject=f'✅ Refund Approved — {auction.item.name}',
        message=f'''
Hi {buyer.First_name},

Great news! Your refund request for "{auction.item.name}" has been approved.

Refund Amount: ₹{amount}

The refund will be processed shortly. Please allow a few business days for the amount to reflect in your account.

— Auctora Team
        ''',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[buyer.Email],
        fail_silently=False,
    )    