from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone
from django.shortcuts import redirect
from django.conf import settings
from userauths.models import UserContext
import geoip2.database

INACTIVITY_TIMEOUT_SECONDS = 60  # 10 minutes

class ContextAwareSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return super().process_request(request)

        # --- Inactivity Timeout Check ---
        last_activity = request.session.get('last_activity')
        now = timezone.now().timestamp()

        if last_activity and (now - last_activity > INACTIVITY_TIMEOUT_SECONDS):
            from django.contrib.auth import logout
            logout(request)
            request.session.flush()
            return redirect('userauths:sign-in')  # or redirect to 'session_expired' page

        # Update session timestamp on activity
        request.session['last_activity'] = now

        # --- Context Awareness ---
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        try:
            with geoip2.database.Reader(
                'C:\\Users\\pastor sunday\\Documents\\PROJECT SHIT\\PYTHON BUILD\\Banking-App-with-Django\\GeoLite2-City.mmdb'
            ) as reader:
                response = reader.city(ip_address)
                location = response.city.name if response and response.city else "Unknown"
        except Exception:
            location = "Unknown"

        # Check stored user context
        try:
            context = UserContext.objects.filter(user=request.user).latest('last_seen')
            if context.ip_address != ip_address or context.user_agent != user_agent or context.location != location:
                UserContext.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'location': location
                    }
                )
        except UserContext.DoesNotExist:
            UserContext.objects.update_or_create(
                user=request.user,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'location': location
                }
            )

        # Calculate risk score
        risk_score = self.calculate_risk(ip_address, user_agent, location, request.user)

        # Apply session expiry rules
        if risk_score > 0.7:
            request.session.set_expiry(30)  # 5 minutes
            if 're_authenticated' not in request.session:
                expiry_time = request.session.get_expiry_date()
                if expiry_time and (expiry_time - timezone.now()).total_seconds() <= 60:
                    request.session['session_warning'] = True
                return redirect('userauths:re_authenticate')
        elif risk_score > 0.3:
            request.session.set_expiry(180)  # 30 minutes
        else:
            request.session.set_expiry(8640)  # 24 hours

        return super().process_request(request)

    def calculate_risk(self, ip, user_agent, location, user):
        try:
            context = UserContext.objects.filter(user=user).latest('last_seen')
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
