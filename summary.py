import json
from dateutil.parser import parse
from decimal import Decimal, ROUND_HALF_UP
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

base = Path(__file__).parents[0]
env = Environment(
    loader=FileSystemLoader(base),
    autoescape=select_autoescape()
)


def read_json_file(file_name):
    with open(file_name, 'r') as f:
        trades = json.load(f, parse_float=Decimal)
    return reversed(trades)


def get_legs(trades):
    legs = []
    for trade in trades:
        instruction = None
        symbol = None
        for order_leg in trade['orderLegCollection']:
            instruction = order_leg['instruction']
            symbol = order_leg['instrument']['symbol']

        for order_activity in trade['orderActivityCollection']:
            for execution_leg in order_activity['executionLegs']:
                legs.append({
                    'quantity': execution_leg['quantity'],
                    'price': execution_leg['price'],
                    'time': execution_leg['time'],
                    'instruction': instruction,
                    'symbol': symbol
                })

    return legs


def parse_time(legs):
    for leg in legs:
        time = parse(leg['time'])
        leg['time'] = time
    return legs


def get_positions(legs):
    positions = []
    current_positions = {}
    for leg in legs:
        if not leg['symbol'] in current_positions:
            current_positions[leg['symbol']] = []
            positions.append(current_positions[leg['symbol']])
        current_positions[leg['symbol']].append(leg)
        if leg['quantity'] != current_positions[leg['symbol']][0]['quantity']:
            new_position = []
            # new_quantity = current_positions[leg['symbol']][0]['quantity'] - leg['quantity']
            # current_positions[leg['symbol']][0].update({
            #     'quantity': new_quantity
            # })
            quantity = current_positions[leg['symbol']][0]['quantity'] - leg['quantity']
            new_leg = {
                'symbol': current_positions[leg['symbol']][0]['symbol'],
                'instruction': current_positions[leg['symbol']][0]['instruction'],
                'quantity': quantity,
                'price': current_positions[leg['symbol']][0]['price'],
                'time': current_positions[leg['symbol']][0]['time']
            }
            new_position.append(new_leg)
            positions.append(new_position)
        if leg['instruction'] in ['SELL', 'BUY_TO_COVER']:
            del current_positions[leg['symbol']]
    return positions


def get_position_summaries(positions):
    position_summaries = []
    for position in positions:
        position_summary = {}
        position_summaries.append(position_summary)
        opening = [l for l in position if l['instruction'] in ['BUY', 'SELL_SHORT']]
        closing = [l for l in position if l['instruction'] in ['SELL', 'BUY_TO_COVER']]
        quantity = sum([l['quantity'] for l in opening])
        risk = sum([l['quantity'] * l['price'] for l in opening])
        average_price = risk / quantity
        symbol = opening[0]['symbol']
        direction = 'Long' if opening[0]['instruction'] == 'BUY' else 'Short'
        entry_date = position[0]['time'].date()
        if closing:
            size = sum([l['quantity'] * l['price'] for l in closing])
            closing_quantity = sum([l['quantity'] for l in closing])
            # assert closing_quantity == quantity
            exit_price = size / quantity
            profit_percentage = ((exit_price / average_price) - 1) * 100
            profit_percentage = profit_percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            profit = size - risk
            exit_date = position[-1]['time'].date()
            days = (exit_date - entry_date).days
        else:
            exit_price = None
            exit_date = None
            profit = None
            profit_percentage = None
            days = (datetime.datetime.now().date() - entry_date).days
        position_summary.update({
            'symbol': symbol,
            'risk': risk,
            'entry_date': entry_date,
            'average_price': average_price,
            'exit_price': exit_price,
            'exit_date': exit_date,
            'days': days,
            'quantity': quantity,
            'direction': direction,
            'profit': profit,
            'profit_percentage': profit_percentage
        })
    return position_summaries


def write_output(position_summaries, keys=None, template_file='template.html', output_file='output.html'):
    if keys is None:
        keys = ['symbol', 'direction', 'entry_date', 'average_price', 'exit_price', 'exit_date', 'days', 'quantity', 'risk',
                'profit_percentage', 'profit']
    template = env.get_template(template_file)
    output = template.render(position_summaries=position_summaries, keys=keys)
    with open(output_file, 'w') as f:
        f.write(output)


def main():
    trades = read_json_file('trades.json')
    legs = get_legs(trades)
    legs = parse_time(legs)
    positions = get_positions(legs)
    position_summaries = get_position_summaries(positions)
    write_output(position_summaries)


main()

