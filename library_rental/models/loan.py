import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LibraryLoan(models.Model):
    _name = "library.loan"
    _description = "Library Loan"

    LOAN_PERIOD_DAYS = 14
    FINE_RATE_PER_DAY = 5.0

    copy_id = fields.Many2one("library.copy", required=True, ondelete="restrict")
    member_id = fields.Many2one("library.member", required=True, ondelete="restrict")
    loan_date = fields.Date(default=fields.Date.context_today)
    due_date = fields.Date(
        string="Термін повернення",
        compute="_compute_due_date",
        store=True,
    )
    fine_amount = fields.Float(
        string="Сума штрафу",
        compute="_compute_fine_amount",
        store=True,
    )
    is_overdue = fields.Boolean(
        string="Прострочено",
        compute="_compute_is_overdue",
    )
    return_date = fields.Date()
    state = fields.Selection(
        [
            ("active", "Active"),
            ("returned", "Returned"),
        ],
        default="active",
    )
    book_id = fields.Many2one(
        related="copy_id.book_id",
        store=False,
        readonly=True,
    )
    author = fields.Char(related="copy_id.book_id.author", readonly=True)

    @api.depends("loan_date")
    def _compute_due_date(self):
        for record in self:
            record.due_date = (
                record.loan_date + timedelta(days=self.LOAN_PERIOD_DAYS)
                if record.loan_date
                else False
            )

    @api.depends("return_date", "due_date")
    def _compute_fine_amount(self):
        for record in self:
            record.fine_amount = (
                (record.return_date - record.due_date).days * self.FINE_RATE_PER_DAY
                if record.return_date and record.due_date and record.return_date > record.due_date
                else 0.0
            )

    @api.depends("state", "due_date")
    def _compute_is_overdue(self):
        for record in self:
            record.is_overdue = bool(
                record.state == "active"
                and record.due_date
                and record.due_date < fields.Date.context_today(record)
            )

    @api.onchange("copy_id")
    def _onchange_copy_id(self):
        if self.copy_id and self.env["library.loan"].search_count([
            ("copy_id", "=", self.copy_id.id),
            ("state", "=", "active"),
            ("id", "!=", self._origin.id),
        ]):
            return {
                "warning": {
                    "title": "Примірник уже видано",
                    "message": f"Для примірника «{self.copy_id.display_name}» уже є активна видача.",
                },
            }

    @api.constrains("copy_id", "state")
    def _check_active_copy_loan(self):
        for rec in self:
            if rec.state == "active" and rec.copy_id:
                other_loans = self.env["library.loan"].search([
                    ("copy_id", "=", rec.copy_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", rec.id),
                ])
                if other_loans:
                    raise ValidationError(
                        f"Примірник «{rec.copy_id.display_name}» уже має активну видачу."
                    )

    @api.constrains("loan_date", "due_date")
    def _check_due_date_after_loan_date(self):
        for rec in self:
            if rec.loan_date and rec.due_date and rec.due_date <= rec.loan_date:
                raise ValidationError(
                    "Термін повернення має бути пізніше дати видачі."
                )

    @api.constrains("loan_date", "return_date")
    def _check_return_date_not_before_loan_date(self):
        for rec in self:
            if rec.loan_date and rec.return_date and rec.return_date < rec.loan_date:
                raise ValidationError(
                    "Дата повернення не може бути раніше дати видачі."
                )

    @api.model
    def _cron_check_overdue_loans(self):
        overdue_loans = self.search([
            ("state", "=", "active"),
            ("due_date", "<", fields.Date.context_today(self)),
        ])
        for loan in overdue_loans:
            try:
                with self.env.cr.savepoint():
                    _logger.info(
                        "Прострочена видача %s, термін повернення: %s",
                        loan.id,
                        loan.due_date,
                    )
            except Exception:
                _logger.exception("Не вдалося обробити видачу %s", loan.id)
                continue
        _logger.info("Загальна кількість прострочених видач: %s", len(overdue_loans))
