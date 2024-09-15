class PartitionRouter:
    def db_for_read(self, model, **hints):
        """
        Direct read operations for specific models to the 'postgresql' database.
        """
        if model._meta.model_name in ['scaninfo', 'checkoutinfo', 'logproduct']:
            return 'postgresql'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Direct write operations for specific models to the 'postgresql' database.
        """
        if model._meta.model_name in ['scaninfo', 'checkoutinfo', 'logproduct']:
            return 'postgresql'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between models in the same database.
        """
        db_list = ('default', 'postgresql')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure the models end up in the correct database.
        """
        if model_name in ['scaninfo', 'checkoutinfo', 'logproduct']:
            return db == 'postgresql'
        return db == 'default'
