from .agregar_comentario_interno_ticket import agregar_comentario_interno_ticket
from .asignar_tecnico_ticket import asignar_tecnico_ticket
from .buscar_cliente import buscar_cliente
from .consultar_mis_tickets import consultar_mis_tickets
from .consultar_tickets_cliente import consultar_tickets_cliente
from .crear_ticket_soporte import crear_ticket_soporte
from .listar_sucursales_cliente import listar_sucursales_cliente
from .obtener_detalle_ticket import obtener_detalle_ticket

ALL_TOOLS = [
    consultar_mis_tickets,
    consultar_tickets_cliente,
    buscar_cliente,
    listar_sucursales_cliente,
    crear_ticket_soporte,
    obtener_detalle_ticket,
    agregar_comentario_interno_ticket,
    asignar_tecnico_ticket,
]
