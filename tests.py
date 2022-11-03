import datetime
from decimal import Decimal, ROUND_HALF_UP

from summary import get_positions, get_position_summaries

fake_data = [{
    "symbol": "AAPL",
    "instruction": "BUY",
    "quantity": Decimal(16.0).quantize(Decimal('.01'), ROUND_HALF_UP),
    "price": Decimal(29.34).quantize(Decimal('.01'), ROUND_HALF_UP),
    "time": datetime.datetime(2022, 9, 23)
    },

    {
        "symbol": "AAPL",
        'instruction': 'SELL',
        'quantity': Decimal(16.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        'price': Decimal(222.22).quantize(Decimal('.01'), ROUND_HALF_UP),
        'time': datetime.datetime(2022, 10, 10)
    },

    {
        "symbol": "ATT",
        'instruction': 'BUY',
        'quantity': Decimal(6.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        'price': Decimal(81.55).quantize(Decimal('.01'), ROUND_HALF_UP),
        'time': datetime.datetime(2022, 9, 10)
    },

    {
        "symbol": "ATT",
        'instruction': 'SELL',
        'quantity': Decimal(6.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        'price': Decimal(111.25).quantize(Decimal('.01'), ROUND_HALF_UP),
        'time': datetime.datetime(2022, 9, 20)
    },

    {
        "symbol": "AMZN",
        'instruction': 'BUY',
        'quantity': Decimal(12.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        'price': Decimal(75.25).quantize(Decimal('.01'), ROUND_HALF_UP),
        'time': datetime.datetime(2022, 10, 20)
    }
]


def test_get_positions():
    positions = get_positions(legs=fake_data)
    assert len(positions) == 3
    assert positions[0][0]['symbol'] == 'AAPL'
    assert len(positions[0]) == 2
    assert positions[0][0]['instruction'] == 'BUY'
    assert positions[0][0]['price'] == Decimal('29.34')
    assert positions[0][1]['instruction'] == 'SELL'
    assert positions[1][0]['symbol'] == 'ATT'
    assert len(positions[1]) == 2
    assert positions[1][0]['instruction'] == 'BUY'
    assert positions[1][0]['price'] == Decimal('81.55')
    assert positions[1][1]['instruction'] == 'SELL'
    assert positions[1][0]['quantity'] == Decimal('6.0')
    assert positions[2][0]['symbol'] == 'AMZN'
    assert len(positions[2]) == 1
    assert positions[2][0]['instruction'] == 'BUY'
    assert positions[2][0]['price'] == Decimal('75.25')


def test_get_position_summaries():
    positions = get_positions(fake_data)
    position_summaries = get_position_summaries(positions)
    assert len(position_summaries) == 3
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
    partial_closing_trade = [{
        "symbol": "META",
        "instruction": "BUY",
        "quantity": Decimal(10.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        "price": Decimal(241.34).quantize(Decimal('.01'), ROUND_HALF_UP),
        "time": datetime.datetime(2022, 10, 13)
         },

        {
            "symbol": "META",
            'instruction': 'SELL',
            'quantity': Decimal(5.0).quantize(Decimal('.01'), ROUND_HALF_UP),
            'price': Decimal(232.11).quantize(Decimal('.01'), ROUND_HALF_UP),
            'time': datetime.datetime(2022, 10, 20)
        },
        # {
        #     "symbol": "GE",
        #     'instruction': 'BUY',
        #     'quantity': Decimal(18.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        #     'price': Decimal(72.01).quantize(Decimal('.01'), ROUND_HALF_UP),
        #     'time': datetime.datetime(2022, 9, 20)
        # },
        #
        # {
        #     "symbol": "GE",
        #     'instruction': 'SELL',
        #     'quantity': Decimal(6.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        #     'price': Decimal(54.21).quantize(Decimal('.01'), ROUND_HALF_UP),
        #     'time': datetime.datetime(2022, 10, 4)
        # },
        #
        # {
        #     "symbol": "GE",
        #     'instruction': 'SELL',
        #     'quantity': Decimal(12.0).quantize(Decimal('.01'), ROUND_HALF_UP),
        #     'price': Decimal(65.14).quantize(Decimal('.01'), ROUND_HALF_UP),
        #     'time': datetime.datetime(2022, 10, 17)
        # }
    ]

    positions = get_positions(legs=partial_closing_trade)
    assert len(positions) == 2
    expected = [
        [
            {
                "symbol": "META",
                "instruction": "BUY",
                "quantity": Decimal(5.0).quantize(Decimal('.01'), ROUND_HALF_UP),
                "price": Decimal(241.34).quantize(Decimal('.01'), ROUND_HALF_UP),
                "time": datetime.datetime(2022, 10, 13)
            },
            {
                "symbol": "META",
                "instruction": "SELL",
                "quantity": Decimal(5.0).quantize(Decimal('.01'), ROUND_HALF_UP),
                "price": Decimal(232.11).quantize(Decimal('.01'), ROUND_HALF_UP),
                "time": datetime.datetime(2022, 10, 20)
            },
        ],
        [
            {
                "symbol": "META",
                "instruction": "BUY",
                "quantity": Decimal(5.0).quantize(Decimal('.01'), ROUND_HALF_UP),
                "price": Decimal(241.34).quantize(Decimal('.01'), ROUND_HALF_UP),
                "time": datetime.datetime(2022, 10, 13)
            }
        ]
    ]
    assert positions == expected
