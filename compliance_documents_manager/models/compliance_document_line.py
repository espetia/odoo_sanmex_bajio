# -*- coding: utf-8 -*-
import logging
import zipfile
import io
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ComplianceDocumentLine(models.Model):
    _name = "compliance.document.line"
    _description = "Documento administrativo"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.depends("date_expiration")
    def _compute_expiration_date_soon(self):
        for record in self:
            f_today = fields.Date.today()
            if record.date_expiration:
                dates_diff = (record.date_expiration - f_today).days
                record.expiration_date_soon = 0 <= dates_diff <= 7
            else:
                record.expiration_date_soon = False

    name = fields.Char("Nombre", compute="_compute_name", store=True)
    partner_id = fields.Many2one("res.partner", string="Proveedor", required=True)
    type_resource = fields.Selection(
        [
            ("empleado", "Empleado"),
            ("propiedad", "Propiedad"),
            ("otro", "Otro"),
        ],
        string="Tipo de recurso",
        required=True,
    )
    employee_id = fields.Many2one("hr.employee", string="Empleado")
    company_id = fields.Many2one("res.company", string="Compañía", default=lambda self: self.env.company)
    date_application = fields.Date(string="Fecha de solicitud")
    date_expiration = fields.Date(string="Fecha de expiración")
    folio_document = fields.Char(string="Folio del documento")
    expiration_date_soon = fields.Boolean(
        string="Próximo a vencer", compute="_compute_expiration_date_soon", store=True
    )
    note = fields.Text(string="Nota")
    # fields for the fleet vehicle
    # license_plate = fields.Char(string="Placa")
    # brand = fields.Char(string="Marca")
    # model = fields.Char(string="Modelo")
    # year = fields.Char(string="Año")
    # n_series = fields.Char(string="Número de serie")
    # n_economic = fields.Char(string="Número económico")
    # fields for the employee
    employee_name = fields.Char(string="Nombre del empleado", compute="_compute_employee_name_details", store=True)
    nss_employee = fields.Char(string="Número IMSS", compute="_compute_employee_name_details", store=True)
    curp_employee = fields.Char(string="CURP", compute="_compute_employee_name_details", store=True)
    rfc_employee = fields.Char(string="RFC", compute="_compute_employee_name_details", store=True)
    department_id = fields.Many2one(
        "hr.department",
        string="Departamento",
        compute="_compute_employee_name_details", store=True,
        help="Departamento al que pertenece el empleado",
    )
    # fields for the property
    property_name = fields.Char(string="Nombre de la propiedad")
    property_address = fields.Char(string="Dirección de la propiedad")
    property_name_doc = fields.Char(string="Nombre del documento de propiedad")
    is_visible = fields.Boolean(
        "Visible", default=True, help="Si está desactivado, solo los managers podrán ver este registro"
    )
    type_compliance_document_id = fields.Many2one(
        "type.compliance.document",
        string="Tipo de documento",
        required=True,
        help="Tipo de documento",
    )
    notes = fields.Text(string="Notas Adicionales", help="Campo para agregar notas o comentarios adicionales")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    amount_cost = fields.Monetary('Costo', currency_field="currency_id")

    @api.depends("employee_id.name", "type_compliance_document_id.name", "type_resource", "property_name_doc")
    def _compute_name(self):
        for record in self:
            if record.employee_id.name and record.type_resource == "empleado":
                # Formato: "Juan Pérez - Contrato"
                record.name = f"{record.employee_id.name} - {record.type_compliance_document_id.name}"
            elif record.type_resource == "propiedad" and record.property_name_doc:
                record.name = f"{record.property_name_doc} - {record.type_compliance_document_id.name}"
            else:
                record.name = "Documento sin definir"
            # if record.type_resource == "propiedad" and record.property_name_doc:
            # Formato: "Propiedad - Permiso"
            #    record.name = f"{record.property_name_doc} - {dict(record._fields['type_document'].selection)[record.type_document]}"
            # else:
            #    record.name = "Documento sin definir"

    @api.depends("employee_id")
    def _compute_employee_name_details(self):
        for record in self:
            record.employee_name = record.employee_id.name if record.employee_id else "No asignado"
            record.nss_employee = record.employee_id.nss_employee if record.employee_id else ""
            record.curp_employee = record.employee_id.curp_employee if record.employee_id else ""
            record.rfc_employee = record.employee_id.rfc_employee if record.employee_id else ""
            record.department_id = record.employee_id.department_id if record.employee_id else False

    def action_download_attachments(self):
        """Descargar attachments de los registros seleccionados"""
        if len(self) == 1:
            # Un solo registro
            return self._download_single_record()
        else:
            # Múltiples registros
            return self._download_multiple_records()

    def _download_single_record(self):
        """Descargar attachments de un solo registro"""
        attachments = (
            self.env["ir.attachment"].sudo().search([("res_model", "=", self._name), ("res_id", "=", self.id)])
        )

        if not attachments:
            raise UserError("No hay archivos adjuntos para descargar")

        if len(attachments) == 1:
            # Un solo archivo
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/{attachments.id}?download=true",
                "target": "self",
            }
        else:
            # Múltiples archivos del mismo registro
            return self._create_zip_download(attachments, f"compliance_doc_{self.id}")

    def _download_multiple_records(self):
        """Descargar attachments de múltiples registros"""
        all_attachments = self.env["ir.attachment"]

        for record in self:
            record_attachments = (
                self.env["ir.attachment"].sudo().search([("res_model", "=", self._name), ("res_id", "=", record.id)])
            )
            all_attachments |= record_attachments

        if not all_attachments:
            raise UserError("No hay archivos adjuntos en los registros seleccionados")

        return self._create_zip_download(all_attachments, "Documentos_de_control")

    def _create_zip_download(self, attachments, zip_name):
        """Crear ZIP con attachments"""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Contador para evitar nombres duplicados
            name_counter = {}

            for attachment in attachments:
                if attachment.datas:
                    file_data = base64.b64decode(attachment.datas)

                    # Manejar nombres duplicados
                    original_name = attachment.name or f"file_{attachment.id}"
                    if original_name in name_counter:
                        name_counter[original_name] += 1
                        name, ext = original_name.rsplit(".", 1) if "." in original_name else (original_name, "")
                        file_name = (
                            f"{name}_{name_counter[original_name]}.{ext}"
                            if ext
                            else f"{name}_{name_counter[original_name]}"
                        )
                    else:
                        name_counter[original_name] = 0
                        file_name = original_name

                    zip_file.writestr(file_name, file_data)

        zip_buffer.seek(0)
        zip_data = base64.b64encode(zip_buffer.getvalue()).decode()

        # Crear attachment temporal
        zip_attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": f"{zip_name}.zip",
                    "datas": zip_data,
                    "type": "binary",
                    "res_model": "ir.attachment",
                }
            )
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{zip_attachment.id}?download=true",
            "target": "self",
        }
