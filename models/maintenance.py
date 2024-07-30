from odoo import api, fields, models, _


class CarMaintenance(models.Model):

    _name = "car.maintenance"
    _description = 'Car Maintenance'
    _inherit = ['mail.thread']
    _rec_name = 'ref'
    _sql_constraints = [
        ('check_date', 'CHECK(nb_day != 0)',
         ' TThe number Of Repair Days must be positive!'),
    ]

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    reason = fields.Selection([
        ('damaged', 'Damaged'),
        ('situation', 'Situation')
    ], string='The Reason', default='draft', required=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    agency_logo = fields.Image(string='The Agency Logo', related='agency_id.logo', compute_sudo="True")
    agency_id = fields.Many2one('company.agency', string='The Owner Agency', required=True, ondelete='cascade',
                                readonly=True, related='car_id.agency_id')
    brand_image = fields.Image(string="The Brand", related='car_id.brand_image', compute_sudo="True")
    car_situation = fields.Selection([
        ('damaged', 'Damaged'),
        ('available', 'Available')
    ], string='Car Situation', related='car_id.state', compute_sudo="True")
    registration_number = fields.Char(string='Registration Number', related='car_id.registration_number',
                                      compute_sudo="True")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    repairman_id = fields.Many2one('res.partner', string='Repairman', required=True)
    car_id = fields.Many2one('company.car', string='The car',
                             domain="[('state', '=', 'available')]")
    costs = fields.Monetary(string='Cost', compute='_damage_cost', readonly=True)
    services_ids = fields.Many2many('car.services', 'car_services_maintenance', string='Services Needed')
    damage_ids = fields.Many2many('car.damage', 'car_services_damage', string='Damage')
    nb_day = fields.Integer(string='The number Of Repair Days ', compute='_number_of_the_days', readonly=True)
    phone = fields.Char(string="The Worker Phone", related='repairman_id.mobile', compute_sudo="True")
    email = fields.Char(string="The Worker Email", related='repairman_id.email', compute_sudo="True")
    active = fields.Boolean(default=True)
    ref = fields.Char(string="Maintenance Reference", default=lambda self: _('New'))
    notes = fields.Text(string='Notes')
    start_date = fields.Date(
        'Contract Start Date',
        help='Date when the coverage of the contract begins', required=True)
    finish_date = fields.Date(
        'Contract End Date',
        help='Date when the coverage of the contract ends', required=True)

    def name_get(self):
        res = []
        for rec in self :
            res.append((rec.id, f'{rec.start_date}-{rec.ref}'))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('car.maintenance')
        return super(CarMaintenance, self).create(vals_list)

    @api.depends('services_ids')
    def _damage_cost(self):
        self.costs = 0
        for rec in self:
            for service in rec.services_ids:
                rec.costs = service.price + rec.costs

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

    def action_start(self):
            self.write({'state': 'in_progress'})
            self.car_id.state = 'maintenance'

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        if self.reason == 'damaged':
            self.car_id.state = 'damaged'
        else:
            self.car_id.state = 'available'

    def action_draft(self):
        self.write({'state': 'draft'})


