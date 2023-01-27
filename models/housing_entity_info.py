# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HousingEntityInfo(models.Model):
    _name = 'jt.housing.entity.info.base'
    _description = 'Housing entity info base'
    _order = 'priority desc, sequence, name'