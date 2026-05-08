"""
CU — Backup / Restore y Gestiones Anuales

Endpoints:
  POST /api/admin/backup/exportar-tenant/    — Director/Admin: descarga JSON del tenant
  POST /api/admin/backup/completo/           — Superadmin: dumpdata completo (JSON)
  POST /api/admin/backup/restore/            — Superadmin: loaddata desde archivo JSON
  GET/POST   /api/admin/backup/gestiones/    — Superadmin/Director: CRUD de gestiones anuales
  POST /api/admin/backup/gestiones/<pk>/congelar/   — congela la gestión
  POST /api/admin/backup/gestiones/<pk>/descongelar/ — descongela la gestión
"""

import json
import os
import tempfile
from io import StringIO

from django.core import serializers as dj_serializers
from django.core.management import call_command
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from .models import GestionAnual
from .serializers import GestionAnualSerializer

_ROLES_GESTION = frozenset({'Director', 'Administrativo'})


def _tiene_rol_gestion(user):
    if user.is_staff:
        return True
    return bool(set(user.groups.values_list('name', flat=True)) & _ROLES_GESTION)


# ── Exportar datos del tenant (Director/Administrativo) ──────────────────────

class ExportarTenantView(APIView):
    """
    POST /api/admin/backup/exportar-tenant/
    Genera un archivo JSON con los datos clínicos del tenant del usuario autenticado.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        tenant = request.tenant
        if not tenant:
            return Response({"detail": "Sin establecimiento."}, status=404)
        if not _tiene_rol_gestion(request.user):
            return Response({"detail": "Sin permisos."}, status=403)

        export = {
            "meta": {
                "tenant_id":    tenant.id,
                "tenant_nombre": tenant.nombre,
                "tenant_slug":  tenant.slug,
                "fecha_export": timezone.now().isoformat(),
                "version":      "1.0",
            },
            "datos": {},
        }

        # ── Pacientes ─────────────────────────────────────────────────────
        try:
            from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
            pac_qs = Paciente.objects.filter(tenant=tenant).select_related()
            export["datos"]["pacientes"] = json.loads(dj_serializers.serialize("json", pac_qs))
        except Exception as e:
            export["datos"]["pacientes"] = {"error": str(e)}

        # ── Personal de Salud ─────────────────────────────────────────────
        try:
            from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud
            ps_qs = PersonalSalud.objects.filter(tenant=tenant).select_related()
            export["datos"]["personal_salud"] = json.loads(dj_serializers.serialize("json", ps_qs))
        except Exception as e:
            export["datos"]["personal_salud"] = {"error": str(e)}

        # ── Fichas ────────────────────────────────────────────────────────
        try:
            from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha
            fichas_qs = Ficha.objects.filter(paciente__tenant=tenant)
            export["datos"]["fichas"] = json.loads(dj_serializers.serialize("json", fichas_qs))
        except Exception as e:
            export["datos"]["fichas"] = {"error": str(e)}

        # ── Triajes ───────────────────────────────────────────────────────
        try:
            from AtencionClinica.RegistroDeTriaje.models import Triaje
            triajes_qs = Triaje.objects.filter(tenant=tenant)
            export["datos"]["triajes"] = json.loads(dj_serializers.serialize("json", triajes_qs))
        except Exception as e:
            export["datos"]["triajes"] = {"error": str(e)}

        # ── Consultas ─────────────────────────────────────────────────────
        try:
            from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
            consultas_qs = Consulta.objects.filter(tenant=tenant)
            export["datos"]["consultas"] = json.loads(dj_serializers.serialize("json", consultas_qs))
        except Exception as e:
            export["datos"]["consultas"] = {"error": str(e)}

        body = json.dumps(export, ensure_ascii=False, indent=2)
        response = HttpResponse(body, content_type="application/json; charset=utf-8")
        filename = f"export_{tenant.slug}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# ── Backup completo (superadmin) ──────────────────────────────────────────────

class BackupCompletoView(APIView):
    """
    POST /api/admin/backup/completo/
    Ejecuta Django dumpdata y devuelve el archivo JSON. Solo superadmin.
    """
    permission_classes = (IsAdminUser,)

    _EXCLUDE = [
        'auth.permission', 'contenttypes',
        'rest_framework_simplejwt.blacklistedtoken',
        'rest_framework_simplejwt.outstandingtoken',
        'admin.logentry', 'sessions.session',
    ]

    def post(self, request):
        out = StringIO()
        try:
            call_command(
                'dumpdata',
                '--natural-foreign', '--natural-primary',
                '--indent', '2',
                *[f'--exclude={e}' for e in self._EXCLUDE],
                stdout=out,
            )
        except Exception as exc:
            return Response({"detail": f"Error al generar backup: {exc}"}, status=500)

        data = out.getvalue()
        response = HttpResponse(data, content_type="application/json; charset=utf-8")
        filename = f"backup_completo_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# ── Restore (superadmin) ──────────────────────────────────────────────────────

class RestoreView(APIView):
    """
    POST /api/admin/backup/restore/
    Recibe un archivo JSON y ejecuta Django loaddata. Solo superadmin.
    """
    permission_classes = (IsAdminUser,)
    parser_classes     = (MultiPartParser,)

    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"detail": "Se requiere el campo 'archivo' (JSON)."}, status=400)

        suffix = '.json'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            call_command('loaddata', tmp_path)
            return Response({"mensaje": "Restauración completada exitosamente."})
        except Exception as exc:
            return Response({"detail": f"Error al restaurar: {exc}"}, status=400)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


# ── Gestiones anuales ─────────────────────────────────────────────────────────

class GestionAnualViewSet(ViewSet):
    """
    GET  /api/admin/backup/gestiones/          — lista gestiones del tenant
    POST /api/admin/backup/gestiones/          — crea gestión
    POST /api/admin/backup/gestiones/<pk>/congelar/    — congela
    POST /api/admin/backup/gestiones/<pk>/descongelar/ — descongela
    """
    permission_classes = (IsAuthenticated,)

    def _check(self, user, tenant):
        if not tenant:
            return Response({"detail": "Sin establecimiento."}, status=404)
        if not _tiene_rol_gestion(user):
            return Response({"detail": "Sin permisos."}, status=403)
        return None

    def list(self, request):
        tenant = request.tenant if not request.user.is_staff else None
        qs = GestionAnual.objects.all() if request.user.is_staff else GestionAnual.objects.filter(tenant=tenant)
        if not request.user.is_staff and not tenant:
            return Response({"detail": "Sin establecimiento."}, status=404)
        serializer = GestionAnualSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request):
        tenant = request.tenant
        err = self._check(request.user, tenant)
        if err:
            return err
        ser = GestionAnualSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(tenant=tenant)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def congelar(self, request, pk=None):
        tenant = request.tenant
        err = self._check(request.user, tenant)
        if err:
            return err
        try:
            gestion = GestionAnual.objects.get(pk=pk, tenant=tenant)
        except GestionAnual.DoesNotExist:
            return Response({"detail": "Gestión no encontrada."}, status=404)
        gestion.congelar()
        return Response(GestionAnualSerializer(gestion).data)

    @action(detail=True, methods=['post'])
    def descongelar(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"detail": "Solo superadmin puede descongelar."}, status=403)
        try:
            gestion = GestionAnual.objects.get(pk=pk)
        except GestionAnual.DoesNotExist:
            return Response({"detail": "Gestión no encontrada."}, status=404)
        gestion.descongelar()
        return Response(GestionAnualSerializer(gestion).data)
