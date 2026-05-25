# CU14 - Gestión de Identidad Blockchain
# Vistas pendientes de implementación.
# views.py — Endpoints CU: Gestión de Identidad Blockchain
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from GestionDeUsuarios.LoginYAutenticacion.permissions import EsAdminODirector
from .models import IdentidadBlockchain, EventoBlockchain
from .service import (
    registrar_identidad_blockchain,
    verificar_integridad_cadena,
    verificar_rol_usuario,
)


@api_view(['POST'])
@permission_classes([IsAuthenticated, EsAdminODirector])
def registrar_identidad(request):
    """
    POST /api/blockchain/identidad/registrar/
    Genera claves RSA y DID para un usuario y lo registra en la blockchain.
    Solo Admin puede hacerlo.
    """
    usuario_id = request.data.get('usuario_id')
    if not usuario_id:
        return Response(
            {'error': 'El campo usuario_id es obligatorio.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        usuario = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar si ya tiene identidad
    if IdentidadBlockchain.objects.filter(usuario=usuario).exists():
        return Response(
            {'error': 'Este usuario ya tiene una identidad blockchain registrada.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    identidad = registrar_identidad_blockchain(usuario, request.tenant)

    return Response({
        'mensaje': 'Identidad blockchain registrada exitosamente.',
        'did': identidad.did_simulado,
        'clave_publica': identidad.clave_publica_pem,
        'usuario': usuario.username,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_identidad(request):
    """
    GET /api/blockchain/identidad/
    Devuelve la identidad blockchain del usuario autenticado.
    """
    try:
        identidad = IdentidadBlockchain.objects.get(
            usuario=request.user,
            tenant=request.tenant
        )
    except IdentidadBlockchain.DoesNotExist:
        return Response(
            {'error': 'No tienes una identidad blockchain registrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'did': identidad.did_simulado,
        'clave_publica': identidad.clave_publica_pem,
        'creado_en': identidad.creado_en,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, EsAdminODirector])
def verificar_cadena(request):
    """
    GET /api/blockchain/verificar-cadena/
    Verifica que toda la cadena de bloques esté íntegra.
    Solo Admin puede hacerlo.
    """
    resultado = verificar_integridad_cadena(request.tenant)
    return Response(resultado)


@api_view(['GET'])
@permission_classes([IsAuthenticated, EsAdminODirector])
def verificar_rol(request, usuario_id):
    """
    GET /api/blockchain/verificar-rol/{usuario_id}/
    Contrasta el rol local del usuario con el registro en blockchain.
    Si hay alteración, suspende la cuenta automáticamente.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        usuario = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    resultado = verificar_rol_usuario(usuario, request.tenant)

    if not resultado['valido']:
        return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    return Response(resultado)


@api_view(['GET'])
@permission_classes([IsAuthenticated, EsAdminODirector])
def listar_eventos(request):
    """
    GET /api/blockchain/eventos/
    Lista todos los eventos de la blockchain del tenant.
    """
    eventos = EventoBlockchain.objects.filter(
        tenant=request.tenant
    ).order_by('numero_bloque')

    data = [{
        'numero_bloque': e.numero_bloque,
        'tipo_evento': e.tipo_evento,
        'documento_tipo': e.documento_tipo,
        'documento_id': e.documento_id,
        'firmado_por': e.firmado_por.username,
        'timestamp': e.timestamp,
        'bloque_hash': e.bloque_hash,
    } for e in eventos]

    return Response(data)