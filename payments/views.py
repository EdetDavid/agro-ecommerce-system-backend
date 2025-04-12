from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
import traceback
import requests
import base64

from .models import Payment
from .serializers import PaymentSerializer
from orders.models import Order

# --- Standard PaymentViewSet (For Admin/Internal Use) ---
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related('order', 'order__buyer')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAdminUser]

# --- Helper Function to Get PayPal Auth Token ---
def get_paypal_auth_header():
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET

    if not client_id or not client_secret:
        print("CRITICAL ERROR: PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET missing.")
        return None

    auth_string = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded_auth}"


# --- PayPal Specific Views (Using Direct HTTP Requests) ---

class CreatePayPalOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        django_order_id = request.data.get('order_id')
        if not django_order_id:
            return Response({"error": "Django Order ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.select_related('payment').get(
                id=django_order_id,
                buyer=request.user
            )

            payment = getattr(order, 'payment', None)
            if not payment:
                 print(f"Error: Payment record missing for Order ID {django_order_id}")
                 return Response({"error": "Payment record not found for this order."}, status=status.HTTP_404_NOT_FOUND)

            if payment.status not in ['Pending', 'Failed']:
                 print(f"Warning: Attempt to create PayPal order for payment ID {payment.id} with status '{payment.status}'.")
                 return Response({"error": f"Cannot create PayPal order for payment with status '{payment.status}'."}, status=status.HTTP_400_BAD_REQUEST)

            order_amount = "{:.2f}".format(order.total_price)

            paypal_url = f"https://api.{(settings.PAYPAL_MODE == 'live' and 'paypal.com' or 'sandbox.paypal.com')}/v2/checkout/orders"
            headers = {
                "Content-Type": "application/json",
                "Authorization": get_paypal_auth_header()
            }
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": "USD", # Replace as needed - or make dynamic
                        "value": order_amount
                    },
                    "description": f"AgroEcommerce Order #{order.id}",
                    "custom_id": str(order.id),
                    "invoice_id": f"INV-{order.id}-{payment.id}"
                }]
            }

            print(f"Sending PayPal Create Order request to: {paypal_url}")
            try:
                response = requests.post(paypal_url, headers=headers, json=payload)
                response.raise_for_status()
                paypal_data = response.json()

                paypal_order_id = paypal_data.get('id')
                if not paypal_order_id:
                     print(f"Error: PayPal Create Order response missing 'id'. Response: {paypal_data}")
                     raise Exception("PayPal Create Order response missing 'id'")

                print(f"PayPal order created successfully. PayPal Order ID: {paypal_order_id}")
                payment.paypal_order_id = paypal_order_id
                payment.status = 'Pending PayPal'
                payment.payment_method = 'PayPal'
                payment.save()

                return Response({"id": paypal_order_id}, status=status.HTTP_201_CREATED)


            except requests.exceptions.HTTPError as http_err:
                print("PayPal HTTPError:", http_err)
                error_message = str(http_err)
                try:
                    error_details = response.json()
                    if 'details' in error_details:
                       error_message = ", ".join([d.get('description', d.get('issue', 'Unknown issue')) for d in error_details['details']])
                except: pass

                payment.status = 'Failed'
                payment.save()
                return Response({"error": f"Failed to create PayPal order: {error_message}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except requests.exceptions.RequestException as req_err:
                print("PayPal RequestException:", req_err)
                payment.status = 'Failed'
                payment.save()
                return Response({"error": f"Connection error with PayPal: {req_err}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Order.DoesNotExist:
            print(f"Error: Order ID {django_order_id} not found.")
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            traceback.print_exc()
            if 'payment' in locals() and payment:
                payment.status = 'Failed'
                payment.save()
            return Response({"error": "An unexpected server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CapturePayPalOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        paypal_order_id = request.data.get('orderID')
        django_order_id = request.data.get('djangoOrderID')

        if not paypal_order_id or not django_order_id:
            return Response({"error": "PayPal Order ID and Django Order ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        payment = None
        try:
            payment = Payment.objects.select_related('order').get(
                 paypal_order_id=paypal_order_id,
                 order_id=django_order_id,
                 order__buyer=request.user
             )

            if payment.status == 'Completed':
                print("Payment is already completed.")
                return Response({"message": "Payment already completed."}, status=status.HTTP_200_OK)

            if payment.status != 'Pending PayPal':
                return Response({"error": f"Cannot capture payment with status '{payment.status}'."}, status=status.HTTP_400_BAD_REQUEST)

            capture_url = f"https://api.{(settings.PAYPAL_MODE == 'live' and 'paypal.com' or 'sandbox.paypal.com')}/v2/checkout/orders/{paypal_order_id}/capture"
            headers = {
                "Content-Type": "application/json",
                "Authorization": get_paypal_auth_header()
            }

            print(f"Sending PayPal Capture request to: {capture_url}")

            try:
                capture_response = requests.post(capture_url, headers=headers)
                capture_response.raise_for_status()
                capture_data = capture_response.json()
                paypal_status = capture_data.get('status', 'UNKNOWN').upper()
                print("PayPal Capture API Response:", capture_data)

                if paypal_status == 'COMPLETED':
                    capture_id = None
                    try:
                        purchase_units = capture_data.get('purchase_units', [])
                        if purchase_units and isinstance(purchase_units, list) and len(purchase_units) > 0:
                            payments_info = purchase_units[0].get('payments', {})
                            captures = payments_info.get('captures', [])
                            if captures and isinstance(captures, list) and len(captures) > 0:
                                capture_id = captures[0].get('id')
                    except Exception as extract_err:
                         print(f"Error extracting capture ID: {extract_err}")

                    payment.status = 'Completed'
                    payment.transaction_id = capture_id or paypal_order_id
                    payment.paypal_payment_id = capture_id or paypal_order_id
                    payment.save()

                    order = payment.order
                    order.status = 'Processing'
                    order.save()

                    serializer = PaymentSerializer(payment)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    payment.status = 'Failed'
                    payment.save()
                    error_message = f"PayPal Capture Status: {paypal_status}."
                    return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

            except requests.exceptions.HTTPError as http_err:
                print("PayPal HTTPError during Capture:", http_err)
                error_message = f"PayPal API Error during capture ({http_err})."
                error_data = None # Initialize
                try:
                    error_data = capture_response.json() # Attempt to get JSON error details
                    error_message += f" Details: {error_data}"
                except: pass

                payment.status = 'Failed'
                payment.save()
                # --- Enhanced Error Response ---
                error_response_payload = {"error": error_message} # Base error
                if error_data and isinstance(error_data, dict) and error_data.get('details'):
                    error_response_payload["paypal_error_details"] = error_data.get('details') # Include PayPal details if available

                return Response(error_response_payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except requests.exceptions.RequestException as req_err:
                print("PayPal RequestException during Capture:", req_err)
                payment.status = 'Failed'
                payment.save()
                return Response({"error": f"Connection error during PayPal capture: {req_err}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Payment.DoesNotExist:
             print(f"Error: Payment record not found matching PayPal Order {paypal_order_id}, Django Order {django_order_id} - User: {request.user.id}")
             return Response({"error": "Payment record not found or does not match your account."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("--- Unexpected Exception in CapturePayPalOrderView ---")
            traceback.print_exc()

            try:
                if 'payment' in locals() and payment:
                    payment.status = 'Failed'
                    payment.save()
            except: pass
            return Response({"error": "An unexpected server error occurred during PayPal capture."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
