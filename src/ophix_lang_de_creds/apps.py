from django.apps import AppConfig


class OphixLangDeCredsConfig(AppConfig):
    name = "ophix_lang_de_creds"
    verbose_name = "Ophix German — Credentials"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_import_docs, sender=self)


def _import_docs(sender, **kwargs):
    try:
        from django.core.management import call_command
        call_command(
            "ophix_docs_update",
            include_app_docs="ophix_lang_de_creds",
            language="de",
            verbosity=0,
        )
    except Exception:
        pass
