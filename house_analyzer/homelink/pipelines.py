# -*- coding: utf-8 -*-

import logging
from homelink.items import *
from scrapy.exceptions import DropItem


logger = logging.getLogger(__name__)


class FilterPipeline(object):
    def process_item(self, item, spider):
        logger.info('process item[{0}] in filter pipeline'.format(item))

        sql_helper = getattr(spider, 'sql_helper', None)
        if not sql_helper:
            raise DropItem('sql helper is None: [{0}]'.format(item))

        if isinstance(item, HlHouseItem):
            sql_helper.insert_or_update_house_basic_info(item)
            sql_helper.insert_or_update_house_dynamic_info(item)
        elif isinstance(item, HlCommunityBasicInfoItem):
            sql_helper.insert_or_update_community_basic_info(item)
        elif isinstance(item, HlCommunityDynamicInfoItem):
            sql_helper.insert_or_update_community_dynamic_info(item)
        else:
            raise DropItem('unknown item: [{0}]'.format(item))

        return item
