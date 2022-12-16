# coding=utf-8
"""Schema transformations API feature tests."""

__copyright__ = 'Copyright (c) 2022, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import os

from pytest_bdd import (
    given,
    parsers,
    scenarios,
    then
)

from conftest import api_request, upload_data

scenarios('../../features/api/api_schema_transformations.feature')


@given(parsers.parse("a metadata file with schema {schema_from} is uploaded to folder with schema {schema_to}"), target_fixture="api_response")
def api_upload_transform_metadata_json(user, schema_from, schema_to):
    # toegevoegd /tempZone/home
    api_request(
        user,
        "research_file_delete",
        {"coll": "/tempZone/home/research-{}".format(schema_to), "file_name": "yoda-metadata.json"}
    )

    cwd = os.getcwd()
    # toegevoegd mode='rb'
    with open("{}/files/transformations/{}_{}.json".format(cwd, schema_from, schema_to), mode='rb') as f:
        metadata = f.read()

    return upload_data(
        user,
        "yoda-metadata.json",
        "/research-{}".format(schema_to),
        metadata
    )


@then(parsers.parse("transformation of metadata is successful for collection {schema_to} and {keep} backup of original metadata"), target_fixture="api_response")
def api_transform_metadata(user, schema_to, keep):
    collection = '/tempZone/home/research-{}'.format(schema_to)
    keep_metadata_backup = (keep=='keep')

    return api_request(
        user,
        "transform_metadata",
        {"coll": collection,
		 "keep_metadata_backup": keep_metadata_backup}
    )

@then(parsers.parse("number of files in collection {schema_to} is {count}"), target_fixture="api_response")
def api_upload_transform_metadata_file_count(user, schema_to, count):
    collection = '/tempZone/home/research-{}'.format(schema_to)

    _, body = api_request(
        user,
        "browse_folder",
        {"coll": collection}
    )
    assert len(body['data']['items']) == int(count)
	