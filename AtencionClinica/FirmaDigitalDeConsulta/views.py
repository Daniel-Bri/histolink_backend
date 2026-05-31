# CU11 - Firma Digital de Consulta
import hashlib
import json

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from IA_Blockchain.GestionDeIdentidadBlockchain.models import IdentidadBlockchain
from IA_Blockchain.GestionDeIdentidadBlockchain.service import agregar_evento_blockchain


def calcular_hash_consulta(consulta) -> str:
    """
    SHA-256 del contenido clínico SOAP. Cualquier cambio en el texto
    produce un hash diferente, detectando manipulación.
    """
    contenido = json.dumps({
        'id': consulta.id,
        'ficha_id': consulta.ficha_id,
        'medico_id': consulta.medico_id,
        'motivo_consulta': consulta.motivo_consulta,
        'historia_enfermedad_actual': consulta.historia_enfermedad_actual,
        'examen_fisico': consulta.examen_fisico,
        'impresion_diagnostica': consulta.impresion_diagnostica,
        'codigo_cie10_principal': consulta.codigo_cie10_principal,
        'codigo_cie10_secundario': consulta.codigo_cie10_secundario,
        'descripcion_cie10': consulta.descripcion_cie10,
        'plan_tratamiento': consulta.plan_tratamiento,
        'indicaciones_alta': consulta.indicaciones_alta,
        'creado_en': consulta.creado_en.isoformat(),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(contenido.encode('utf-8')).hexdigest()


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def firmar_consulta(request, consulta_id):
    """
    T008 — Firma digital de una consulta médica.
    Calcula SHA-256 del contenido SOAP, firma con RSA y ancla en blockchain.
    Solo médicos con identidad blockchain registrada pueden firmar.
    """
    grupos = list(request.user.groups.values_list('name', flat=True))
    if 'Médico' not in grupos and not request.user.is_superuser:
        return Response(
            {'error': 'Solo un médico puede firmar consultas.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        consulta = Consulta.objects.get(id=consulta_id, tenant=request.tenant)
    except Consulta.DoesNotExist:
        return Response({'error': 'Consulta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    if consulta.estado == 'FIRMADA':
        return Response(
            {'error': 'La consulta ya fue firmada digitalmente.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        identidad = IdentidadBlockchain.objects.get(
            usuario=request.user, tenant=request.tenant
        )
    except IdentidadBlockchain.DoesNotExist:
        return Response(
            {
                'error': (
                    'No tienes una identidad blockchain registrada. '
                    'Contacta al administrador para registrar tu clave RSA.'
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    hash_doc = calcular_hash_consulta(consulta)

    evento = agregar_evento_blockchain(
        tenant=request.tenant,
        tipo_evento='FIRMA_CONSULTA',
        documento_tipo='Consulta',
        documento_id=consulta.id,
        hash_documento=hash_doc,
        firmado_por=request.user,
        clave_privada_pem=identidad.clave_privada_pem,
    )

    consulta.hash_documento = hash_doc
    consulta.firmada_por = request.user
    consulta.firmada_en = timezone.now()
    consulta.estado = 'FIRMADA'
    consulta.save(update_fields=['hash_documento', 'firmada_por', 'firmada_en', 'estado'])

    return Response({
        'mensaje': 'Consulta firmada y anclada en blockchain correctamente.',
        'consulta_id': consulta.id,
        'estado': 'FIRMADA',
        'hash_documento': hash_doc,
        'firmada_por': request.user.get_full_name() or request.user.username,
        'firmada_en': consulta.firmada_en.isoformat(),
        'did_firmante': identidad.did_simulado,
        'bloque_numero': evento.numero_bloque,
        'bloque_hash': evento.bloque_hash,
    }, status=status.HTTP_200_OK)
