# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    def _check_ticket_has_empty_fields(self):
        self.ensure_one()
        error_message = False
        field_ids = self.stage_id.validate_field_ids
        field_names = [x.name for x in field_ids]
        values = self.read(field_names)
        fields = [
            field.field_description for field in field_ids if not values[0][field.name]
        ]
        fields = ", ".join(fields)
        if fields:
            error_message = _(
                "Ticket %s can't be moved to the stage %s until "
                "the following fields are set: %s."
            ) % (self.name, self.stage_id.name, fields)
        return error_message

    def _validate_stage_fields_error_message(self):
        error_message = []
        for record in self:
            message = record._check_ticket_has_empty_fields()
            if message:
                error_message.append(message)
        return error_message

    @api.constrains("stage_id")
    def _validate_stage_fields(self):
        message = self._validate_stage_fields_error_message()
        if message:
            message = "\n".join(message)
            raise ValidationError(message)
