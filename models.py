from datetime import datetime, timedelta
from sqlalchemy import Column, BigInteger, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
import re
from __init__ import session


Base = declarative_base()


class NumberPlates(Base):
    __tablename__ = 'number_plates'

    id = Column(BigInteger, primary_key=True)
    vrn = Column(Text)

    def get_number_plates(self):
        nb_plates = []
        for vrn, in session.query(NumberPlates.vrn).all():
            nb_plates.append(vrn)
        return nb_plates


class ResidenceParkingLot(Base):
    __tablename__ = 'residence_parking_lot'

    id = Column(BigInteger, primary_key=True)
    vrn = Column(Text)
    event_date = Column(DateTime)
    event_type = Column(Text)

    def get_week_activity(self, vrn, monday_of_week):
        """
        gets the whole activity of a vehicle during a specified week
        :param vrn: vehicle nb plate
        :param monday_of_week: dd-mm-yyyy type string
        :return: entry log list
        """
        datetime_monday = datetime.strptime(monday_of_week, '%d-%m-%Y')
        datetime_sunday = datetime_monday + timedelta(days=7)

        action_log = []
        for row in session.query(ResidenceParkingLot.event_date, ResidenceParkingLot.event_type).\
            filter(ResidenceParkingLot.vrn==vrn):
            action_log.append({'event_date': row.event_date, 'event_type': row.event_type})

        desired_week_events = [event for event in action_log if
                               (event['event_date'] >= datetime_monday and event['event_date'] <= datetime_sunday)]

        return desired_week_events

    def transform_datetime_to_index(self, date: datetime, monday: datetime):
        before = (date - monday).days * 48
        m = 1 if date.minute <= 30 else 2
        day_time = date.hour * 2 + m - 1
        index = before + day_time

        return index

    def get_action_indexes(self, week, monday):
        """
        :param week: list, action log for desired week
        :return: list of dicts with index instead of datetime
        """
        datetime_monday = datetime.strptime(monday, '%d-%m-%Y')
        res = []
        for item in week:
            index = self.transform_datetime_to_index(item['event_date'], datetime_monday)
            res.append({'index': index, 'event_type': item['event_type'],
                        'event_date': re.sub(r':\d{2}\.\d+', '', str(item['event_date']))})

        return res

    def allocate_action_array(self, indexed_log: list):
        """
        0 = car is outside the parking lot, 1 = car is inside the parking lot
        :param indexed_log: list of events where the date was converted into appropiate index
        :return: list of 1s and 0s
        """
        sorted_indexed_log = sorted(indexed_log, key=lambda item: item['index'])
        result = []
        for i in range(336):
            result.append({'index': i, 'value': 0, 'action': 'None', 'timestamp': 'No event registered'})

        prev_index = 0
        for item in sorted_indexed_log:
            value = 1 if item['event_type'] == 'out' else 0
            for i in range(prev_index, item['index']):
                result[i]['value'] = value

            # if item['event_type'] ==
            result[item['index']]['timestamp'] = item['event_date']
            prev_index = item['index']

        value = 1 if sorted_indexed_log[-1]['event_type'] == 'in' else 0
        for i in range(sorted_indexed_log[-1]['index'], 336):
            result[i]['value'] = value

        for i in range(1, 335):
            if result[i]['value'] == 0 and result[i-1]['value'] == 0:
                result[i]['action'] = 'Outside parking lot'
            if result[i]['value'] == 0 and result[i-1]['value'] == 1:
                result[i]['action'] = 'Left the parking lot'
            if result[i]['value'] == 1 and result[i - 1]['value'] == 0:
                result[i]['action'] = 'Entered the parking lot'
            if result[i]['value'] == 1 and result[i - 1]['value'] == 1:
                result[i]['action'] = 'Inside parking lot'

        if result[0]['value'] == 0:
            result[0]['action'] = 'Outside parking lot'
        else:
            result[0]['action'] = 'Inside parking lot'

        if result[-1]['value'] == 0:
            result[-1]['action'] = 'Outside parking lot'
        else:
            result[-1]['action'] = 'Inside parking lot'

        return result

    def calculate_lot_percentages(self, vrn: str, step_data: list):
        """
        :param step_data: calculated data for individual chart
        :return: dict with vrn and calculated percentages of time periods
        """
        in_counter = 0
        out_counter = 0
        for item in step_data:
            if item['value'] == 1:
                in_counter += 1
            else:
                out_counter += 1

        in_percentage = round((in_counter * 100) / len(step_data), 2)
        out_percentage = 100 - in_percentage

        return {
            'name': vrn,
            'in%': in_percentage,
            'out%': out_percentage
        }


class CommercialParkingLot(Base):
    __tablename__ = 'commercial_parking_lot'

    id = Column(BigInteger, primary_key=True)
    mapped_index = Column(Integer)
    value = Column(Integer)
    active_time = Column(Text)  # for querying
    active_date = Column(Text)  # for x axis

    @staticmethod
    def insert_entry(index, value, active_time, active_date):
        entry = CommercialParkingLot(mapped_index=index, value=value, active_time=active_time, active_date=active_date)
        session.add(entry)
        session.commit()

    def get_commercial_day(self, date:str):
        result = []

        for row in session.query(CommercialParkingLot.mapped_index, CommercialParkingLot.value,
                                 CommercialParkingLot.active_time, CommercialParkingLot.active_date).\
            filter(CommercialParkingLot.active_date==date):
            result.append({'index': row.mapped_index, 'value': row.value, 'active_time': row.active_time})

        return sorted(result, key=lambda item: item['index'])


class CommercialParkingLotSummary(Base):
    __tablename__ = 'commercial_parking_lot_summary'

    id = Column(BigInteger, primary_key=True)
    average = Column(Integer)
    maximum = Column(Integer)
    date = Column(DateTime)
    day = Column(Text)

    def get_listings(self, date: str):
        result = []
        datetime_monday = datetime.strptime(date, '%d-%m-%Y')
        datetime_sunday = datetime_monday + timedelta(days=7)

        for row in session.query(CommercialParkingLotSummary.average, CommercialParkingLotSummary.maximum,
                                 CommercialParkingLotSummary.date, CommercialParkingLotSummary.day).\
                filter(datetime_monday <= CommercialParkingLotSummary.date).filter(CommercialParkingLotSummary.date
                                                                                   < datetime_sunday):

            result.append({'name': row.day, 'Average stay in minutes': row.average,
                           'Maximum numbers of cars in lot': row.maximum})

        return result
