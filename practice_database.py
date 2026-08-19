from database_manager import create_database, save_price

create_database()

save_price("AAPL", "2026-08-05 09:30:00", 210.50)
save_price("MSFT", "2026-08-05 09:30:00", 418.25)

# TODO: Add two more fake records.

save_price("GOOGL", "2026-08-05 09:30:00", 135.75)
save_price("AMZN", "2026-08-05 09:30:00", 98.40)

print("Practice prices saved.")
