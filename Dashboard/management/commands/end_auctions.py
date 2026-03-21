from django.core.management.base import BaseCommand
from django.utils import timezone
from Dashboard.models import Auction, Bid, Notification
from Dashboard.emails import send_auction_won_email, send_auction_ended_seller_email

class Command(BaseCommand):
    help = 'Automatically end auctions that have passed their end time'

    def handle(self, *args, **kwargs):
        # Find all active auctions that have passed end time
        expired_auctions = Auction.objects.filter(
            status='ACTIVE',
            end_time__lte=timezone.now()
        )

        count = 0
        for auction in expired_auctions:
            # Mark auction as ended
            auction.status = 'ENDED'
            auction.save()

            # Find winning bid
            winning_bid = Bid.objects.filter(
                auction=auction
            ).order_by('-amount').first()

            if winning_bid:
                # Mark winning bid
                winning_bid.status = 'WINNING'
                winning_bid.save()

                

                # Mark all other bids as lost
                Bid.objects.filter(
                    auction=auction
                ).exclude(id=winning_bid.id).update(status='LOST')

                # Notify winner
                Notification.objects.create(
                    user=winning_bid.buyer.user,
                    message=f"🏆 Congratulations! You won '{auction.item.name}' with ₹{winning_bid.amount}. Please complete your payment.",
                    notification_type='AUCTION_ENDED',
                    auction=auction
                )

                send_auction_won_email(winning_bid.buyer.user, auction, winning_bid.amount)
    

                # Notify seller
                Notification.objects.create(
                    user=auction.item.seller.user,
                    message=f"Your auction for '{auction.item.name}' has ended. Winner: {winning_bid.buyer.user.First_name} {winning_bid.buyer.user.Last_name} with ₹{winning_bid.amount}.",
                    notification_type='AUCTION_ENDED',
                    auction=auction
                )

                send_auction_ended_seller_email(
                    auction.item.seller.user,
                    auction,
                    winning_bid.buyer.user,
                  winning_bid.amount
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Ended auction: {auction.item.name} | Winner: {winning_bid.buyer.user.Email} | Amount: ₹{winning_bid.amount}'
                    )
                )
            else:
                # No bids — just end with no winner
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Ended auction with no bids: {auction.item.name}'
                    )
                )

            count += 1

        if count == 0:
            self.stdout.write('No auctions to end.')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nTotal auctions ended: {count}')
            )