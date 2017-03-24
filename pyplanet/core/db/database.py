"""
The database class in this file holds the engine and state of the database connection. Each instance has one specific
database instance running.
"""
import importlib
import logging
import peewee

from pyplanet.core.exceptions import ImproperlyConfigured
from .registry import Registry
from .migrator import Migrator

Proxy = peewee.Proxy()


class Database:
	def __init__(self, engine_cls, instance, *args, **kwargs):
		"""
		Initiate database.
		:param engine_cls: Engine class
		:param instance: Instance of the app.
		:param args: *
		:param kwargs: **
		:type instance: pyplanet.core.instance.Instance
		"""
		self.engine = engine_cls(*args, **kwargs)
		self.instance = instance
		self.migrator = Migrator(self)
		self.registry = Registry(self)
		Proxy.initialize(self.engine)

	@classmethod
	def create_from_settings(cls, instance, conf):
		try:
			engine_path, _, cls_name = conf['ENGINE'].rpartition('.')
			db_name = conf['NAME']
			db_options = conf['OPTIONS'] if 'OPTIONS' in conf and conf['OPTIONS'] else dict()

			# We will try to load it so we have the validation inside this class.
			engine = getattr(importlib.import_module(engine_path), cls_name)
		except ImportError:
			raise ImproperlyConfigured('Database engine doesn\'t exist!')
		except Exception as e:
			raise ImproperlyConfigured('Database configuration isn\'t complete or engine could\'t be found!')

		return cls(engine, instance, db_name, **db_options)

	def connect(self):
		self.engine.connect()
		logging.info('Database connection established!')

	def initiate(self):
		# Create the migration table.
		from .models import migration
		migration.Migration.create_table(True)

		# Migrate all models.
		self.migrator.migrate()