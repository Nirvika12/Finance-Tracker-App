from dotenv import load_dotenv
import os 

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY_TOKEN")
ALGORITHM = int(os.getenv("ALGORITHM"))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))