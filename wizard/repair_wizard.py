from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RepairCarWizard(models.TransientModel):
    _name = 'car.repair.wizard'
    _description = 'Repair Car Wizard'

    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    finish_date = fields.Date(
        'Contract End Date',
        help='Date when the coverage of the contract ends', required=True)
    start_date = fields.Date(
        'Contract Start Date',
        help='Date when the coverage of the contract begins', required=True)
    notes = fields.Html('Terms and Conditions', copy=False)
    nb_day = fields.Integer(string='The number Of Rental Days ', compute='_number_of_the_days', readonly=True)
    active = fields.Boolean(default=True)
    repairman_id = fields.Many2one('res.partner', string='Repairman')
    phone = fields.Char(string="The Worker Phone", related='repairman_id.mobile', compute_sudo="True")
    email = fields.Char(string="The Worker Email", related='repairman_id.email', compute_sudo="True")
    reason = fields.Selection([
        ('damaged', 'Damaged'),
        ('situation', 'Situation')
    ], string='The Reason', default='situation', required=True)
    damage_ids = fields.Many2many('car.damage', 'car_repair_wizard_damage', string='Damage')
    services_ids = fields.Many2many('car.services', 'car_services_repair_wizard', string='Services Needed')
    costs = fields.Monetary(string='Cost', compute='_damage_cost', readonly=True)
    car_situation = fields.Selection([
        ('damaged', 'Damaged'),
        ('available', 'Available')
    ], string='The Reason')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    @api.model
    def default_get(self, fields):
        res = super(RepairCarWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            car = self.env['company.car'].browse(active_id)
            if car.state == 'damaged':
                res.update({
                    'damage_ids': car.damage_ids,
                    'services_ids': car.services_ids,
                    'reason': 'damaged',
                    'car_situation': car.state
                })
        return res

    def action_create_maintenance(self):
        active_id = self.env.context.get('active_id')
        car = self.env['company.car'].browse(active_id)

        if not car:
            raise ValidationError(_("Car record not found."))

        rent_contract = self.env['car.maintenance'].create({
            'car_id': car.id,
            'start_date': self.start_date,
            'finish_date': self.finish_date,
            'state': 'draft',
            'repairman_id': self.repairman_id.id,
            'reason': 'damaged',
            'damage_ids': car.damage_ids,
            'services_ids': car.services_ids,
            'costs': car.costs
        })

        if not rent_contract:
            raise ValidationError(_("Failed to create maintenance records."))

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'car.maintenance',
            'res_id': rent_contract.id,
            'target': 'current',
        }

    @api.depends('start_date', 'finish_date')
    def _number_of_the_days(self):
        for record in self:
            if record.start_date and record.finish_date:
                start_date = fields.Date.from_string(record.start_date)
                finish_date = fields.Date.from_string(record.finish_date)
                delta = finish_date - start_date
                record.nb_day = delta.days
            else:
                record.nb_day = 0

    @api.depends('services_ids')
    def _damage_cost(self):
        self.costs = 0
        for rec in self:
            for service in rec.services_ids:
                rec.costs = service.price + rec.costs


