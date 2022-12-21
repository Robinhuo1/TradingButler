import datetime
from decimal import Decimal
from decimal import ROUND_HALF_UP

import pytest

from tradingbutler.summary import get_position_summaries
from tradingbutler.summary import get_positions

legs = [
    {
        'symbol': 'AAPL',
        'instruction': 'SELL_SHORT',
        'quantity': 16,
        'price': Decimal('29.34'),
        'time': datetime.datetime(2022, 9, 23),
        'order_id': 1
    },
    {
        'symbol': 'AAPL',
        'instruction': 'BUY_TO_COVER',
        'quantity': 16,
        'price': Decimal('23.7'),
        'time': datetime.datetime(2022, 10, 10),
        'order_id': 2
    },
    {
        'symbol': 'ATT',
        'instruction': 'BUY',
        'quantity': 6,
        'price': Decimal('81.55'),
        'time': datetime.datetime(2022, 9, 10),
        'order_id': 3
    },
    {
        "symbol": "ATT",
        'instruction': 'SELL',
        'quantity': 6,
        'price': Decimal('111.25'),
        'time': datetime.datetime(2022, 9, 20),
        'order_id': 4
    },
    {
        'symbol': 'AMZN',
        'instruction': 'BUY',
        'quantity': 12,
        'price': Decimal('75.25'),
        'time': datetime.datetime(2022, 10, 20),
        'order_id': 5
    }
]


def test_get_positions():
    positions = get_positions(legs=legs)
    assert len(positions) == 3
    assert positions[0]['opening']['symbol'] == 'AAPL'
    assert len(positions[0]) == 3
    assert positions[0]['opening']['instruction'] == 'SELL_SHORT'
    assert positions[0]['opening']['price'] == Decimal('29.34')
    assert positions[0]['closing']['instruction'] == 'BUY_TO_COVER'
    assert len(set(positions[0]['order_ids'])) == 2
    assert positions[1]['opening']['symbol'] == 'ATT'
    assert len(positions[1]) == 3
    assert positions[1]['opening']['instruction'] == 'BUY'
    assert positions[1]['opening']['price'] == Decimal('81.55')
    assert positions[1]['closing']['instruction'] == 'SELL'
    assert positions[1]['opening']['quantity'] == Decimal('6.0')
    assert positions[2]['opening']['symbol'] == 'AMZN'
    assert len(positions[2]) == 2
    assert positions[2]['opening']['instruction'] == 'BUY'
    assert positions[2]['opening']['price'] == Decimal('75.25')
    assert len(set(positions[2]['order_ids'])) == 1


def test_get_position_summaries():
    positions = get_positions(legs)
    position_summaries = get_position_summaries(positions)
    assert len(position_summaries) == 3
    assert position_summaries[0]['symbol'] == 'AAPL'
    assert position_summaries[1]['symbol'] == 'ATT'
    assert position_summaries[1]['average_price'] == Decimal('81.55')
    assert position_summaries[1]['risk'] == Decimal('489.300')
    assert position_summaries[1]['days'] == 10
    assert position_summaries[1]['profit'] == Decimal('178.2000')
    assert position_summaries[1]['profit_percentage'] == Decimal('36.42')
    assert position_summaries[1]['entry_date'] == datetime.date(2022, 9, 10)
    assert position_summaries[1]['exit_date'] == datetime.date(2022, 9, 20)
    assert position_summaries[1]['exit_price'] == Decimal('111.25')
    assert position_summaries[1]['direction'] == 'Long'
    assert position_summaries[2]['symbol'] == 'AMZN'
    assert position_summaries[2]['exit_price'] == None
    assert position_summaries[2]['exit_date'] == None
    assert position_summaries[2]['profit'] == None
    assert position_summaries[2]['profit_percentage'] == None


def test_partial_closing():
    data = [
        {
            'symbol': 'META',
            'instruction': 'BUY',
            'quantity': 10,
            'price': Decimal('241.34'),
            'time': datetime.datetime(2022, 10, 13),
            'order_id': 1
        },
        {
            'symbol': 'META',
            'instruction': 'SELL',
            'quantity': 5,
            'price': Decimal('232.11'),
            'time': datetime.datetime(2022, 10, 20),
            'order_id': 2
        },
    ]

    positions = get_positions(legs=data)
    assert len(positions) == 2
    expected = [
        {
            'closing':
                {
                    'instruction': 'SELL',
                    'price': Decimal('232.1100'),
                    'quantity': 5,
                    'symbol': 'META',
                    'time': datetime.datetime(2022, 10, 20)
                },
            'opening':
                {
                    'instruction': 'BUY',
                    'price': Decimal('241.3400'),
                    'quantity': 5,
                    'risk': Decimal('1206.7000'),
                    'symbol': 'META',
                    'time': datetime.datetime(2022, 10, 13)
                },
            'order_ids':
                [1, 1, 1, 1, 1, 2]
        },
        {
            'opening':
                {
                    'instruction': 'BUY',
                    'price': Decimal('241.3400'),
                    'quantity': 5,
                    'risk': Decimal('1206.7000'),
                    'symbol': 'META',
                    'time': datetime.datetime(2022, 10, 13)
                },
            'order_ids':
                [1, 1, 1, 1, 1]
        }
    ]
    assert positions == expected


def test_partial_closing_multiple_buys():
    data = [
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 12,
            'price': Decimal('72.01'),
            'time': datetime.datetime(2022, 9, 20),
            'order_id': 1
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 6,
            'price': Decimal('54.21'),
            'time': datetime.datetime(2022, 10, 4),
            'order_id': 2
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 4,
            'price': Decimal('50.21'),
            'time': datetime.datetime(2022, 10, 7),
            'order_id': 3
        },
        {
            'symbol': 'GE',
            'instruction': 'SELL',
            'quantity': 11,
            'price': Decimal('65.14'),
            'time': datetime.datetime(2022, 10, 17),
            'order_id': 4
        }
    ]
    positions = get_positions(legs=data)
    assert len(positions) == 2
    expected = [
        {
            'closing':
                {
                    'instruction': 'SELL',
                    'price': Decimal('65.14'),
                    'quantity': 11,
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 17)
                },
            'opening':
                {
                    'instruction': 'BUY',
                    'price': Decimal('72.0100'),
                    'quantity': 11,
                    'risk': Decimal('792.1100'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 20)
                },
            'order_ids':
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4]
        },
        {
            'opening':
                {
                    'instruction': 'BUY',
                    'price': ((1 * Decimal('72.01') + 6 * Decimal('54.21') + 4 * Decimal('50.21')) / 11).quantize(Decimal('.0001'), ROUND_HALF_UP),
                    'quantity': 11,
                    'risk': Decimal('598.1100'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 20)
                },
            'order_ids':
                [1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3]
        }
    ]
    assert positions == expected


def test_only_buy():
    data = [
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 12,
            'price': Decimal('72.01'),
            'time': datetime.datetime(2022, 9, 20),
            'order_id': 1
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 6,
            'price': Decimal('54.21'),
            'time': datetime.datetime(2022, 10, 4),
            'order_id': 2
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 4,
            'price': Decimal('50.21'),
            'time': datetime.datetime(2022, 10, 7),
            'order_id': 3
        },
    ]
    positions = get_positions(legs=data)
    assert len(positions) == 1
    expected = [
        {
            'opening':
                {
                    'instruction': 'BUY',
                    'price': ((12 * Decimal('72.01') + 6 * Decimal('54.21') + 4 * Decimal('50.21')) / 22).quantize(Decimal('.0001'), ROUND_HALF_UP),
                    'quantity': 22,
                    'risk': Decimal('1390.2200'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 20)
                },
            'order_ids':
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3]
        }
    ]
    assert positions == expected


def test_partial_closing_multiple_sells():
    data = [
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 12,
            'price': Decimal('72.01'),
            'time': datetime.datetime(2022, 9, 20),
            'order_id': 1
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 6,
            'price': Decimal('54.21'),
            'time': datetime.datetime(2022, 10, 4),
            'order_id': 2
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 4,
            'price': Decimal('50.21'),
            'time': datetime.datetime(2022, 10, 7),
            'order_id': 3
        },
        {
            'symbol': 'GE',
            'instruction': 'SELL',
            'quantity': 11,
            'price': Decimal('65.14'),
            'time': datetime.datetime(2022, 10, 17),
            'order_id': 4
        },
        {
            'symbol': 'GE',
            'instruction': 'SELL',
            'quantity': 5,
            'price': Decimal('69.33'),
            'time': datetime.datetime(2022, 10, 21),
            'order_id': 5
        },
        {
            'symbol': 'GE',
            'instruction': 'SELL',
            'quantity': 4,
            'price': Decimal('70.55'),
            'time': datetime.datetime(2022, 10, 26),
            'order_id': 6
        }
    ]

    positions = get_positions(legs=data)
    assert len(positions) == 4
    expected = [
        {
            'closing':
                {
                    'instruction': 'SELL',
                    'price': Decimal('65.14'),
                    'quantity': 11,
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 17)
                },
            'opening':
                {
                    'instruction': 'BUY',
                    'price': Decimal('72.0100'),
                    'quantity': 11,
                    'risk': Decimal('792.1100'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 20)
                },
            'order_ids':
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4]
        },
        {
            'closing':
                {
                    'instruction': 'SELL',
                    'price': Decimal('69.33'),
                    'quantity': 5,
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 21)
                },
            'opening':
                {
                    'instruction': 'BUY',
                    'price': ((1 * Decimal('72.01') + 4 * Decimal('54.21')) / 5).quantize(Decimal('.0001'), ROUND_HALF_UP),
                    'quantity': 5,
                    'risk': Decimal('288.8500'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 20)
                },
            'order_ids':
                [1, 2, 2, 2, 2, 5]
        },
        {
            'closing':
                {
                    'instruction': 'SELL',
                    'price': Decimal('70.55'),
                    'quantity': 4,
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 26)
                },
            'opening':
                {
                    'instruction': 'BUY',
                    'price': ((2 * Decimal('54.21') + 2 * Decimal('50.21')) / 4).quantize(Decimal('.0001'), ROUND_HALF_UP),
                    'quantity': 4,
                    'risk': Decimal('208.8400'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 4)
                },
            'order_ids':
                [2, 2, 3, 3, 6]
        },
        {
            'opening':
                {
                    'instruction': 'BUY',
                    'price': Decimal('50.2100'),
                    'quantity': 2,
                    'risk': Decimal('100.4200'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 7)
                },
            'order_ids':
                [3, 3]
        }
    ]
    assert positions == expected


def test_sell_short_fully_closed():
    data = [
        {
            'symbol': 'GE',
            'instruction': 'SELL_SHORT',
            'quantity': 12,
            'price': Decimal('72.01'),
            'time': datetime.datetime(2022, 9, 20),
            'order_id': 1
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY_TO_COVER',
            'quantity': 12,
            'price': Decimal('54.21'),
            'time': datetime.datetime(2022, 10, 4),
            'order_id': 2
        },
    ]
    positions = get_positions(legs=data)
    assert len(positions) == 1
    expected = [
        {
            'closing':
                {
                    'instruction': 'BUY_TO_COVER',
                    'price': Decimal('54.21'),
                    'quantity': 12,
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 4)
                },
            'opening':
                {
                    'instruction': 'SELL_SHORT',
                    'price': Decimal('72.0100'),
                    'quantity': 12,
                    'risk': Decimal('864.1200'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 20)
                },
            'order_ids':
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2]
        },
    ]
    assert positions == expected


def test_partial_closing_sell_short_multiple_positions():
    data = [
        {
            'symbol': 'GE',
            'instruction': 'SELL_SHORT',
            'quantity': 7,
            'price': Decimal('72.01'),
            'time': datetime.datetime(2022, 9, 20),
            'order_id': 1
        },
        {
            'symbol': 'GE',
            'instruction': 'SELL_SHORT',
            'quantity': 8,
            'price': Decimal('77.22'),
            'time': datetime.datetime(2022, 9, 28),
            'order_id': 2
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY_TO_COVER',
            'quantity': 10,
            'price': Decimal('54.21'),
            'time': datetime.datetime(2022, 10, 4),
            'order_id': 3
        },
        {
            'symbol': 'GE',
            'instruction': 'BUY_TO_COVER',
            'quantity': 3,
            'price': Decimal('60.33'),
            'time': datetime.datetime(2022, 10, 8),
            'order_id': 4
        },
    ]
    positions = get_positions(legs=data)
    assert len(positions) == 3
    expected = [
        {
            'closing':
                {
                    'instruction': 'BUY_TO_COVER',
                    'price': Decimal('54.21'),
                    'quantity': 10,
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 4)
                },
            'opening':
                {
                    'instruction': 'SELL_SHORT',
                    'price': ((7 * Decimal('72.01') + 3 * Decimal('77.22')) / 10).quantize(Decimal('.0001'), ROUND_HALF_UP),
                    'quantity': 10,
                    'risk': Decimal('735.7300'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 20)
                },
            'order_ids':
                [1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3]
        },
        {
            'closing':
                {
                    'instruction': 'BUY_TO_COVER',
                    'price': Decimal('60.33'),
                    'quantity': 3,
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 10, 8)
                },
            'opening':
                {
                    'instruction': 'SELL_SHORT',
                    'price': Decimal('77.2200'),
                    'quantity': 3,
                    'risk': Decimal('231.6600'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 28)
                },
            'order_ids':
                [2, 2, 2, 4]
        },
        {
            'opening':
                {
                    'instruction': 'SELL_SHORT',
                    'price': Decimal('77.2200'),
                    'quantity': 2,
                    'risk': Decimal('154.4400'),
                    'symbol': 'GE',
                    'time': datetime.datetime(2022, 9, 28)
                },
            'order_ids':
                [2, 2]
        }
    ]
    assert positions == expected


def test_closing_more_shares_than_open_fails():
    data = [
        {
            'symbol': 'GE',
            'instruction': 'BUY',
            'quantity': 5,
            'price': Decimal('72.01'),
            'time': datetime.datetime(2022, 9, 20),
            'order_id': 1
        },
        {
            'symbol': 'GE',
            'instruction': 'SELL',
            'quantity': 10,
            'price': Decimal('54.21'),
            'time': datetime.datetime(2022, 10, 4),
            'order_id': 2
        },
    ]
    with pytest.raises(ValueError) as excinfo:
        get_positions(legs=data)
    assert excinfo.value.args[0] == 'closing more shares than open'
