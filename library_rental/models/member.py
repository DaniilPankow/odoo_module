from odoo import fields, models


class LibraryMember(models.Model):
    _name = "library.member"
    _description = "Library Member"

    name = fields.Char(required=True)
    membership_number = fields.Char(required=True)
    email = fields.Char()
    phone = fields.Char()
    user_id = fields.Many2one(
        "res.users",
        string="Користувач Odoo",
        ondelete="restrict",
        required=False,
    )
    loan_ids = fields.One2many("library.loan", "member_id")

    _membership_number_unique = models.Constraint(
        "unique(membership_number)",
        "Membership number must be unique.",
    )
    _user_id_unique = models.Constraint(
        "unique(user_id)",
        "Цей користувач уже прив'язаний до іншого читача",
    )
