from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone
from django.shortcuts import redirect
from userauths.models import UserContext
import geoip2.database


class ContextAwareSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        # Only apply this for logged-in users
        if not request.user.is_authenticated:
            return super().process_request(request)

        # Get IP and User-Agent from the request
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

        # Get location using GeoIP2
        try:
            with geoip2.database.Reader(
                'C:\\Users\\pastor sunday\\Documents\\PROJECT SHIT\\PYTHON BUILD\\Banking-App-with-Django\\GeoLite2-City.mmdb'
            ) as reader:
                response = reader.city(ip_address)
                location = response.city.name if response and response.city else "Unknown"
        except Exception:
            location = "Unknown"

        # Try to get existing context
        try:
            context = UserContext.objects.get(user=request.user)
        except UserContext.DoesNotExist:
            context = None

        # If context is missing or has changed, update it
        if context is None or context.ip_address != ip_address or context.user_agent != user_agent or context.location != location:
            UserContext.objects.update_or_create(
                user=request.user,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'location': location
                }
            )

        # Evaluate session risk
        risk_score = self.calculate_risk(ip_address, user_agent, location, request.user)

        # Session expiry and re-authentication logic
        if risk_score > 0.7:
            request.session.set_expiry(300)  # 5 minutes
            if not request.session.get('re_authenticated', False):
                expiry_time = request.session.get_expiry_date()
                time_left = (expiry_time - timezone.now()).total_seconds()
                if time_left <= 60:
                    request.session['session_warning'] = True
                request.session['next'] = request.path  # Store current path to redirect later
                return redirect('userauths:re_authenticate')
        elif risk_score > 0.3:
            request.session.set_expiry(1800)  # 30 minutes
        else:
            request.session.set_expiry(86400)  # 24 hours

        return super().process_request(request)

    def calculate_risk(self, ip, user_agent, location, user):
        try:
            context = UserContext.objects.get(user=user)
            score = 0.0
            if context.ip_address != ip:
                score += 0.3
            if context.user_agent != user_agent:
                score += 0.2
            if context.location != location and location != "Unknown":
                score += 0.4
            return min(score, 1.0)
        except UserContext.DoesNotExist:
            return 0.9
