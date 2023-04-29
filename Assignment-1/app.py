from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

parking_lots = {}
previous_ticket_id = 0


def calculate_charge(entry_time):
    # calculate difference between entry and exit time in minutes
    diff_minutes = int((datetime.now() - entry_time).total_seconds() / 60)
    # round up to the nearest 15 minutes
    rounded_minutes = int((diff_minutes + 14) / 15) * 15
    # calculate charge based on hourly rate of $10
    charge = rounded_minutes / 60 * 10
    return charge


@app.route('/entry', methods=['POST'])
def entry():
    plate = request.args.get('plate')
    parking_lot = request.args.get('parkingLot')
    entry_time = datetime.now()

    global previous_ticket_id
    ticket_id = previous_ticket_id
    previous_ticket_id += 1

    # if parking lot doesn't already exist add it
    if parking_lot not in parking_lots:
        parking_lots[parking_lot] = []
    # add new value to parking lot
    parking_lots[parking_lot].append({'plate': plate, 'entry_time': entry_time, 'ticket_id': ticket_id})

    return {
        'ticketId': ticket_id
    }


@app.route('/exit', methods=['POST'])
def exit():
    ticket_id = int(request.args.get('ticketId'))
    for parking_lot, entries in parking_lots.items():
        for entry in entries:
            if ticket_id == entry['ticket_id']:
                charge = calculate_charge(entry['entry_time'])
                time_parked_minutes = int((datetime.now() - entry['entry_time']).total_seconds() / 60)
                return {
                    'plate': entry['plate'],
                    'parkingLot': parking_lot,
                    'time_parked_minutes': time_parked_minutes,
                    'charge': charge
                }


if __name__ == '__main__':
    app.run()
