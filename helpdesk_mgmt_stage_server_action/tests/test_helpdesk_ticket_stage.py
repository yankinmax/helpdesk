# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import RecordCapturer, TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class HelpdeskTicketStageServerAction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.HelpdeskTicket = cls.env["helpdesk.ticket"]
        cls.HelpdeskTicketStage = cls.env["helpdesk.ticket.stage"]
        cls.HelpdeskTicketTag = cls.env["helpdesk.ticket.tag"]
        cls.ServerAction = cls.env["ir.actions.server"]
        cls.server_action_helpdesk_ticket = cls.ServerAction.create(
            {
                "name": "Helpdesk Ticket Server Action",
                "model_id": cls.env["ir.model"]._get_id("helpdesk.ticket"),
                "crud_model_id": cls.env["ir.model"]._get_id("helpdesk.ticket"),
                "value": str(cls.env.user.id),
                "update_path": "user_id",
                "update_field_id": cls.env["ir.model.fields"]._get_ids(
                    "helpdesk.ticket"
                )["user_id"],
                "evaluation_type": "value",
                "state": "object_write",
            }
        )
        cls.helpdesk_ticket_stage_1 = cls.HelpdeskTicketStage.create(
            {"name": "Stage 1", "sequence": 1}
        )
        cls.helpdesk_ticket_stage_2 = cls.HelpdeskTicketStage.create(
            {
                "name": "Stage 2",
                "action_id": cls.server_action_helpdesk_ticket.id,
                "sequence": 2,
            }
        )

    def test_helpdesk_ticket_create(self):
        self.helpdesk_ticket_1 = self.HelpdeskTicket.create(
            {
                "name": "Helpdesk Ticket 1",
                "stage_id": self.helpdesk_ticket_stage_2.id,
                "description": "Helpdesk Ticket Description",
            }
        )
        self.assertEqual(self.helpdesk_ticket_1.user_id, self.env.user)

    def test_helpdesk_ticket_write(self):
        self.helpdesk_ticket_2 = self.HelpdeskTicket.create(
            {
                "name": "Helpdesk Ticket 2",
                "stage_id": self.helpdesk_ticket_stage_1.id,
                "description": "Helpdesk Ticket Description",
            }
        )
        self.helpdesk_ticket_3 = self.HelpdeskTicket.create(
            {
                "name": "Helpdesk Ticket 3",
                "stage_id": self.helpdesk_ticket_stage_1.id,
                "description": "Helpdesk Ticket Description",
            }
        )
        self.assertNotEqual(self.helpdesk_ticket_2.user_id, self.env.user)
        self.assertNotEqual(self.helpdesk_ticket_3.user_id, self.env.user)
        self.helpdesk_ticket_2.write({"stage_id": self.helpdesk_ticket_stage_2.id})
        self.helpdesk_ticket_3.write({"stage_id": self.helpdesk_ticket_stage_2.id})
        self.assertEqual(self.helpdesk_ticket_2.user_id, self.env.user)
        self.assertEqual(self.helpdesk_ticket_3.user_id, self.env.user)
        self.helpdesk_ticket_3.write({"user_id": False})
        self.helpdesk_ticket_3.write({"stage_id": self.helpdesk_ticket_stage_2.id})
        self.assertFalse(self.helpdesk_ticket_3.user_id)

    def test_helpdesk_ticket_without_stage(self):
        self.helpdesk_ticket_4 = self.HelpdeskTicket.create(
            {
                "name": "Helpdesk Ticket 4",
                "description": "Helpdesk Ticket Description",
            }
        )
        self.assertFalse(self.helpdesk_ticket_4.user_id)
        self.helpdesk_ticket_stage_3 = self.HelpdeskTicketStage.create(
            {
                "name": "Stage 3",
                "sequence": 3,
            }
        )
        self.helpdesk_ticket_4.write({"stage_id": self.helpdesk_ticket_stage_3.id})
        self.assertFalse(self.helpdesk_ticket_4.user_id)
        self.helpdesk_ticket_4.write({"stage_id": self.helpdesk_ticket_stage_2.id})
        self.assertEqual(self.helpdesk_ticket_4.user_id, self.env.user)

    def test_helpdesk_ticket_run_action(self):
        create_tag_action = self.ServerAction.create(
            {
                "model_id": self.env["ir.model"]._get_id("helpdesk.ticket.tag"),
                "crud_model_id": self.env["ir.model"]._get_id("helpdesk.ticket.tag"),
                "name": "Create new helpdesk tag",
                "value": "New helpdesk tag",
                "state": "object_create",
            }
        )
        stage_1 = self.HelpdeskTicketStage.create(
            {"name": "Stage 1", "sequence": 1, "action_id": create_tag_action.id}
        )
        ticket = self.HelpdeskTicket.create(
            {
                "name": "Create a tag ticket",
                "description": "Ticket Description",
            }
        )
        self.assertFalse(
            self.HelpdeskTicketTag.search([("name", "=", "New helpdesk tag")]).exists()
        )
        with RecordCapturer(self.HelpdeskTicketTag, []) as capture:
            ticket.write({"stage_id": stage_1.id})
        tag = capture.records
        self.assertEqual(1, len(tag))
        self.assertEqual("New helpdesk tag", tag.name)
