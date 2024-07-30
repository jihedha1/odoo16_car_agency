# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    car_agency_notes = fields.Char(
        string='Terms and Conditions',
        config_parameter='car_agency.notes'
    )


