from odoo import models, fields, api, _
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo.tools import formatLang, format_date

class AccountMove(models.Model):
    _inherit = "account.move"


    @api.depends('partner_id')
    def _get_partner_referrers(self):
        for record in self:
            lines = []
            if record.partner_id.referrer_plan_ids.ids and record.id:
                # Factura nueva, tiramos de comisionistas del contacto:
                referrers = record.partner_id.referrer_plan_ids
                # Si la factura viene desde pedido de venta:
                amsalelines = self.env['account.move.line'].search([('move_id','=',record.id),('sale_line_ids','!=',False)])
                if amsalelines.ids:
                    referrers = amsalelines[0].sale_line_ids[0].order_id.referrer_plan_ids
                # Si es factura rectificativa:
                original_invoice = self.env['account.move'].search([('reversal_move_id','in',record.id)])
                if record.move_type in ['in_refund','out_refund'] and original_invoice.ids:
                    referrers = original_invoice[0].referrer_plan_ids

                for li in referrers:
                    newline = self.env['referrer.plan.rel'].create({
                        'referrer_id': li.referrer_id.id,
                        'invoice_id': record.id,
                        'credit_commission_po_line_id': li.commission_po_line_id.id,
                    })
                    # Para evitar que en la creación ponga el valor por defecto y tome el de la factura:
                    newline.write({'commission_plan_id':li.commission_plan_id.id})
                    lines.append(newline.id)

            record['referrer_plan_ids'] = [(6,0,lines)]
    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'invoice_id', string='Referrers', store=True,
                                        compute='_get_partner_referrers')

    # Sobreescribir la regla enterprise para considerar varios, es requerido por la búsqueda de campos m2o estándar:
    def _make_commission(self):
        for move in self.filtered(lambda m: m.move_type in ['out_invoice', 'in_invoice', 'out_refund']):
            if move.move_type in ['out_invoice', 'in_invoice']:
                sign = 1
                # (original) if move.commission_po_line_id or not move.referrer_id:
                if move.referrer_plan_ids.commission_po_line_id or not move.referrer_plan_ids.ids:
                    continue
            else:
                sign = -1
                # (original) if not move.commission_po_line_id:
                if not move.referrer_plan_ids.credit_commission_po_line_id.ids:
                    continue

            # Aquí creamos el bucle para varios comisionistas (alcanza el resto del método):
            for li in move.referrer_plan_ids:
                comm_by_rule = defaultdict(float)
                product = None
                order = None
                desc_lines = ""
                for line in move.invoice_line_ids:
                    # (original, ponemos aquí el método completo: rule = line._get_commission_rule()
                    template = line.env['sale.order.template']
                    sale_order = line.subscription_id or line.sale_line_ids.order_id
                    if len(sale_order) == 1:
                        template = sale_order.sale_order_template_id
                    # check whether the product is part of the subscription template
                    template_products = template.sale_order_template_line_ids.product_id.mapped('product_tmpl_id')
                    template_id = template.id if template and line.product_id.product_tmpl_id.id in template_products.ids else None
                    sub_pricelist = line.subscription_id.pricelist_id
                    pricelist_id = sub_pricelist and sub_pricelist.id or line.sale_line_ids.mapped(
                        'order_id.pricelist_id')[:1].id

                    # In order of precedence, the commission plan can be one of:
                    # 1. the commission plan set on the subscription
                    # 2. the commission plan set on the sale order
                    # 3. the referrer's commission plan
                    plan = line.sale_line_ids.order_id.commission_plan_id or li.commission_plan_id
                    if line.subscription_id:
                        plan = line.subscription_id.commission_plan_id
                    #if not plan: (siempre va a haber, si hay "li" ya que es un campo requerido)
                    #    return self.env['commission.rule']
                    rule = plan._match_rules(line.product_id, template_id, pricelist_id)

                    # Aquí continúa el estándar enterprise:
                    if rule:
                        if not product:
                            product = rule.plan_id.product_id
                        if not order:
                            order = line.subscription_id
                            desc_lines += _("\n%s: from %s to %s", line.product_id.name,
                                            format_date(self.env, line.deferred_start_date),
                                            format_date(self.env, line.deferred_end_date))
                        commission = move.currency_id.round(line.price_subtotal * rule.rate / 100.0)
                        comm_by_rule[rule] += commission

                # regulate commissions
                for r, amount in comm_by_rule.items():
                    if r.is_capped:
                        amount = min(amount, r.max_commission)
                        comm_by_rule[r] = amount

                total = sum(comm_by_rule.values())

                if not total:
                    continue

                # build description lines
                desc = _(
                    'Commission on %(invoice)s, %(partner)s, %(amount)s',
                    invoice=move.name,
                    partner=move.partner_id.name,
                    amount=formatLang(self.env, move.amount_untaxed, currency_obj=move.currency_id),
                )

                if order:
                    desc += f"\n{order.name}, {desc_lines}"
                    # extend the description to show the number of months to defer the expense over
                    end_date_list = move.invoice_line_ids.mapped('deferred_end_date')
                    start_date_list = move.invoice_line_ids.mapped('deferred_start_date')
                    if any(start_date_list) and any(end_date_list):
                        date_to = max((ed for ed in end_date_list if ed))
                        date_from = min((sd for sd in start_date_list if sd))
                        # we calculate the delta according to the whole range to avoid 11 month and 29 days= 11 months
                        delta = relativedelta(date_to + relativedelta(days=1), date_from)
                        n_months = delta.years * 12 + delta.months + delta.days // 30
                        if n_months:
                            desc += _(' (%d month(s))', n_months)

                # Saltamos método estándar para incluir código directamente:
                # (original) purchase = move._get_commission_purchase_order()
                purchase = self.env['purchase.order'].sudo().search([
                    ('partner_id', '=', li.referrer_id.id),
                    ('company_id', '=', self.company_id.id),
                    ('state', '=', 'draft'),
                    ('currency_id', '=', self.currency_id.id),
                    ('purchase_type', '=', 'commission'),
                ], limit=1)

                if not purchase:
                    sales_rep = self._get_sales_representative()
                    purchase = self.env['purchase.order'].with_context(mail_create_nosubscribe=True).sudo().create({
                        'partner_id': li.referrer_id.id,
                        'currency_id': self.currency_id.id,
                        'company_id': self.company_id.id,
                        'fiscal_position_id': self.env['account.fiscal.position'].with_company(
                            self.company_id)._get_fiscal_position(li.referrer_id).id,
                        'payment_term_id': li.referrer_id.with_company(
                            self.company_id).property_supplier_payment_term_id.id,
                        'user_id': sales_rep and sales_rep.id or False,
                        'dest_address_id': li.referrer_id.id,
                        'origin': self.name,
                        'purchase_type': 'commission',
                    })

                # Por aquí continúa el estándar del módulo:
                line = self.env['purchase.order.line'].sudo().create({
                    'name': desc,
                    'product_id': product.id,
                    'product_qty': 1,
                    'price_unit': total * sign,
                    'product_uom': product.uom_id.id,
                    'date_planned': fields.Datetime.now(),
                    'order_id': purchase.id,
                    'qty_received': 1,
                })

                if move.move_type in ['out_invoice', 'in_invoice']:
                    # link the purchase order line to the invoice
                    # (original) move.commission_po_line_id = line
                    li.commission_po_line_id = line
                    msg_body = _('New commission. Invoice: %s. Amount: %s.',
                                 move._get_html_link(),
                                 formatLang(self.env, total, currency_obj=move.currency_id))
                else:
                    msg_body = _('Commission refunded. Invoice: %s. Amount: %s.',
                                 move._get_html_link(),
                                 formatLang(self.env, total, currency_obj=move.currency_id))
                purchase.message_post(body=msg_body)
