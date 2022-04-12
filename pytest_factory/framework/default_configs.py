# these variable names MUST match the config.ini keys in order for the config.ini values to override these defaults!
# TODO set up a test for default config value types:
#   NONE - means setting is supported by framework but is optional
#   Exception - means setting is required by framework but be given value by user

assert_no_missing_calls = False
assert_no_extra_calls = False
http_req_wildcard_fields = {"query"}
