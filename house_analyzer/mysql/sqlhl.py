# coding: utf-8

import logging
from sqlalchemy import distinct
from sqlalchemy.ext.declarative import declarative_base

from conf import config
from mysql.sqlutil import ISqlHelper
from mysql.base import HlHouseBasicInfo
from mysql.base import HlHouseDynamicInfo


_Base = declarative_base()
logger = logging.getLogger(__name__)


class SqlHl(ISqlHelper):
    """sql helper for home_link"""

    def __init__(self, config):
        super(SqlHl, self).__init__(config)

    def query_house_basic_info(self, item):
        try:
            query = self.session.query(HlHouseBasicInfo).filter(HlHouseBasicInfo.house_id == item['house_id'])
            return query.first()
        except Exception as e:
            logger.exception('query house basic info[{0}] exception[{1}]'.format(item, e))

    def insert_or_update_house_basic_info(self, item):
        try:
            row = self.query_house_basic_info(item)
            if row is None:
                logger.info('new house info[{0}].'.format(item['house_id']))
                if item['status'] in config.HOUSE_STATUS_SALE:
                    row = HlHouseBasicInfo(
                        house_id=item['house_id'],
                        city=item['city'],
                        room_info=item['room_info'],
                        floor_info=item['floor_info'],
                        orientation=item['orientation'],
                        decoration=item['decoration'],
                        house_size=item['house_size'],
                        house_type=item['house_type'],
                        community=item['community'],
                        district=item['district'],
                        location=item['location'],
                        room_structure=item['room_structure'],
                        room_size=item['room_size'],
                        building_structure=item['building_structure'],
                        elevator_household_ratio=item['elevator_household_ratio'],
                        elevator_included=item['elevator_included'],
                        property_right_deadline=item['property_right_deadline'],
                        last_trading_date=item['last_trading_date'],
                        status=item['status'],
                        list_date=item['list_date'],
                    )
                else:
                    row = HlHouseBasicInfo(
                        house_id=item['house_id'],
                        city=item['city'],
                        status=item['status'],
                        deal_date=item['deal_date'],
                        deal_total_price=item['deal_total_price'],
                        deal_unit_price=item['deal_unit_price'],
                        deal_time_span=item['deal_time_span'],
                        list_total_price=item['list_total_price'],
                        list_unit_price=item['list_unit_price'],
                        price_change_times=item['price_change_times'],
                        community=item['community'],
                        room_info=item['room_info'],
                        district=item['district'],
                        location=item['location'],
                        house_size=item['house_size'],
                        list_date=item['list_date']
                    )
                return self.add(row)
            else:
                logger.info('old house info[{0}].'.format(item['house_id']))
                if row.status in config.HOUSE_STATUS_SALE and item['status'] in config.HOUSE_STATUS_DEAL:
                    logger.info('house[{0}] status change: [{1}] to [{2}].'.format(row.house_id, row.status, item['status']))
                    row.deal_date = item['deal_date']
                    row.deal_total_price = item['deal_total_price']
                    row.deal_unit_price = item['deal_unit_price']
                    row.deal_time_span = item['deal_time_span']
                    row.list_total_price = item['list_total_price']
                    row.list_unit_price = item['list_unit_price']
                    row.price_change_times = item['price_change_times']

                if row.status != item['status']:
                    logger.info('house[{0}] status change: [{1}] to [{2}].'.format(row.house_id, row.status, item['status']))
                    row.status = item['status']

                self.session.commit()
            return row
        except Exception as e:
            self.session.rollback()
            logger.exception('insert or update house basic info[{0}] exception[{1}].'.format(item, e))

    def get_house_id_list(self, city, house_status):
        try:
            query = self.session.query(HlHouseBasicInfo.house_id).filter(HlHouseBasicInfo.status == house_status)\
                .filter(HlHouseBasicInfo.city == city)
            return query.all()
        except Exception as e:
            logger.exception('get house id list exception[{0}]'.format(e))

    def get_house_id_list_v2(self):
        try:
            sql = "SELECT DISTINCT(house_id) FROM hl_house_dynamic_info WHERE house_id NOT IN (SELECT house_id FROM hl_house_basic_info) "
            query = self.session.execute(sql)
            # query = self.session.query(distinct(HlHouseDynamicInfo.house_id))
            # return query.all()
            return query.fetchall()
        except Exception as e:
            logger.exception('get house id list v2 exception[{0}]'.format(e))

    def query_house_dynamic_info(self, house_id, record_date):
        try:
            query = self.session.query(HlHouseDynamicInfo).filter(HlHouseDynamicInfo.house_id == house_id).filter(HlHouseDynamicInfo.record_date == record_date)
            return query.first()
        except Exception as e:
            logger.exception('query house dynamic info[{0}:{1}] exception[{2}]'.format(house_id, record_date, e))

    def query_newest_house_dynamic_info(self, house_id):
        try:
            query = self.session.query(HlHouseDynamicInfo).filter(HlHouseDynamicInfo.house_id == house_id)\
                .order_by(HlHouseDynamicInfo.record_date.desc())
            return query.first()
        except Exception as e:
            logger.exception('query house dynamic info[{0}] exception[{1}]'.format(house_id, e))

    def insert_or_update_house_dynamic_info(self, house_id, record_date, price):
        try:
            total_price, unit_price = price
            dynamic_info = self.query_newest_house_dynamic_info(house_id)

            if dynamic_info is None:
                logger.info('new house[{0}] dynamic info[{1}|{2}]'.format(house_id, record_date, price))
                new_dynamic_info = HlHouseDynamicInfo(
                    house_id=house_id,
                    record_date=record_date,
                    total_price=total_price,
                    unit_price=unit_price
                )
                self.session.add(new_dynamic_info)
            elif dynamic_info.record_date != record_date:
                if dynamic_info.total_price != total_price:
                    logger.info('house[{0}] dynamic info update from [{1}|{2}] to [{3}|{4}]'.format(
                        house_id, dynamic_info.record_date, (dynamic_info.total_price, dynamic_info.unit_price), record_date, price))
                    new_dynamic_info = HlHouseDynamicInfo(
                        house_id=house_id,
                        record_date=record_date,
                        total_price=total_price,
                        unit_price=unit_price
                    )
                    self.session.add(new_dynamic_info)
            else:
                if dynamic_info.total_price != total_price:
                    logger.info('house[{0}] dynamic info update from [{1}|{2}] to [{3}|{4}]'.format(
                        house_id, dynamic_info.record_date, (dynamic_info.total_price, dynamic_info.unit_price), record_date, price))
                    dynamic_info.total_price = total_price
                    dynamic_info.unit_price = unit_price
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            logger.exception('insert or update house dynamic info[{0}:{1}:{2}] exception[{3}]'.format(house_id, record_date, price, e))

    def get_all_house_basic_info(self):
        try:
            query = self.session.query(HlHouseBasicInfo)
            return query.all()
        except Exception as e:
            logger.exception('get all house basic info exception[{0}]'.format(e))

    def get_all_house_dynamic_info(self):
        try:
            query = self.session.query(HlHouseDynamicInfo)
            return query.all()
        except Exception as e:
            logger.exception('get all house dynamic info exception[{0}]'.format(e))

    # def insert(self, item):
    #     try:
    #         if item['status'] in config.HOUSE_STATUS_SALE:
    #             history = {}
    #             record_date = datetime.datetime.today().strftime('%Y-%m-%d')
    #             history[record_date] = [item['total_price'], item['unit_price']]
    #
    #             row = HomeLink(
    #                 house_id=item['house_id'],
    #                 city=item['city'],
    #                 total_price=item['total_price'],
    #                 unit_price=item['unit_price'],
    #                 room_info=item['room_info'],
    #                 floor_info=item['floor_info'],
    #                 orientation=item['orientation'],
    #                 decoration=item['decoration'],
    #                 house_size=item['house_size'],
    #                 house_type=item['house_type'],
    #                 community=item['community'],
    #                 district=item['district'],
    #                 location=item['location'],
    #                 room_structure=item['room_structure'],
    #                 room_size=item['room_size'],
    #                 building_structure=item['building_structure'],
    #                 elevator_household_ratio=item['elevator_household_ratio'],
    #                 elevator_included=item['elevator_included'],
    #                 property_right_deadline=item['property_right_deadline'],
    #                 last_trading_date=item['last_trading_date'],
    #                 history_price=json.dumps(history),
    #                 status=item['status'],
    #                 list_date=item['list_date'],
    #             )
    #             return self.add(row)
    #         elif item['status'] in config.HOUSE_STATUS_DEAL:
    #             history = {}
    #
    #             list_unit_price = round(item['list_total_price'] / item['house_size'] * 10000, 2)
    #
    #             history[item['list_date']] = [item['list_total_price'], list_unit_price]
    #             history[item['deal_date']] = [item['deal_total_price'], item['deal_unit_price']]
    #
    #             row = HomeLink(
    #                 house_id=item['house_id'],
    #                 city=item['city'],
    #                 status=item['status'],
    #                 deal_date=item['deal_date'],
    #                 deal_total_price=item['deal_total_price'],
    #                 deal_unit_price=item['deal_unit_price'],
    #                 deal_time_span=item['deal_time_span'],
    #                 list_total_price=item['list_total_price'],
    #                 price_change_times=item['price_change_times'],
    #                 history_price=json.dumps(history),
    #
    #                 community=item['community'],
    #                 room_info=item['room_info'],
    #                 district=item['district'],
    #                 location=item['location'],
    #                 total_price=item['total_price'],
    #                 unit_price=item['unit_price'],
    #                 house_size=item['house_size'],
    #                 list_date=item['list_date']
    #             )
    #             return self.add(row)
    #         else:
    #             logger.warning('not matching url:[{0}]'.format(item['url']))
    #             return None
    #     except Exception as e:
    #         logger.exception('insert item[{0}] exception[{1}]'.format(item, e))

    # def update(self, row, item):
    #     try:
    #         if item['status'] in config.HOUSE_STATUS_SALE:
    #             history = None
    #             if row.history_price is None:  # 第一次未记录历史价格，则更新
    #                 history = {row.create_time.strftime('%Y-%m-%d'): [row.total_price, row.unit_price]}
    #                 row.history_price = json.dumps(history)
    #
    #             if row.total_price != item['total_price']:
    #                 if history is None:
    #                     history = json.loads(row.history_price)
    #                 record_date = datetime.datetime.today().strftime('%Y-%m-%d')
    #                 history[record_date] = [item['total_price'], item['unit_price']]
    #                 row.history_price = json.dumps(history)
    #                 logger.info('house[{0}] price change[{1}].'.format(row.house_id, row.history_price))
    #
    #             row.community = item['community']
    #             row.total_price = item['total_price']
    #             row.unit_price = item['unit_price']
    #             row.status = item['status']
    #             self.session.commit()
    #             return True
    #         elif item['status'] in config.HOUSE_STATUS_DEAL:
    #             if row.deal_date is None:
    #                 row.deal_date = item['deal_date']
    #                 row.deal_total_price = item['deal_total_price']
    #                 row.deal_unit_price = item['deal_unit_price']
    #                 row.deal_time_span = item['deal_time_span']
    #                 row.list_total_price = item['list_total_price']
    #                 row.price_change_times = item['price_change_times']
    #
    #                 if row.history_price is None:
    #                     history = {}
    #                     list_date = datetime.datetime.strptime(item['deal_date'], "%Y-%m-%d") - datetime.timedelta(
    #                         days=item['deal_time_span'])
    #                     record_date = list_date.strftime('%Y-%m-%d')
    #                     house_size = round(item['deal_total_price'] / item['deal_unit_price'] * 10000, 2)
    #                     list_unit_price = round(item['list_total_price'] / house_size, 2)
    #                     history[record_date] = [item['list_total_price'], list_unit_price]
    #                     history[item['deal_date']] = [item['deal_total_price'], item['deal_unit_price']]
    #                 else:
    #                     history = json.loads(row.history_price)
    #                     history[item['deal_date']] = [item['deal_total_price'], item['deal_unit_price']]
    #
    #                 row.history_price = json.dumps(history)
    #
    #             row.community = item['community']
    #             row.room_info = item['room_info']
    #             row.district = item['district']
    #             row.location = item['location']
    #             row.total_price = item['total_price']
    #             row.unit_price = item['unit_price']
    #             row.house_size = item['house_size']
    #             row.list_date = item['list_date']
    #
    #             row.status = item['status']
    #             self.session.commit()
    #             return True
    #         else:
    #             logger.warning('not matching url:[{0}]'.format(item['url']))
    #             return False
    #     except Exception as e:
    #         logger.exception('update item[{0}] exception[{1}]'.format(item, e))
    #         self.session.rollback()
    #         return False
    #     finally:
    #         pass

    # def update_session(self):
    #     try:
    #         self.session.commit()
    #     except Exception as e:
    #         logger.exception('update exception[{0}]'.format(e))

    # def get_hl_data(self):
    #     try:
    #         query = self.session.query(HomeLink)
    #         return query.all()
    #     except Exception as e:
    #         logger.exception('get home link data exception[{0}]'.format(e))
