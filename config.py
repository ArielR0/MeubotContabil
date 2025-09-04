import os
from dotenv import load_dotenv

#---TOKEN BOT-----
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

#---DATA BASE-----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")