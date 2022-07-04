from datetime import datetime
import peewee

from ..database.database import db

class BaseModel(peewee.Model):
    class Meta: 
        database = db

class User(BaseModel):
    firstName = peewee.CharField(max_length=80)
    lastName = peewee.CharField(max_length=80)
    email = peewee.CharField(unique=True, index=True)
    password = peewee.CharField()
    changedPassword = peewee.CharField()
    changedEmail = peewee.CharField()
    upline = peewee.CharField()
    downline = peewee.CharField()
    tree = peewee.CharField()
    kyc = peewee.BooleanField()
    product = peewee.CharField()
    marketingCampaign = peewee.CharField()
    isActive = peewee.BooleanField(default=True)
    role = peewee.IntegerField()
    createdAt = peewee.DateTimeField(default=datetime.now())
    
class ResetPasswordToken(BaseModel):
    owner = peewee.ForeignKeyField(User, on_delete="CASCADE")
    token = peewee.CharField(index=True)
    createdAt = peewee.DateTimeField(default=datetime.now())
    isExpire = peewee.BooleanField(default=False)

class MailConfig(BaseModel):
    username= peewee.CharField()
    password= peewee.CharField()
    fromEmail = peewee.CharField()
    port= peewee.IntegerField()
    server= peewee.CharField()
    tls= peewee.BooleanField()
    ssl= peewee.BooleanField()
    use_credentials = peewee.BooleanField()
    validate_certs = peewee.BooleanField()

class DatabaseConfig(BaseModel):
    DBName = peewee.CharField(),
    username = peewee.CharField()
    password = peewee.CharField()
    host = peewee.CharField()
    port = peewee.IntegerField()

class TokenBlocklist(BaseModel):
    token = peewee.CharField()
    inserted_at = peewee.DateTimeField(default=datetime.now())