# -*- coding: utf-8 -*-
{
    "name": "Fleet Custom SMX",
    "version": "15.0.1.0.0",
    "summary": """ Fleet Custom SMX """,
    "author": "Jchuc",
    "website": "",
    "category": "",
    "depends": ["base", "fleet"],
    "data": [
        "data/sequence_batch_odometer.xml",
        "security/ir.model.access.csv",
        "views/fleet_batch_odometer_views.xml",
        "views/fleet_batch_odometer_line_views.xml",
        "views/fleet_vehicle_odometer_views.xml",
        "views/fleet_vehicle_views.xml"
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
