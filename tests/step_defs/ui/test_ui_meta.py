# coding=utf-8
"""Meta UI feature tests."""

__copyright__ = 'Copyright (c) 2020-2022, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

from pytest_bdd import (
    scenarios,
    then,
    when,
)

scenarios('../../features/ui/ui_meta.feature')


@when('user opens metadata form')
def ui_metadata_open(browser):
    browser.find_by_css('button.metadata-form').click()


@when('users fills in metadata form')
def ui_metadata_fill(browser):
    for input in browser.find_by_css('input.is-invalid'):
        if input.visible:
            input.fill('The quick brown fox jumps over the lazy dog')


@when('users clicks save button')
def ui_metadata_save(browser):
    browser.find_by_css('.yodaButtons .btn-primary').click()


@when('users clicks delete all metadata button')
def ui_metadata_delete(browser):
    browser.find_by_css('.yodaButtons .btn-danger').click()
    browser.find_by_css('.confirm').click()


@then('metadata form is saved as yoda-metadata.json')
def ui_metadata_saved(browser):
    assert browser.is_text_present("Updated metadata of folder </research-initial>")


@then('metadata is deleted from folder')
def ui_metadata_deleted(browser):
    browser.is_text_present("Deleted metadata of folder </research-initial>", wait_time=3)
