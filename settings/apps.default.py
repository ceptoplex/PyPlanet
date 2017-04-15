"""
This file contains the apps & apps settings and overrides the default ones that are defined in the core.
Please copy the default file to: apps.py
"""

# In the apps dictionary and array you configure the apps (or plugins) are loaded for specific pools (controllers).
# Be aware that the list will *ALWAYS* be prepended after the mandatory defaults are loaded in place.
# The mandatory defaults are specific per version, refer to the documentation:
# TODO: Link to documentation.
APPS = {
	'default': [
		'pyplanet.apps.contrib.local_records.app.LocalRecordsConfig'
	]
}
