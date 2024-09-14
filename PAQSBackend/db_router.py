class DatabaseRouter:
    """
    A router to control all database operations on models for different databases.
    """
    
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'scylla':
            return 'scylla'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'scylla':
            return 'scylla'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'scylla' or obj2._meta.app_label == 'scylla':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'scylla':
            return db == 'scylla'
        return db == 'default'
