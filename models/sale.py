from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CarSale(models.Model):
    _name = "car.sale"
    _description = 'car Records'
    _inherit = ['mail.thread']

    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    payment_method = fields.Selection([('cryptocurrencies', 'Cryptocurrencies'), ('cash', 'Cash'),
                                       ('bank_transfers', 'Bank Transfers'), ('cheque', 'Cheque')],
                                      string='Payment Method', default='cryptocurrencies' )
    pay_mode = fields.Selection([('monthly_installments', 'Monthly Installments'), ('full_payment', 'Full Payment')],
                                string='Pay Mode', default='monthly_installments')
    nbr_years = fields.Selection(
        [('1', '1 year'), ('2', '2 years'), ('3', '3 years'), ('4', '4 years'), ('5', '5 years')],
        string='Number Of Years For Installments', default='1')
    advance_installment = fields.Monetary(
        string='Advanced Installment',
        compute='_advanced_installment',
        readonly=True)
    percentage_advanced = fields.Selection(
        [('0.5', '50%'), ('0.4', '40%'), ('0.3', '30%'), ('0.2', '20%')],
        string='Percentage Of The Advanced Installment', default='0.2')
    percentage_of_increase = fields.Float(string='Percentage Of Increase (%)', compute='_increase', readonly=True)
    monthly_installment = fields.Monetary(string='Monthly Installment', compute='_monthly_installment', readonly=True)
    client_id = fields.Many2one('res.partner', string='The Client', required=True,  ondelete='cascade')
    agency_id = fields.Many2one('company.agency', string='The agency', domain="[('state', '=', 'active')]",
                                required=True,  ondelete='cascade')
    company_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    responsible = fields.Many2one('res.users', related='agency_id.responsible_id', string='Responsible Person',
                                  readonly=True)
    agency_image = fields.Image(string="The Agency Logo", related='agency_id.logo', compute_sudo="True")
    client_image = fields.Image(string="The Client Image", related='client_id.image_1920', compute_sudo="True")
    car_id = fields.Many2one('company.car', string='Car',
                             domain="[('agency_id', '=', agency_id), ('state', '=', 'available')]",  ondelete='cascade')
    date = fields.Date(string="Date of License", related='car_id.date', compute_sudo="True")
    brand_image = fields.Image(string="The Brand Logo", related='car_id.brand_image', compute_sudo="True")
    registration_number = fields.Char(string='Registration Number',
                                      compute_sudo="True", related='car_id.registration_number')
    start_date = fields.Date(
        'Contract Start Date', default=fields.Date.context_today,
        help='Date when the coverage of the contract begins', required=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('cancelled', 'Cancelled'),
         ('in_progress', 'In Progress'),
         ('done', 'Done'),
         ], default='draft', string='Status')
    notes = fields.Html('Terms and Conditions', copy=False)
    sale_price = fields.Monetary(string='Sale Price', required=True)
    active = fields.Boolean(default=True)

    def name_get(self):
        res = []
        for rec in self :
            res.append((rec.id, f'{rec.client_id.name}-{rec.car_id.name_get()[0][1]}'))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('car.sale')
        return super(CarSale, self).create(vals_list)

    def action_draft(self):
        self.car_id.state = 'available'
        self.car_id.active = True
        self.write({'state': 'draft'})

    def action_signe(self):
        self.car_id.state = 'sold'
        self.car_id.active = False
        if self.pay_mode == 'monthly_installments':
            self.write({'state': 'in_progress'})
        else:
            self.write({'state': 'done'})

    def action_cancel(self):
        self.car_id.state = 'available'
        self.car_id.active = True
        self.write({'state': 'cancelled'})

    def action_sign_and_print(self):
        self.car_id.state = 'sold'
        self.car_id.active = False
        if self.pay_mode == 'monthly_installments':
            self.write({'state': 'in_progress'})
        else:
            self.write({'state': 'done'})
        return self.env.ref("car_agency.report_sale").report_action(self)

    def action_return(self):
        self.write({'state': 'draft'})

    @api.depends('sale_price', 'percentage_advanced')
    def _advanced_installment(self):
        self.advance_installment = float(self.percentage_advanced)*self.sale_price

    @api.depends('nbr_years', 'percentage_advanced')
    def _increase(self):
        for record in self:
            if record.percentage_advanced:
                try:
                    record.percentage_of_increase = float(record.nbr_years) // float(record.percentage_advanced)
                except ZeroDivisionError:
                    record.percentage_of_increase = 0
            else:
                record.percentage_of_increase = 0

    @api.depends('sale_price', 'percentage_of_increase', 'percentage_advanced')
    def _monthly_installment(self):
        for record in self:
            if record.nbr_years:
                try:
                    record.monthly_installment = (record.sale_price * (1 + (record.percentage_of_increase / 100)) - record.advance_installment) / ((float(record.nbr_years)) * 12)
                except ZeroDivisionError:
                    record.monthly_installment = 0
            else:
                record.monthly_installment = 0

