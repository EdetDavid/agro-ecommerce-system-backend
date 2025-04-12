from rest_framework import serializers
from .models import User, Profile  # Import the custom User model


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Use the custom User model
        fields = ['id', 'username', 'first_name', 'last_name', 'email',
                  'password', 'is_farmer', 'is_buyer']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Determine buyer status based on farmer status
        is_farmer = validated_data.get('is_farmer', False)
        # If you want ONLY farmer OR buyer, use: is_buyer = not is_farmer
        # If a farmer CAN also be a buyer, use: is_buyer = validated_data.get('is_buyer', True)
        # Default: Buyer if not Farmer
        is_buyer = validated_data.get('is_buyer', not is_farmer)

        user = User.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data['email'],
            password=validated_data['password'],
            is_farmer=is_farmer,
            is_buyer=is_buyer,
        )
        # Profile creation is now handled by the signal in models.py
        # Profile.objects.create(user=user) # Remove this line if using signal
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_farmer = serializers.BooleanField(
        source='user.is_farmer', read_only=True)
    is_buyer = serializers.BooleanField(source='user.is_buyer', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    profile_picture = serializers.ImageField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'phone_number', 'address',
            'is_farmer', 'is_buyer',  # Still read-only representation
            'profile_picture',
            'profile_picture_url'
        ]
        read_only_fields = ['id', 'user', 'is_farmer',
                            'is_buyer', 'profile_picture_url']

    def get_profile_picture_url(self, obj):
        # ... (same as before) ...
        request = self.context.get('request')
        picture_url = obj.profile_picture_url
        if request and picture_url:
            return request.build_absolute_uri(picture_url)
        return picture_url

    def update(self, instance, validated_data):
        # Handle profile picture update
        picture_file = validated_data.pop('profile_picture', Ellipsis)
        instance.phone_number = validated_data.get(
            'phone_number', instance.phone_number)
        instance.address = validated_data.get('address', instance.address)

        if picture_file is not Ellipsis:
            if picture_file is None:
                # Clear picture logic...
                if instance.profile_picture and instance.profile_picture.name != Profile._meta.get_field('profile_picture').default:
                    instance.profile_picture.delete(save=False)
                instance.profile_picture = None
            else:
                # Update picture logic...
                if instance.profile_picture and hasattr(instance.profile_picture, 'path') and \
                   instance.profile_picture.name != Profile._meta.get_field('profile_picture').default:
                    try:
                        instance.profile_picture.delete(save=False)
                    except Exception as e:
                        print(
                            f"Warning: Could not delete old profile picture {instance.profile_picture.name}: {e}")
                instance.profile_picture = picture_file
        instance.save()  # Save profile fields first

        # --- Manually Handle Role Updates from Request Data ---
        # Access the original request data from the context
        request_data = self.context['request'].data
        user_instance = instance.user
        user_updated = False  # Flag to check if user needs saving

        # Check if 'is_farmer' was sent in the request payload
        if 'is_farmer' in request_data:
            try:
                # Convert potential string ('true'/'false') to boolean
                new_is_farmer = str(request_data['is_farmer']).lower() in [
                    'true', '1', 't', 'y', 'yes']
                if user_instance.is_farmer != new_is_farmer:
                    user_instance.is_farmer = new_is_farmer
                    # --- Logic: If farmer=false, ensure buyer=true (or vice-versa if exclusive) ---
                    # This depends on your business logic: can someone be both? Or neither?
                    # Example: If roles are mutually exclusive (either farmer OR buyer)
                    # user_instance.is_buyer = not new_is_farmer
                    # Example: If farmer=false means they MUST be a buyer
                    if not new_is_farmer:
                        user_instance.is_buyer = True
                    user_updated = True
            except Exception as e:
                print(f"Error processing 'is_farmer' from request data: {e}")

        # Check if 'is_buyer' was sent (Only relevant if user can explicitly set buyer status independently)
        # If roles are exclusive (like above), this check might be redundant or need adjustment
        if 'is_buyer' in request_data:
            try:
                new_is_buyer = str(request_data['is_buyer']).lower() in [
                    'true', '1', 't', 'y', 'yes']
                if user_instance.is_buyer != new_is_buyer:
                    user_instance.is_buyer = new_is_buyer
                    # Example: If buyer=false means they MUST be a farmer
                    # if not new_is_buyer:
                    #    user_instance.is_farmer = True
                    user_updated = True
            except Exception as e:
                print(f"Error processing 'is_buyer' from request data: {e}")

        # Save the User model only if role fields were changed
        if user_updated:
            # Specify which fields to update for efficiency and safety
            update_fields = ['is_farmer', 'is_buyer']
            user_instance.save(update_fields=update_fields)
            print(f"User roles updated for {user_instance.username}")

        return instance
