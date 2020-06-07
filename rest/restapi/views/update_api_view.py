from rest_framework import mixins
from rest_framework.generics import GenericAPIView

class UpdateAPIView(mixins.UpdateModelMixin,
                    GenericAPIView):
    """
    Custom api view for swagger, generating only pyt method
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)