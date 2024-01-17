{
    "name": "Custom Inplast",
    "summary": "Customs Inplast",
    "version": "17.0.1.0.0",
    'category': 'Product, Picking',
    "author": "Punt Sistemes",
    "website": "https://www.puntsistemes.es",
    "Maintainers":[
        "Equipo rojo",
    ],
    "license": "LGPL-3",
    "depends": [
        "product",
        "stock",
        "account",
        "report_qweb_pdf_watermark",
    ],
    "data": [
        "security/ir.model.access.csv",
#        "views/product_category_views.xml",
        "views/product_template_views.xml",
        "views/stock_location_views.xml",
        "views/menu_views.xml",
        "report/templates.xml",
        "report/ir_action_report.xml",
    ],
    "installable": True,
}
