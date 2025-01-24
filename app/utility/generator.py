from datetime import datetime, timedelta
import random
import string

def generate_otp(length=6):
	"""Generate a random OTP of specified length."""
	digits = '0123456789'
	otp = ''.join(random.choice(digits) for _ in range(length))
	return otp

def randomword(length):
	letters = 'abcdefghijklmnopqrstuvwxyz'
	return ''.join(random.choice(letters) for i in range(length))

def generate_random_phone_number():
	# Generate a random 10-digit number (excluding any specific formatting)
	number = ''.join(random.choices('0123456789', k=10))
	
	# Format the number as a typical phone number (e.g., ###-###-####)
	formatted_number = f'{number[:3]}-{number[3:6]}-{number[6:]}'
	
	return formatted_number

def generate_random_dob(start_date='1970-01-01', end_date='2005-12-31'):
	# Convert start_date and end_date to datetime objects
	start_date = datetime.strptime(start_date, '%Y-%m-%d')
	end_date = datetime.strptime(end_date, '%Y-%m-%d')
	
	# Calculate the range in days
	delta = end_date - start_date
	random_days = random.randint(0, delta.days)
	
	# Generate a random date within the specified range
	random_dob = start_date + timedelta(days=random_days)
	
	return random_dob.date()

def generate_strong_password(length=10):
	# Define characters to use in the password
	characters = string.ascii_letters + string.digits + string.punctuation
	
	# Generate password
	password = ''.join(random.choice(characters) for _ in range(length))
	
	return password
