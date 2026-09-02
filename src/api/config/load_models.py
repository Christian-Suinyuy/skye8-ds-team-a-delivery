from api.config.database import engine, Base
from api.config.models.user import User

def load_models():
    """Function used to load all models into  tables into database"""
    Base.metadata.create_all(bind=engine)