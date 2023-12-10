import io

from odoo import models
from odoo.tools import format_amount, format_date, format_datetime, pdf


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        result = super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)
        if self._get_report(report_ref).report_name != 'sale.report_saleorder':
            return result

        orders = self.env['sale.order'].browse(res_ids)

        for order in orders:
            initial_stream = result[order.id]['stream']
            if initial_stream:
                order_template = order.sale_order_template_id
                header_record = order_template if order.pnt_sale_header elif order_template.sale_header else order.company_id
# backup:                footer_record = order_template if order_template.sale_footer else order.company_id
                footer_record = order_template if order.pnt_sale_footer elif order_template.sale_footer else order.company_id
                has_header = bool(header_record.sale_header)
                has_footer = bool(footer_record.sale_footer)
                included_product_docs = self.env['product.document']
                for line in order.order_line:
                    product_product_docs = line.product_id.product_document_ids
                    product_template_docs = line.product_template_id.product_document_ids
                    doc_to_include = (
                        product_product_docs.filtered(lambda d: d.attached_on == 'inside')
                        or product_template_docs.filtered(lambda d: d.attached_on == 'inside')
                    )
                    included_product_docs = included_product_docs | doc_to_include

                if (not has_header and not included_product_docs and not has_footer):
                    continue

                IrBinary = self.env['ir.binary']
                so_form_fields = self._get_so_form_fields_mapping(order)
                pdf_data = []
                if has_header:
                    header_stream = IrBinary._record_to_stream(header_record, 'sale_header').read()
                    header_stream = pdf.fill_form_fields_pdf(header_stream, so_form_fields)
                    pdf_data.append(header_stream)
                if included_product_docs:
                    docs_streams = self._fill_sol_documents_fields(
                        order, included_product_docs, so_form_fields
                    )
                    pdf_data.extend(docs_streams)

                pdf_data.append((initial_stream).getvalue())
                if has_footer:
                    footer_stream = IrBinary._record_to_stream(footer_record, 'sale_footer').read()
                    footer_stream = pdf.fill_form_fields_pdf(footer_stream, so_form_fields)
                    pdf_data.append(footer_stream)

                stream = io.BytesIO(pdf.merge_pdf(pdf_data))
                result[order.id].update({'stream': stream})

        return result