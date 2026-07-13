from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MailReplaceRule(models.Model):
    _name = 'mail.replace.rule'
    _description = 'Mail Replace Rule'
    _order = 'sequence'
    # Common Values
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    name = fields.Char(
        string='Rule Name',
        required=True,
    )
    model_id = fields.Many2one(
        string='Model',
        comodel_name='ir.model',
        ondelete='cascade',
    )
    model = fields.Char(
        string='Model Name',
        related='model_id.model',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        default=lambda self: self.env.company,
        ondelete='cascade',
        index=True,
    )
    only_for_internal_users = fields.Boolean(
        string='Only for Internal Users',
        default=True,
        help="""
        If enabled the system will replace the "Email From" and "Reply To" values only for emails initiated by internal users. 
        Please disable this checkbox only consciously, as it affects security.
        """
    )
    # Email From
    email_from_author = fields.Boolean(
        string='Email From Author',
        help='If enabled, the system will work as is and will not replace email_from parameter',
    )
    email_from = fields.Char(
        string='Email From',
    )
    email_from_user_id = fields.Many2one(
        string='Email From User',
        comodel_name='res.users',
        ondelete='cascade',
    )
    email_from_computed = fields.Char(
        string='Email From (Computed)',
        compute='_compute_email_from',
    )
    # Reply To
    reply_to_author = fields.Boolean(
        string='Reply To Author',
        help='If enabled, the system will work as is and will not replace reply_to parameter',
    )
    reply_to = fields.Char(
        string='Reply To',
        help='Forcibly replace the reply_to parameter',
    )
    reply_to_user_id = fields.Many2one(
        string='Reply To User',
        comodel_name='res.users',
        ondelete='cascade',
        help='Forcibly replace the reply_to parameter with email of the selected user',
    )
    reply_to_computed = fields.Char(
        string='Reply To (Computed)',
        compute='_compute_reply_to',
    )
    _sql_constraints = [
        ('model_company_uniq', 'unique (model_id,company_id)',
         'The replacement rule for data model must be unique per company!')
    ]

    @api.depends('email_from', 'email_from_user_id')
    def _compute_email_from(self):
        for rule in self:
            if rule.email_from:
                rule.email_from_computed = rule.email_from
            elif rule.email_from_user_id:
                rule.email_from_computed = rule.email_from_user_id.email_formatted
            elif rule.email_from_author:
                rule.email_from_computed = self.env.user.email_formatted
            else:
                rule.email_from_computed = False

    @api.depends('reply_to', 'reply_to_user_id')
    def _compute_reply_to(self):
        for rule in self:
            if rule.reply_to:
                rule.reply_to_computed = rule.reply_to
            elif rule.reply_to_user_id:
                rule.reply_to_computed = rule.reply_to_user_id.email_formatted
            elif rule.reply_to_author:
                rule.reply_to_computed = self.env.user.email_formatted
            else:
                rule.reply_to_computed = False

    @api.onchange('email_from_author')
    def onchange_email_from_author(self):
        for rule in self:
            if rule.email_from_author:
                rule.email_from = None
                rule.email_from_user_id = None

    @api.onchange('reply_to_author')
    def onchange_reply_to_author(self):
        for rule in self:
            if rule.reply_to_author:
                rule.reply_to = None
                rule.reply_to_user_id = None

    @api.constrains('email_from_author', 'email_from', 'email_from_user_id')
    def _check_email_from(self):
        for rule in self:
            if not rule.email_from_author and not rule.email_from_computed:
                raise ValidationError(_('Please set any email_from option!'))

    @api.constrains('reply_to_author', 'reply_to', 'reply_to_user_id')
    def _check_reply_to(self):
        for rule in self:
            if not rule.reply_to_author and not rule.reply_to_computed:
                raise ValidationError(_('Please set any reply_to option!'))

    def get_rule(self, model=None, company=None, internal_user=None):
        rule = None
        if model and company:
            rule = self.get_strict_rule(model, company, internal_user)
            if not rule:
                rule = self.get_model_rule(model, internal_user)
            if not rule:
                rule = self.get_company_rule(company, internal_user)
        elif model and not company:
            rule = self.get_model_rule(model, internal_user)
        elif not model and company:
            rule = self.get_company_rule(company, internal_user)
        if not rule:
            rule = self.get_global_rule(internal_user)
        return rule

    def get_strict_rule(self, model, company, internal_user):
        domain = [
            ('model', '=', model),
            ('company_id', '=', company.id),
            ('only_for_internal_users', '=', internal_user),
        ]
        return self.search(domain, limit=1)

    def get_model_rule(self, model, internal_user):
        domain = [
            ('model', '=', model),
            ('company_id', '=', False),
            ('only_for_internal_users', '=', internal_user),
        ]
        return self.search(domain, limit=1)

    def get_company_rule(self, company, internal_user):
        domain = [
            ('model_id', '=', False),
            ('company_id', '=', company.id),
            ('only_for_internal_users', '=', internal_user),
        ]
        return self.search(domain, limit=1)

    def get_global_rule(self, internal_user):
        domain = [
            ('model_id', '=', False),
            ('company_id', '=', False),
            ('only_for_internal_users', '=', internal_user),
        ]
        return self.search(domain, limit=1)

    def get_email_from_reply_to(self, model, company, internal_user):
        rule = self.get_rule(model, company, internal_user)
        if rule:
            return rule.email_from_computed, rule.reply_to_computed
        return None, None
