from datetime import datetime, timedelta

from __init__ import create_app
from models import ResidenceParkingLot, CommercialParkingLot

if __name__ == '__main__':
    app = create_app()
    app.run()
