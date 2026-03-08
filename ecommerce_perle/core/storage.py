from whitenoise.storage import CompressedManifestStaticFilesStorage


class PerleStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False
