{
    "name": "Product default stock putaway rule",
    "summary": "Create an Stock putaway rule by product. By default in res.company if not defined in product.category",
    "version": "17.0.1.0.1",
    "category": "Stock",
    "website": "https://www.puntsistemes.es",
    "author": "Punt Sistemes",
    "maintainers": [
        "PuntSistemes S.L.U"
    ],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "product",
        "stock",
    ],
    "data": [
        'views/res_company_views.xml',
        'views/product_category_views.xml',
        'data/server_actions.xml',
    ],

}
