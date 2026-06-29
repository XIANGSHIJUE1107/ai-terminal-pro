import sys, os
sys.path.insert(0, '.')
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

print("Initializing database...")
from stock_platform.data.database import init_db
init_db()

print("Fetching data...")
from stock_platform.data.fetcher import run_daily_update
run_daily_update()

print("Computing indicators...")
from stock_platform.indicator.calculator import batch_update
batch_update()

print("Scanning signals...")
from stock_platform.signal.detector import scan_all
scan_all()

print("Running predictions...")
from stock_platform.prediction.engine import run_predictions
run_predictions()

print("Verifying...")
from stock_platform.prediction.verify import verify_expired_predictions, print_win_rate
verify_expired_predictions()
print_win_rate()

print("All done!")