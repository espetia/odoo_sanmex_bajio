from odoo import models, fields, api


class MailMessage(models.Model):
    _inherit = 'mail.message'

    def get_author_user(self, author_partner_id):
        if not author_partner_id:
            return
        partner = self.env['res.partner'].browse(author_partner_id)
        if partner and partner.user_ids:
            for user in partner.user_ids:
                return user

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            author_partner_id = values.get('author_id', False)
            model = values.get('model', False)
            user = self.get_author_user(author_partner_id)
            company = user and user.company_id
            internal_user = user and user.has_group('base.group_user')
            email_from, reply_to = self.env['mail.replace.rule'].get_email_from_reply_to(model, company, internal_user)
            if email_from:
                # Overwrite email_from if replacement exists
                values.update({'email_from': email_from})
            if reply_to is not None:
                # Overwrite reply_to if replacement exists
                values.update({'reply_to': reply_to})
        return super(MailMessage, self).create(values_list)
