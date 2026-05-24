import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Block :
    numero: int
    anterior_hash: str
    tipo_evento: str
    documento_tipo: str
    documento_id: int
    hash_documento: str
    firma_rsa: str
    firmado_por_id: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def calcular_hash(self) -> str:
        texto=json.dumps(self.__dict__, sort_keys=True)
        bytes_texto=texto.encode('utf-8')
        return hashlib.sha256(bytes_texto).hexdigest()
        
