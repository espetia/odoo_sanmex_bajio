# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchasePaymentDocumentationLine(models.Model):
    _name = 'purchase.payment.documentation.line'
    _description = 'Purchase Payment Documentation Line'

    order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True, ondelete='cascade')
    invoice_number = fields.Char(string='Invoice Number', required=True)
    payment_method = fields.Selection([
        ('PPD', 'PPD'),
        ('PUE', 'PUE'),
        ('regular_pay', 'Regular Pay')
    ], string='Payment Method', required=True)
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id', store=True, string='Currency')
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True)
    invoice_pdf = fields.Binary(string='Invoice PDF', attachment=True, required=True)
    invoice_xml = fields.Binary(string='Invoice XML', attachment=True)
    invoice_pdf_name = fields.Char(string='PDF File Name')
    invoice_xml_name = fields.Char(string='XML File Name')
    comment = fields.Char(string='Comment', size=120)

    @api.constrains('invoice_pdf', 'invoice_xml')
    def _check_file_size_and_type(self):
        max_size = 3 * 1024 * 1024  # 3 MB
        for rec in self:
            if rec.invoice_pdf:
                # Check size
                file_size = len(base64.b64decode(rec.invoice_pdf))
                if file_size > max_size:
                    raise ValidationError("The PDF invoice file cannot exceed 3 MB.")

                # Check format (starts with '%PDF')
                header = base64.b64decode(rec.invoice_pdf[:20])
                if not header.startswith(b'%PDF'):
                    raise ValidationError("The uploaded file for Invoice PDF is not a valid PDF.")

            if rec.invoice_xml:
                # Check size
                file_size = len(base64.b64decode(rec.invoice_xml))
                if file_size > max_size:
                    raise ValidationError("The XML invoice file cannot exceed 3 MB.")

                # Check format based on file extension
                if rec.invoice_xml_name and not rec.invoice_xml_name.lower().endswith('.xml'):
                    raise ValidationError("The uploaded file for Invoice XML must be an XML file.")

    def action_view_pdf(self):
        self.ensure_one()
        if not self.invoice_pdf:
            return

        filename = self.invoice_pdf_name or 'invoice.pdf'
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/purchase.payment.documentation.line/{self.id}/invoice_pdf/{filename}',
            'target': 'new',
        }