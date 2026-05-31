# CU15 - Verificación de Integridad de Documentos
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.FirmaDigitalDeConsulta.views import calcular_hash_consulta
from IA_Blockchain.GestionDeIdentidadBlockchain.models import EventoBlockchain, IdentidadBlockchain


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verificar_documento(request, documento_id):
    """
    T007 — Verifica la integridad de una consulta médica contra blockchain.
    Recalcula el SHA-256 del documento actual y lo compara con el hash
    anclado en el bloque de firma. Devuelve VÁLIDO o ALTERADO.
    """
    try:
        consulta = Consulta.objects.get(id=documento_id, tenant=request.tenant)
    except Consulta.DoesNotExist:
        return Response({'error': 'Documento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if not consulta.hash_documento:
        return Response({
            'estado': 'SIN_FIRMA',
            'mensaje': 'Este documento aún no ha sido firmado digitalmente.',
            'consulta_id': consulta.id,
            'integro': None,
        }, status=status.HTTP_200_OK)

    hash_actual = calcular_hash_consulta(consulta)
    hash_guardado = consulta.hash_documento
    integro = hash_actual == hash_guardado

    # Obtener el evento blockchain de firma para mostrar detalles al auditor
    evento = EventoBlockchain.objects.filter(
        tenant=request.tenant,
        tipo_evento='FIRMA_CONSULTA',
        documento_tipo='Consulta',
        documento_id=documento_id,
    ).order_by('numero_bloque').first()

    firmado_por_nombre = None
    did_firmante = None
    timestamp_firma = None
    bloque_numero = None
    bloque_hash = None

    if evento:
        firmado_por_nombre = evento.firmado_por.get_full_name() or evento.firmado_por.username
        timestamp_firma = evento.timestamp_bloque or evento.timestamp.isoformat()
        bloque_numero = evento.numero_bloque
        bloque_hash = evento.bloque_hash
        try:
            identidad = IdentidadBlockchain.objects.get(
                usuario=evento.firmado_por, tenant=request.tenant
            )
            did_firmante = identidad.did_simulado
        except IdentidadBlockchain.DoesNotExist:
            pass

    return Response({
        'estado': 'VÁLIDO' if integro else 'ALTERADO',
        'integro': integro,
        'consulta_id': consulta.id,
        'hash_guardado': hash_guardado,
        'hash_actual': hash_actual,
        'firmado_por': firmado_por_nombre,
        'firmado_en': timestamp_firma,
        'did_firmante': did_firmante,
        'bloque_numero': bloque_numero,
        'bloque_hash': bloque_hash,
    }, status=status.HTTP_200_OK)
