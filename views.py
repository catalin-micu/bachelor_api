from flask import Blueprint, jsonify, request
from models import NumberPlates, ResidenceParkingLot, CommercialParkingLot, CommercialParkingLotSummary

main = Blueprint('api', __name__)
PARKING_LOT_VRNS = ['VN20BRN', 'IF042090', 'DB08FEF', 'MH14WOW', 'AB27BIM', 'B251RZV', 'CT02PTL']


@main.route('/add_vrn', methods=['POST'])
def add_vrn():

    return 'DONE', 201


@main.route('/get_listings')
def get_listings():
    table = NumberPlates()
    listings = table.get_number_plates()

    return jsonify({'listings': listings, 'flag': 'esti_bunnnn'})


@main.route('/getWeekActivity', methods=['POST'])
def get_week_activity():
    parameters = request.get_json()
    table = ResidenceParkingLot()
    d = table.get_week_activity(parameters['vrn'], parameters['date'])  # 10-05-2021
    r = table.get_action_indexes(d, parameters['date'])

    return jsonify(table.allocate_action_array(r))


@main.route('/getWeekLotSummary', methods=['POST'])
def get_lot_summary():
    table = ResidenceParkingLot()
    parameters = request.get_json()
    result = []
    for vrn in PARKING_LOT_VRNS:
        d = table.get_week_activity(vrn, parameters['date'])  # 10-05-2021
        r = table.get_action_indexes(d, parameters['date'])
        x = table.allocate_action_array(r)
        result.append(table.calculate_lot_percentages(vrn, x))

    return jsonify(result)

@main.route('/commercialDay', methods=['POST'])
def get_commercial_day_variance():
    table = CommercialParkingLot()
    parameters = request.get_json()
    result = table.get_commercial_day(parameters['date'])

    return jsonify(result)

@main.route('/commercialDayPercentages', methods=['POST'])
def get_commercial_values_for_percentages():
    table = CommercialParkingLot()
    parameters = request.get_json()
    result = []
    entries = table.get_commercial_day(parameters['date'])

    for item in entries:
        if ':00' in item['active_time']:
            result.append({'time': item['active_time'], 'occupied': item['value'], 'unoccupied': 3000 - int(item['value'])})

    return jsonify(result)

@main.route('/commercialWeek', methods=['POST'])
def get_commercial_week():
    table = CommercialParkingLotSummary()
    parameters = request.get_json()
    result = []

    entries = table.get_listings(parameters['date'])

    return jsonify(entries)
