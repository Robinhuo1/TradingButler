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
            for order_leg in trade['orderLegCollection']:
                instruction = order_leg['instruction']
                symbol = order_leg['instrument']['symbol']

            for order_activity in trade['orderActivityCollection']:
                for execution_leg in order_activity['executionLegs']:
                    legs.append({
                        'quantity': execution_leg['quantity'],
                        'price': execution_leg['price'],
                        'time': parse(execution_leg['time']),
                        'instruction': instruction,
                        'symbol': symbol
                    })

        return legs


def get_positions(legs):
    positions = []
    current_positions = {}
    for leg in legs:
        if not leg['symbol'] in current_positions:
            current_positions[leg['symbol']] = []
            # current_position = current_positions[leg['symbol']]
            positions.append(current_positions[leg['symbol']])
        current_positions[leg['symbol']].append(leg)
        if leg['quantity'] != current_positions[leg['symbol']][0]['quantity'] and leg['instruction'] in ['SELL', 'BUY_TO_COVER'] and leg['symbol'] == current_positions[leg['symbol']][0]['symbol']:
            new_position = []
            if current_positions[leg['symbol']][1]['instruction'] == 'BUY':
                total = sum(position['quantity'] for position in current_positions[leg['symbol']] if position['instruction'] in ['BUY'])
                total_price = sum(position['quantity'] * position['price'] for position in current_positions[leg['symbol']] if position['instruction'] in ['BUY'])
                average_price = total_price / total
                del current_positions[leg['symbol']][1]
                current_positions[leg['symbol']][0].update({
                    'quantity': total,
                    'price': average_price
                })
            else:
                total = current_positions[leg['symbol']][0]['quantity']
            quantity = total - leg['quantity']
            new_leg = {
                'symbol': current_positions[leg['symbol']][0]['symbol'],
                'instruction': current_positions[leg['symbol']][0]['instruction'],
                'quantity': quantity,
                'price': current_positions[leg['symbol']][0]['price'],
                'time': current_positions[leg['symbol']][0]['time']
            }
            if quantity != 0:
                new_quantity = total - leg['quantity']
                current_positions[leg['symbol']][0].update({
                    'quantity': new_quantity
                })
            if current_positions[leg['symbol']][0]['quantity'] != total:
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
    importer = TdaTradeImporter('trades.json')
    positions = get_positions(importer.legs)
    position_summaries = get_position_summaries(positions)
    write_output(position_summaries)


if __name__ == '__main__':
    main()

