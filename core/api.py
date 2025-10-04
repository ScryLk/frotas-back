from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


def custom_exception_handler(exc, context):
    """Envelopa respostas de erro no padrão { status, message, errors }."""
    response = drf_exception_handler(exc, context)

    if response is None:
        # Erros não tratados pelo DRF
        return Response({
            'status': 'error',
            'message': str(exc),
            'errors': None,
        }, status=500)

    data = response.data
    # Tenta extrair uma mensagem amigável
    message = ''
    if isinstance(data, dict):
        message = data.get('detail') or next(iter(data.values()), '') if data else ''
    else:
        message = str(data)

    response.data = {
        'status': 'error',
        'message': message,
        'errors': data if isinstance(data, dict) else None,
    }
    return response


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'success', 'data': {'health': 'ok'}})
