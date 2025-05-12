from rest_framework.views import APIView
from app.serializers import *
from app.utils import *
from rest_framework.response import Response
from app.models.file import *
from rest_framework import status
from rest_framework.permissions import  IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.http import FileResponse
import secrets
import mimetypes
from app.documents import FileVersionDocument



class Files( APIView, FileAccessLoggingMixin):
    permission_classes = [IsAuthenticated]
    def get(self, request, file_id=None):
        if file_id is None:
            try:
              files = File.objects.filter(user=request.user)
              serializer = FileSerializer(files, many=True)
              return Response({'data':serializer.data, "status_code":200}, status=status.HTTP_200_OK)
            except Exception as e:
              error_message = f"Error : {str(e)}"
              return Response({"error":error_message, "status":500})
        try:
          latest_version = FileVersion.objects.filter(file=file_id).order_by('-version').first()
          fileversion = get_object_or_404(FileVersion, id=file_id, version=latest_version)
          if is_file_infected(fileversion):
                return Response({"message":"This file is infected"}, status=status.HTTP_403_FORBIDDEN)
          serializer = FileVersionSerializer(fileversion)
          return Response({'data':serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})
    
    def post(self, request):
        try:
            name = request.data.get('name')
            folder_id = request.data.get('folder_id')
            file_data = request.FILES['file_data']
            if not (name and file_data):
                return Response({"error": "Missing required fields."}, status=400)

            data = {
                'user': request.user.id,
                'name' : name
            }
            serializer = FileSerializer(data)
            if serializer.is_valid():
                file = serializer.save()
                file_size = file_data.size
                mime_type = mimetypes.guess_type(file_data.name)
                folder = get_object_or_404(Folder, id=folder_id)
                datafv = {
                'file': file.id,
                'version': 1,
                'size': file_size,
                'type': str(mime_type) or 'application/octet-stream',
                'folder': folder.id or None,
                'is_infected': False,
                'file_data': file_data
               }
                serializerfv = FileVersionSerializer(datafv)
                if serializerfv.is_valid():
                    serializerfv.save()
                    return Response({"message":"success", 'status_code':201})
                else:
                 print(1)
                 return Response({"message":serializerfv.errors, 'status_code':400})
            else:
             print(2)
             return Response({"message":serializer.errors, 'status_code':400})
        except  Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})  

    def put(self, request, file_id, version=None):
        try:
            file = get_object_or_404(File, id=file_id, user=request.user)
            latest_version = FileVersion.objects.filter(file=file).order_by('-version').first()
            file_version = get_object_or_404(FileVersion, file=file, version=latest_version)
            new_version = FileVersion.objects.filter(file=file).count() + 1
            data = {
            'file': file.id,
            'version': new_version,
            'size': request.data.get('size', file_version.size),
            'type': request.data.get('type', file_version.type),
            'folder':request.data.get('type', file_version.folder.id),
            'is_infected': request.data.get('is_infected', file_version.is_infected),
            'file_data': request.FILES.get('file_data', file_version.file_data)
        }
            serializer = FileVersionSerializer( data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message":"success",'data': serializer.data, 'status_code':201})
            else:
             return Response({"message":serializer.errors, 'status_code':400})
        except  Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})
        
    def delete(self, request, file_id=None, name=None):
        try:
            file = get_object_or_404(File, id=file_id, user=request.user, name=name)
            print(file.id)
            data= {
                'file':file.id,
                'deleted_by': request.user.id
            }
            serializer = TrashSerializer(data=data)
            if serializer.is_valid():
              serializer.save()
              file.delete()
              return Response({"message":"data deleted successfully", "data":serializer.data})
            return Response({"error":serializer.errors})
            
        except  Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})


class FileDownloadView(FileAccessLoggingMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, file_id):
        try:
            fileversion = get_object_or_404(FileVersion, id=file_id)

            if is_file_infected(fileversion):
                return Response({"message":"This file is infected and cannot be downloaded."}, status=status.HTTP_403_FORBIDDEN)
            response = FileResponse(fileversion.file_data.open('rb'), as_attachment=True, filename=fileversion.file.name)
            return response
        except FileNotFoundError:
            return Response({"error": "File not found on disk."}, status=status.HTTP_404_NOT_FOUND)

class FileShareView(FileAccessLoggingMixin, APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, file_id):
        try:
            fileversion = get_object_or_404(FileVersion, id=file_id)
            if is_file_infected(fileversion):
                return Response({"message":"This file is infected and cannot be Shared."}, status=status.HTTP_403_FORBIDDEN)
            shared_token = secrets.token_urlsafe(16)
            data = request.data.copy()
            data['file'] = fileversion.id
            data['shared_by'] = request.user.id
            data['share_token'] = shared_token
          
            serializer = FileShareSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({'share_link': f"files/share/{shared_token}/"}, status=status.HTTP_201_CREATED)
            return Response({'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except  Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})
    def get(self, request, token):
        try:
            share = get_object_or_404(FileShare, share_token=token)
            if share.access_type == 'restricted':
                if request.user not in share.shared_with.all():
                   return Response({'message':'access_denied'}, status=status.HTTP_401_UNAUTHORIZED)
            if share.expiry_date is not None and share.expiry_date > datetime.today():
                return Response({'message':'access_denied'}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = FileVersionSerializer(share.file)
            return Response({'data':serializer.data}, status=status.HTTP_200_OK)
        except  Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})

class FileShareDownload(FileAccessLoggingMixin,APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, token):
        try:
            share = get_object_or_404(FileShare, token=token)
            if share.expiry_date is not None and share.expiry_date > datetime.today():
                return Response({'message':'access_denied'}, status=status.HTTP_401_UNAUTHORIZED)
            if share.access_type == 'restricted':
                if request.user not in share.shared_with.all():
                   return Response({'message':'access_denied'}, status=status.HTTP_401_UNAUTHORIZED)
            if share.download_limit is not None and share.downloads > share.download_limit:
                return Response({'message':'access_denied'}, status=status.HTTP_401_UNAUTHORIZED)
            share.downloads += 1
            share.save()
            response = FileResponse(share.file.file_data.open('rb'), as_attachment=True, filename=share.file.file.name)
            return response
        except  Exception as e:
          error_message = f"Error : {str(e)}"
          return Response({"error":error_message, "status":500})
        
class FolderView(APIView, FileAccessLoggingMixin):
    permission_classes = [IsAuthenticated]
    def get(self, request, folder_id=None):
        if folder_id:
            folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
            serializer = FolderDetailSerializer(folder)
            return Response(serializer.data)
        else:
            folders = Folder.objects.filter(owner=request.user)
            serializer = FolderSerializer(folders, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = FolderSerializer(request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, folder_id):
        folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
        serializer = FolderSerializer(folder, request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, folder_id):
        folder = get_object_or_404(Folder, id=folder_id, owner=request.user)

        # Optional: prevent delete if folder has children or files
        if folder.children.exists():
            return Response(
                {"error": "Folder has subfolders. Delete them first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if folder.files.exists():
            return Response(
                {"error": "Folder has files. Delete them first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        folder.delete()
        return Response({"message": "Folder deleted"}, status=status.HTTP_204_NO_CONTENT)


class FileSearchView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        if not query:
            return Response({"error": "No search query provided."}, status=status.HTTP_400_BAD_REQUEST)

        search_results = FileVersionDocument.search().query(
            "multi_match", query=query, fields=["file__name", "file__description"]
        )

        ids = [hit.meta.id for hit in search_results]
        files = FileVersion.objects.filter(id__in=ids)

        response_data = []
        for file in files:
            file_data = FileVersionSerializer(file).data
            file_document = FileVersionDocument.from_django(file)
            file_data['extracted_text'] = file_document.get_file_text()
            response_data.append(file_data)

        return Response(response_data)
