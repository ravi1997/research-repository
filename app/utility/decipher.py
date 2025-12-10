from functools import reduce
import hashlib


def hash_salt(salt: str) -> str:
	# Encode the salt and generate SHA-256 hash
	hash_object = hashlib.sha256(salt.encode('UTF-8'))
	# Convert to hexadecimal format
	return hash_object.hexdigest()

def decipher(salt: str):
	# Get the hashed salt
	hashed_salt = hash_salt(salt)
	
	# Function to convert text to char codes
	def text_to_chars(text):
		return [ord(c) for c in text]
	
	# Apply the hashed salt to the character code
	def apply_salt_to_char(code):
		# Reduce the XOR operation across all characters in the hashed salt
		return reduce(lambda a, b: a ^ b, text_to_chars(hashed_salt), code)
	
	# The main decode function
	def decode(encoded: str) -> str:
		# Split the encoded string into hex pairs and convert to integers
		chars = [int(encoded[i:i+2], 16) for i in range(0, len(encoded), 2)]
		# Apply salt to each char code and convert back to characters
		decoded_chars = [chr(apply_salt_to_char(char_code)) for char_code in chars]
		return ''.join(decoded_chars)
	
	return decode



def decode_text(salt: str, encoded: str) -> str:
	decode_function = decipher(salt)
	return decode_function(encoded)