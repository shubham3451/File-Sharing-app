from rest_framework.views import APIView
from app.serializers import *
from app.utils import *
from rest_framework.response import Response
from rest_framework.permissions import  IsAuthenticated
from django.shortcuts import get_object_or_404
import stripe
from django.shortcuts import redirect
import json
from django.conf import settings
from django.http import HttpResponse

class PlanView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self):
        try:
            plans = Plan.objects.all()
            serializer = PlanSerializer(plans, many=True)
            if serializer.is_valid():
                return Response({"message":"success",'data':serializer.data, 'status_code':201})
        except  Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})
        
class MembershipView(APIView):
     permission_classes = [IsAuthenticated]
     def post(self, request, plan_id):
         try:
           stripe.api_key = settings.STRIPE_API_KEY
           plan = get_object_or_404(Plan, id=plan_id)
           
           
           YOUR_DOMAIN = 'http://localhost:8000'
           
           
           
           checkout_session = stripe.checkout.Session.create(
                 line_items=[
                     {
                         # Provide the exact Price ID (for example, price_1234) of the product you want to sell
                         'price': f'{plan.price}',
                         'quantity': 1,
                     },
                 ],
                 mode='payment',
                 success_url=YOUR_DOMAIN + '/success.html',
                 cancel_url=YOUR_DOMAIN + '/cancel.html',
                 metadata={
                    "user_id": str(request.user.id),
                    "plan_id": str(plan.id),
                }
            
             )
         except Exception as e:
             return str(e)
     
         return redirect(checkout_session.url, code=303)


class StripeWebhookView(APIView):
    def post(self, request):
        
           stripe.api_key = settings.STRIPE_API_KEY
           endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
       
           event = None
           payload = request.data
       
           try:
               event = json.loads(payload)
           except json.decoder.JSONDecodeError as e:
               print('⚠️  Webhook error while parsing basic request.' + str(e))
               return HttpResponse(success=False)
           if endpoint_secret:
               # Only verify the event if there is an endpoint secret defined
               # Otherwise use the basic event deserialized with json
               sig_header = request.headers.get('stripe-signature')
               try:
                   event = stripe.Webhook.construct_event(
                       payload, sig_header, endpoint_secret
                   )
               except stripe.error.SignatureVerificationError as e:
                   print('⚠️  Webhook signature verification failed.' + str(e))
                   return HttpResponse(success=False)
       
           # Handle the event
           try:
              if event and event['type'] == 'payment_intent.succeeded':
                  payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
                  print('Payment for {} succeeded'.format(payment_intent['amount']))
                  session = event['data']['object']
                  user_id = session['metadata']['user_id']
                  plan_id = session['metadata']['plan_id']
                  try:
                      user = User.objects.get(id=user_id)
                      plan = Plan.objects.get(id=plan_id)
                  except (User.DoesNotExist, Plan.DoesNotExist):
                      return HttpResponse(status=400)
                  if Membership.objects.filter(user=user, plan=plan, is_active=True).exists():
                      return HttpResponse(status=200)  # Already created
                  # Create membership
                  today = timezone.now().date()
                  expiry = today.replace(year=today.year + 1)
          
                  Membership.objects.create(
                      user=user,
                      plan=plan,
                      is_active=True,
                      purchase_date=today,
                      expiry_date=expiry
                  )
                         # Then define and call a method to handle the successful payment intent.
                  # handle_payment_intent_succeeded(payment_intent)
              elif event['type'] == 'payment_method.attached':
                  payment_method = event['data']['object']  # contains a stripe.PaymentMethod
                  # Then define and call a method to handle the successful attachment of a PaymentMethod.
                  # handle_payment_method_attached(payment_method)
              else:
                  # Unexpected event type
                  print('Unhandled event type {}'.format(event['type']))
           except Exception as e:
              print("Webhook processing error:", e)
              return HttpResponse(status=500)
           return HttpResponse(success=True)
       