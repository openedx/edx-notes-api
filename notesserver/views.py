from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes


@api_view(['GET'])
@permission_classes([AllowAny])
def root(request):  # pylint: disable=unused-argument
    """
    Root view.
    """
    return Response({
        "name": "edX Notes API",
        "version": "1"
    })


class StatusView(APIView):
    """
    Determine if server is alive.
    """
    permission_classes = (AllowAny,)

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Service status.
        """
        return Response()
