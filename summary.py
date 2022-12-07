import copy
import datetime
import json
import queue
from decimal import ROUND_HALF_UP
from decimal import Decimal
from pathlib import Path

from dateutil.parser import parse
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape

base = Path(__file__).parents[0]
env = Environment(
    loader=FileSystemLoader(base),
    autoescape=select_autoescape()
)


class BaseTradeImporter:
    def __init__(self, path):
        self.trades = self.read_file(path)
        self.legs = self.get_legs(self.trades)

    def read_file(self, path):
        raise NotImplementedError

    def get_legs(self, trades):
        raise NotImplementedError


class TdaTradeImporter(BaseTradeImporter):
    def read_file(self, path):
        with open(path, 'r') as f:
            trades = json.load(f, parse_float=Decimal)
        return reversed(trades)

    def get_legs(self, trades):
        legs = []
        for trade in trades:
            instruction = None
            symbol = None
            order_id = trade['orderId']
            for order_leg in trade['orderLegCollection']:
                instruction = order_leg['instruction']
                symbol = order_leg['instrument']['symbol']

            for order_activity in trade['orderActivityCollection']:
                for execution_leg in order_activity['executionLegs']:
                    legs.append({
                        'quantity': int(execution_leg['quantity']),
                        'price': execution_leg['price'],
                        'time': parse(execution_leg['time']),
                        'instruction': instruction,
                        'symbol': symbol,
                        'order_id': order_id
                    })

        return legs


def get_positions(legs):
    positions = []
    current_positions = {}
    for leg in legs:
        if not leg['symbol'] in current_positions:
            current_positions[leg['symbol']] = queue.Queue()
        if leg['instruction'] in ['BUY', 'SELL_SHORT']:
            quantity = leg['quantity']
            for i in range(quantity):
                symbol = leg['symbol']
                instruction = leg['instruction']
                price = leg['price']
                time = leg['time']
                order_id = leg['order_id']
                share = {
                    'symbol': symbol,
                    'instruction': instruction,
                    'price': price,
                    'time': time,
                    'order_id': order_id
                }
                current_positions[leg['symbol']].put(share)
        elif leg['instruction'] in ['SELL', 'BUY_TO_COVER']:
            closing_quantity = leg['quantity']
            closing_instruction = leg['instruction']
            closing_price = leg['price']
            closing_time = leg['time']
            to_be_closed = []
            for i in range(closing_quantity):
                share = current_positions[leg['symbol']].get()
                to_be_closed.append(share)
            risk = sum(share['price'] for share in to_be_closed)
            average_price = (risk / closing_quantity).quantize(Decimal('.0001'), ROUND_HALF_UP)
            assert len(to_be_closed) == closing_quantity
            symbol = share['symbol']
            instruction = share['instruction']
            time = share['time']
            opening_leg = {'symbol': symbol, 'instruction': instruction, 'quantity': len(to_be_closed), 'price': average_price, 'time': time,
                           'risk': risk.quantize(Decimal('.0001'), ROUND_HALF_UP)}
            closing_leg = {'symbol': symbol, 'instruction': closing_instruction, 'quantity': closing_quantity,
                           'price': closing_price, 'time': closing_time}
            order_ids = [share['order_id'] for share in to_be_closed]
            order_ids.append(leg['order_id'])
            position = {
                'opening': opening_leg,
                'closing': closing_leg,
                'order_ids': order_ids
            }
            positions.append(position)

    # Add the open positions
    for symbol, q in current_positions.items():
        if q.qsize():
            still_open = []
            for i in range(q.qsize()):
                still_open.append(q.get())
            risk = sum(share['price'] for share in still_open)
            average_price = (risk / len(still_open)).quantize(Decimal('.0001'), ROUND_HALF_UP)
            symbol = share['symbol']
            instruction = share['instruction']
            time = share['time']
            opening_leg = {'symbol': symbol, 'instruction': instruction, 'quantity': len(still_open),
                           'price': average_price, 'time': time, 'risk': risk.quantize(Decimal('.0001'), ROUND_HALF_UP)}
            order_ids = [share['order_id'] for share in still_open]
            position = {
                'opening': opening_leg,
                'order_ids': order_ids
            }
            positions.append(position)
    return positions


def get_position_summaries(positions):
    position_summaries = []
    for position in positions:
        position_summary = {}
        position_summaries.append(position_summary)
        order_ids = position['order_ids']
        number_legs = len(set(order_ids))
        risk = position['opening']['risk']
        quantity = position['opening']['quantity']
        price = position['opening']['price']
        symbol = position['opening']['symbol']
        direction = 'Long' if position['opening']['instruction'] == 'BUY' else 'Short'
        entry_date = position['opening']['time'].date()
        if len(position) > 2:
            size = quantity * position['closing']['price']
            exit_price = size / quantity
            rounded_exit_price = exit_price.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            profit_percentage = ((exit_price / price) - 1) * 100
            profit_percentage = profit_percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            profit = size - risk
            rounded_profit = profit.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            exit_date = position['closing']['time'].date()
            days = (exit_date - entry_date).days
        else:
            rounded_exit_price = None
            exit_date = None
            rounded_profit = None
            profit_percentage = None
            days = (datetime.datetime.now().date() - entry_date).days
        position_summary.update({
            'symbol': symbol,
            'risk': risk,
            'entry_date': entry_date,
            'average_price': price,
            'exit_price': rounded_exit_price,
            'exit_date': exit_date,
            'days': days,
            'quantity': quantity,
            'direction': direction,
            'profit': rounded_profit,
            'profit_percentage': profit_percentage,
            'number_legs': number_legs
        })
    return position_summaries


def write_output(position_summaries, keys=None, template_file='template.html', output_file='output.html'):
    if keys is None:
        keys = ['symbol', 'direction', 'entry_date', 'average_price', 'exit_price', 'exit_date', 'days', 'quantity', 'risk',
                'profit_percentage', 'profit', 'number_legs']
    template = env.get_template(template_file)
    output = template.render(position_summaries=position_summaries, keys=keys)
    with open(output_file, 'w') as f:
        f.write(output)


def main():
    importer = TdaTradeImporter('trades.json')
    positions = get_positions(importer.legs)
    position_summaries = get_position_summaries(positions)
    write_output(position_summaries)


if __name__ == '__main__':
    main()

