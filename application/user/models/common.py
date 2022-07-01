from datetime import datetime
from email.policy import default
from enum import unique
import peewee
from ..database.database import db

class User(peewee.Model):
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
    class Meta:
        database = db
    
class ResetPasswordToken(peewee.Model):
    owner = peewee.ForeignKeyField(User, on_delete="CASCADE")
    token = peewee.CharField(index=True)
    createdAt = peewee.DateTimeField(default=datetime.now())
    isExpire = peewee.BooleanField(default=False)

    class Meta:
        database = db

class MailConfig(peewee.Model):
    username= peewee.CharField()
    password= peewee.CharField()
    fromEmail = peewee.CharField()
    port= peewee.IntegerField()
    server= peewee.CharField()
    tls= peewee.BooleanField()
    ssl= peewee.BooleanField()
    use_credentials = peewee.BooleanField()
    validate_certs = peewee.BooleanField()
    class Meta:
        database = db

class DatabaseConfig(peewee.Model):
    DBName = peewee.CharField(),
    username = peewee.CharField()
    password = peewee.CharField()
    host = peewee.CharField()
    port = peewee.IntegerField()

    class Meta:
        database = db