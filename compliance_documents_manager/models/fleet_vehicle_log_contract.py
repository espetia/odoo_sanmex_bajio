# -*- coding: utf-8 -*-
import logging
import zipfile
import io
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FleetVehicleLogContract(models.Model):
    _inherit = "fleet.vehicle.log.contract"

    @api.depends(
        "vehicle_id.license_plate",
        "vehicle_id.model_id.name",
        "vehicle_id.n_economic",
        "vehicle_id.vin_sn",
        "vehicle_id.model_year",
        "vehicle_id.model_id.brand_id.name"
    )
    def _compute_vehicle_details(self):
        for record in self:
            if record.vehicle_id:
                record.license_plate = record.vehicle_id.license_plate
                record.brand = record.vehicle_id.model_id.brand_id.name
                record.model = record.vehicle_id.model_id.name
                record.year = record.vehicle_id.model_year
                record.n_series = record.vehicle_id.vin_sn
                record.n_economic = record.vehicle_id.n_economic
            else:
                record.license_plate = False
                record.brand = False
                record.model = False
                record.year = False
                record.n_series = False
                record.n_economic = False

    license_plate = fields.Char(string="Placa", compute="_compute_vehicle_details", store=True)
    brand = fields.Char(string="Marca", compute="_compute_vehicle_details", store=True)
    model = fields.Char(string="Modelo", compute="_compute_vehicle_details", store=True)
    year = fields.Char(string="Año", compute="_compute_vehicle_details", store=True)
    n_series = fields.Char(string="Número de serie", compute="_compute_vehicle_details", store=True)
    n_economic = fields.Char(string="Número económico", compute="_compute_vehicle_details", store=True)

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
