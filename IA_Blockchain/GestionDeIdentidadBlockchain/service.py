# service.py — Puente entre Blockchain simulada y PostgreSQL
import hashlib
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from .models import IdentidadBlockchain, EventoBlockchain
from IA_Blockchain.Blockchain.blockchain import Blockchain
from IA_Blockchain.Blockchain.block import Block


def generar_par_claves_rsa():
    """Genera un par de claves RSA (privada y pública) en formato PEM."""
    clave_privada = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    privada_pem = clave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    publica_pem = clave_privada.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return privada_pem, publica_pem


def generar_did_simulado(usuario_id: int, username: str) -> str:
    """Genera un DID simulado único para el usuario."""
    base = f"did:histolink:{usuario_id}:{username}"
    return base


def registrar_identidad_blockchain(usuario, tenant) -> IdentidadBlockchain:
    """
    Genera claves RSA y DID simulado para un usuario nuevo
    y lo registra en la blockchain.
    """
    privada_pem, publica_pem = generar_par_claves_rsa()
    did = generar_did_simulado(usuario.id, usuario.username)

    identidad = IdentidadBlockchain.objects.create(
        tenant=tenant,
        usuario=usuario,
        clave_publica_pem=publica_pem,
        clave_privada_pem=privada_pem,
        did_simulado=did,
    )

    # Registrar evento en la blockchain
    rol = usuario.groups.first().name if usuario.groups.exists() else 'Sin Rol'
    hash_doc = hashlib.sha256(f"{did}{rol}{usuario.id}".encode()).hexdigest()

    agregar_evento_blockchain(
        tenant=tenant,
        tipo_evento='REGISTRO_IDENTIDAD',
        documento_tipo='IdentidadBlockchain',
        documento_id=identidad.id,
        hash_documento=hash_doc,
        firmado_por=usuario,
        clave_privada_pem=privada_pem,
    )

    return identidad


def firmar_con_rsa(contenido: str, clave_privada_pem: str) -> str:
    """Firma un contenido con la clave privada RSA del usuario."""
    clave_privada = serialization.load_pem_private_key(
        clave_privada_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    firma = clave_privada.sign(
        contenido.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return firma.hex()


def agregar_evento_blockchain(
    tenant,
    tipo_evento: str,
    documento_tipo: str,
    documento_id: int,
    hash_documento: str,
    firmado_por,
    clave_privada_pem: str | None,
) -> EventoBlockchain:
    """
    Agrega un nuevo bloque a la blockchain simulada en PostgreSQL.
    Reconstruye la cadena desde la BD, agrega el bloque y lo persiste.
    """
    # Reconstruir cadena desde BD
    blockchain = Blockchain()
    eventos_previos = EventoBlockchain.objects.filter(tenant=tenant).order_by('numero_bloque')

    for ev in eventos_previos:
        bloque = Block(
            numero=ev.numero_bloque,
            anterior_hash=ev.anterior_hash,
            tipo_evento=ev.tipo_evento,
            documento_tipo=ev.documento_tipo,
            documento_id=ev.documento_id,
            hash_documento=ev.hash_documento,
            firma_rsa=ev.firma_rsa,
            firmado_por_id=ev.firmado_por_id,
            timestamp=ev.timestamp.isoformat(),
        )
        blockchain.cadena.append(bloque)

    # Firmar el contenido
    contenido = json.dumps(
        {
            'tipo_evento': tipo_evento,
            'documento_tipo': documento_tipo,
            'documento_id': documento_id,
            'hash_documento': hash_documento,
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    if clave_privada_pem:
        firma_rsa = firmar_con_rsa(contenido, clave_privada_pem)
    else:
        firma_rsa = hashlib.sha256(contenido.encode('utf-8')).hexdigest()

    # Agregar nuevo bloque
    nuevo_bloque = blockchain.agregar_bloque({
        'tipo_evento': tipo_evento,
        'documento_tipo': documento_tipo,
        'documento_id': documento_id,
        'hash_documento': hash_documento,
        'firma_rsa': firma_rsa,
        'firmado_por_id': firmado_por.id,
    })

    # Persistir en BD
    evento = EventoBlockchain.objects.create(
        tenant=tenant,
        numero_bloque=nuevo_bloque.numero,
        anterior_hash=nuevo_bloque.anterior_hash,
        tipo_evento=nuevo_bloque.tipo_evento,
        documento_tipo=nuevo_bloque.documento_tipo,
        documento_id=nuevo_bloque.documento_id,
        hash_documento=nuevo_bloque.hash_documento,
        firma_rsa=nuevo_bloque.firma_rsa,
        firmado_por=firmado_por,
        bloque_hash=nuevo_bloque.calcular_hash(),
        timestamp_bloque=nuevo_bloque.timestamp,
    )

    return evento


def verificar_integridad_cadena(tenant) -> dict:
    """
    Verifica que toda la cadena de bloques esté íntegra.
    Reconstruye desde BD y llama a verificar_cadena().
    """
    blockchain = Blockchain()
    eventos = EventoBlockchain.objects.filter(tenant=tenant).order_by('numero_bloque')

    for ev in eventos:
        bloque = Block(
            numero=ev.numero_bloque,
            anterior_hash=ev.anterior_hash,
            tipo_evento=ev.tipo_evento,
            documento_tipo=ev.documento_tipo,
            documento_id=ev.documento_id,
            hash_documento=ev.hash_documento,
            firma_rsa=ev.firma_rsa,
            firmado_por_id=ev.firmado_por_id,
            timestamp=ev.timestamp.isoformat(),
        )
        blockchain.cadena.append(bloque)

    es_valida = blockchain.verificar_cadena()
    return {
        'valida': es_valida,
        'total_bloques': len(blockchain.cadena),
    }


def verificar_rol_usuario(usuario, tenant) -> dict:
    """
    Contrasta el rol local del usuario con el registro en blockchain.
    Si hay alteración, suspende la cuenta.
    """
    try:
        identidad = IdentidadBlockchain.objects.get(usuario=usuario, tenant=tenant)
    except IdentidadBlockchain.DoesNotExist:
        return {'valido': False, 'error': 'El usuario no tiene identidad blockchain registrada.'}

    # Obtener el evento original de registro
    evento_registro = EventoBlockchain.objects.filter(
        tenant=tenant,
        tipo_evento='REGISTRO_IDENTIDAD',
        documento_tipo='IdentidadBlockchain',
        documento_id=identidad.id,
    ).first()

    if not evento_registro:
        return {'valido': False, 'error': 'No se encontró el evento de registro en blockchain.'}

    # Verificar bloque individual
    blockchain = Blockchain()
    bloque = Block(
        numero=evento_registro.numero_bloque,
        anterior_hash=evento_registro.anterior_hash,
        tipo_evento=evento_registro.tipo_evento,
        documento_tipo=evento_registro.documento_tipo,
        documento_id=evento_registro.documento_id,
        hash_documento=evento_registro.hash_documento,
        firma_rsa=evento_registro.firma_rsa,
        firmado_por_id=evento_registro.firmado_por_id,
        timestamp=evento_registro.timestamp_bloque,
    )

    es_valido = blockchain.verificar_bloque_individual(bloque, evento_registro.bloque_hash)

    if not es_valido:
        # Suspender cuenta
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        return {'valido': False, 'error': 'Alteración detectada. Cuenta suspendida automáticamente.'}

    return {'valido': True, 'did': identidad.did_simulado}
