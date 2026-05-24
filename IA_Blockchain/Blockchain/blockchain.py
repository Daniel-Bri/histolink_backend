from .block import Block
from dataclasses import dataclass, field

@dataclass
class Blockchain:
    GENESIS_HASH: str = "0" * 64
    cadena: list = field(default_factory=list)

    def agregar_bloque(self, datos: dict) -> Block:
        if len(self.cadena)==0:
            anterior_hash = self.GENESIS_HASH
        else:
            anterior_hash = self.cadena[-1].calcular_hash()
        numero = len(self.cadena)
        nuevo_bloque = Block(numero=numero, anterior_hash=anterior_hash, **datos)
        self.cadena.append(nuevo_bloque)
        return nuevo_bloque       
    
    def verificar_cadena(self):
        for i in range (1, len(self.cadena)):
            actual = self.cadena[i]
            anterior = self.cadena[i-1]
            if actual.anterior_hash != anterior.calcular_hash():
                return False
            if actual.numero != anterior.numero + 1:
                return False
        return True        
    
 
    def verificar_bloque_individual(self, bloque: Block, bloque_hash_guardado:str) -> bool:
        if(bloque.calcular_hash() != bloque_hash_guardado):
            return False
        return True
