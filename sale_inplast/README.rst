Sales Inplast
=============

Client modifications and adaptations for sales in Inplast.

**Table of Contents**

.. contents::
   :local:

Configuration
=============

None.

Usage
=====

- Standard Odoo sales and invoice workflows.
- Manual discounts are preserved when prices are recalculated on invoices.
- Daily scheduled action recomputes active pricelist state at 02:00 local time
  (configured as UTC ``nextcall`` in cron).

Known issues
============

There are no known problems at present.

Authors
=======

`Punt <https://www.puntsistemes.es>`__.

.. image:: /sale_inplast/static/img/punt-sistemes.png
   :alt: Punt
   :target: https://www.puntsistemes.es
