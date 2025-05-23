import base64
import uuid

from rest_framework import serializers
from django.core.files.base import ContentFile


class Base64EncodedImageField(serializers.ImageField):
    def __init__(self, *args, file_prefix='file', max_filename_length=None, **kwargs):
        self.file_prefix = file_prefix
        self.max_filename_length = max_filename_length
        super().__init__(*args, **kwargs)

    def to_internal_value(self, value):
        if isinstance(value, str) and value.startswith("data:image"):
            header, encoded_data = value.split(";base64,")
            extension = header.split("/")[-1]
            unique_filename = f"{self.file_prefix}_{uuid.uuid4()}.{extension}"
            decoded_file = base64.b64decode(encoded_data)
            value = ContentFile(decoded_file, name=unique_filename)
        return super().to_internal_value(value)