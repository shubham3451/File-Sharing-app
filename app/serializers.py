from rest_framework import serializers
from app.models.user import OTP
from app.models import *
from app.models.file import *
from app.models.membership import *
from .utils import activation_link, send_activation_mail


class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password')
        
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            password=validated_data['password'],
        )
        activationlink = activation_link(user)
        subject="Activate your Account"
        send_activation_mail(user, activationlink, subject)
        return user

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('user', 'otp', 'created_at', 'is_verified')

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('user', 'name', 'created_at')

class FileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileVersion
        fields = '__all__' #('file', 'version', 'size', 'type', 'folder','file_data', 'uploaded_at', 'is_infected')

class FolderSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
         model = Folder
         fields = '__all__'


class FolderDetailSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
  #  files = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'children']

    def get_children(self, obj):
        children = obj.children.all()
        return FolderSerializer(children, many=True).data

    # def get_files(self, obj):
    #     return FileSerializer(obj.files.all(), many=True).data


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('user', 'plan','purchase_date', 'expiry_date','auto_renew', 'is_active')

class FileShareSerializer(serializers.ModelSerializer):
    shared_with = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    class Meta:
        model = FileShare
        fields = '__all__'

class TrashSerializer(serializers.ModelSerializer):
    class Meta:
         model = Trash
         fields = '__all__'

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'