from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
# Add necessary parsers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer
import traceback  # For detailed error logging


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited (Admins primarily).
    """
    queryset = User.objects.all().order_by('-date_joined').select_related('profile')
    serializer_class = UserSerializer
    # Restrict general user access
    permission_classes = [permissions.IsAdminUser]

    # Add custom actions if needed, e.g., for non-admins to view limited user data


class RegisterView(APIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [AllowAny]  # Allow anyone to register

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                # Profile should be created automatically by the signal now
                print(f"User registered successfully: {user.username}")
                # Return user data (excluding password) using the serializer's representation
                user_data = UserSerializer(
                    user, context={'request': request}).data
                return Response(user_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error during user save or profile creation: {e}")
                traceback.print_exc()  # Log the full traceback
                return Response({"error": "An internal error occurred during registration."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"Registration validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Use GenericViewSet as we only define custom actions
class ProfileViewSet(viewsets.GenericViewSet):
    """
    API endpoint for retrieving and updating the logged-in user's profile.
    Uses the /api/users/profile/me/ endpoint.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    # Add parsers to handle file uploads (FormData) along with JSON
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # No need for a default queryset or list/create methods if only using 'me'
    # queryset = Profile.objects.all() # Keep if needed for other actions

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request, *args, **kwargs):
        """
        Retrieve or update the profile for the currently authenticated user.
        Handles GET (retrieve), PUT (full update), PATCH (partial update).
        """
        try:
            # Use related name 'profile' from User model or get_or_create
            # Using get_or_create is safer as it handles users who might lack a profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            if created:
                print(
                    f"Profile created on demand for user {request.user.username} (ID: {request.user.id})")

        except Profile.DoesNotExist:  # Should not happen with get_or_create, but good practice
            print(
                f"Error: Profile DoesNotExist for user {request.user.username} (ID: {request.user.id})")
            return Response({"error": "Profile not found for this user."},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(
                f"Error retrieving profile for user {request.user.username} (ID: {request.user.id}): {e}")
            traceback.print_exc()
            return Response({"error": "An internal error occurred while retrieving the profile."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Handle GET request
        if request.method == 'GET':
            # Pass request to serializer context for absolute URLs
            serializer = self.get_serializer(
                profile, context={'request': request})
            return Response(serializer.data)

        # Handle PUT/PATCH requests
        partial_update = request.method == 'PATCH'
        # Pass request context AND existing instance to serializer
        serializer = self.get_serializer(
            instance=profile,      # Pass the existing profile instance
            data=request.data,
            partial=partial_update,
            context={'request': request}  # Pass request for URL building
        )

        if serializer.is_valid():
            try:
                updated_profile = serializer.save()
                print(
                    f"Profile updated successfully for user {request.user.username} (ID: {request.user.id})")
                # Return the updated data, including potentially new profile_picture_url
                # Serialize the *updated* instance again to ensure URL is correct
                response_serializer = self.get_serializer(
                    updated_profile, context={'request': request})
                return Response(response_serializer.data)
            except Exception as e:
                print(
                    f"Error saving profile update for user {request.user.username} (ID: {request.user.id}): {e}")
                traceback.print_exc()
                return Response({"error": f"Failed to save profile update: {str(e)}"},
                                status=status.HTTP_400_BAD_REQUEST)  # Or 500 depending on error
        else:
            print(
                f"Profile update validation errors for user {request.user.username} (ID: {request.user.id}): {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
