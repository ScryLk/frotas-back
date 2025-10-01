from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    errors = serializers.DictField(child=serializers.ListField(child=serializers.CharField()), required=False, allow_null=True)


class EmptySuccessResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = serializers.SerializerMethodField()

    def get_data(self, obj):  # always null
        return None
