# encoding: utf-8
#
# Copyright (c) 2016 Rob Walton <dhttps://github.com/robwalton>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-04-17
#


"""
These tests assume Ulysses has an icloud library entry.


The MANUALLY_CONFIGURED_TOKEN setting in this module must be configured with
a valid key. To find this, re-nable the test_authorize() tests below and
look for the key in the Exception it throws (after Ulysses has popped up
a dialogue asking if the app should be authorised.)

Many tests look for a group called '/ulysses-python-client-playground' at the
top level of the Ulysses library in which to build and remove content.
"""


import pytest
import logging
import random
import string
import time
import os.path

from ulysses import calls
import ulysses.xcallback

logger = logging.getLogger(__name__)


# Only valid for a particular local Ulysses install
MANUALLY_CONFIGURED_TOKEN = 'c6e4ef1a29e44e62acdcee4e5eabc423'


PLAYGROUND_NAME = 'ulysses-python-client-playground'


TEST_STRING = ur""" -- () ? & ' " ‘quoted text’ _x_y_z_ a://b.c/d?e=f&g=h"""


# pyunit fixture and helpers

def setup_module(module):
    ulysses.xcallback.set_access_token(MANUALLY_CONFIGURED_TOKEN)


@pytest.fixture(scope='module')
def playground_id():
    """Return id of pre-existing playground group."""

    icloud_grp = calls.get_root_items(recursive=False)[0]
    assert icloud_grp.title == 'iCloud'
    icloud_grp = calls.get_item(icloud_grp.identifier, True)
    return icloud_grp.get_group_by_title(PLAYGROUND_NAME).identifier


@pytest.fixture(scope='module')
def testgroup_id(playground_id):
    """Return if of group for this tests run and destroy on completion"""

    group_name = randomword(8)
    print "Create a group in playground:", group_name
    identifier = calls.new_group(group_name, playground_id)
    yield identifier

    print 'Trash the group made in playground:', group_name
    calls.trash(identifier)


def group(identifier):
    return calls.get_item(identifier, recursive=True)


# Test up calls

def test_get_version():
    assert calls.get_version() >= 2


@pytest.mark.skip(reason='re-enable to see a valid token and then put this'
                  ' in MANUALLY_CONFIGURED_TOKEN')
def test_authorize():
    # Raise exception with token (just to help determine it!
    raise Exception('authorisation token: ' + calls.authorize())


def test_get_root_items__non_recursive():
    items = calls.get_root_items(recursive=False)

    assert len(items) >= 1
    assert items[0].title == 'iCloud'
    assert isinstance(items[0], calls.Group)


def test_get_root_items__recursive():
    groups = calls.get_root_items(recursive=True)
    icloud_grp = groups[0]

    assert icloud_grp.title == 'iCloud'


def test_get_root_items_with_wrong_access_token():
    original_token = ulysses.xcallback.token_provider.token
    try:
        ulysses.xcallback.token_provider.token = 'not_the_right_token'
        with pytest.raises(calls.UlyssesError) as excinfo:
            calls.get_root_items()
        assert 'Access denied. Code=4' in str(excinfo.value)
    finally:
        ulysses.xcallback.token_provider.token = original_token


@pytest.mark.skip(reason='Takes 20s to fail for some reason')
def test_get_item_fails():
    identifier = 'x' * 22
    with pytest.raises(calls.UlyssesError):
        calls.get_item(identifier)


def test_check_playground_exists(playground_id):
    item = calls.get_item(playground_id, recursive=False)
    assert item.type == 'group'
    assert item.title == PLAYGROUND_NAME


def test_new_group(testgroup_id):
    name = 'test_new_group' + TEST_STRING
    identifier = calls.new_group(name, testgroup_id)

    assert calls.get_item(identifier, False).title == name


def test_trash(testgroup_id):
    identifier = calls.new_group('test_trash', testgroup_id)
    group(testgroup_id).get_group_by_title('test_trash')

    calls.trash(identifier)

    with pytest.raises(KeyError):
        group(testgroup_id).get_group_by_title('test_trash')


def test_set_group_title(testgroup_id):
    name = 'test_set_group_title'
    identifier = calls.new_group(name, testgroup_id)

    calls.set_group_title(identifier, name + TEST_STRING)

    group = calls.get_item(identifier, False)
    assert group.title == name + TEST_STRING


def test_set_sheet_title_with(testgroup_id):
    title = 'tests-set-sheet-title'
    identifier = calls.new_sheet(title, testgroup_id)
    new_title = title + TEST_STRING.replace('_', '')

    calls.set_sheet_title(identifier, new_title, 'heading2')

    sheet = calls.get_item(identifier)
    assert sheet.title == new_title
    assert sheet.titleType == 'heading2'


@pytest.mark.skip('Ulysses seems to ignore underscores when setting')
def test_set_sheet_title_with_underscores(testgroup_id):
    title = 'tests-set-sheet-title'
    identifier = calls.new_sheet(title, testgroup_id)
    new_title = title + TEST_STRING

    calls.set_sheet_title(identifier, new_title, 'heading2')

    sheet = calls.get_item(identifier)
    assert sheet.title == new_title
    assert sheet.titleType == 'heading2'


def test_move__to_group(testgroup_id):
    sheetid = calls.new_sheet('test_move__to_group-sheet', testgroup_id)
    groupid = calls.new_group('test_move__to_group-group', testgroup_id)

    calls.move(sheetid, groupid)

    group(groupid).get_sheet_by_title('test_move__to_group-sheet')


def test_move__to_index(testgroup_id):
    group_id = calls.new_group('test_move__to_index-group', testgroup_id)
    sheet1_id = calls.new_sheet('sheet1', group_id)
    calls.new_sheet('sheet2', group_id)
    group_ = group(group_id)
    assert group_.sheets[0].title == 'sheet2'
    assert group_.sheets[1].title == 'sheet1'

    calls.move(sheet1_id, index=0, silent_mode=True)

    group_ = group(group_id)
    assert group_.sheets[0].title == 'sheet1'
    assert group_.sheets[1].title == 'sheet2'


def test_copy__to_index(testgroup_id):
    group_id = calls.new_group('test_copy__to_index-group', testgroup_id)
    sheet1_id = calls.new_sheet('sheet0', group_id)
    calls.new_sheet('sheet2', group_id)
    calls.new_sheet('sheet1', group_id)

    calls.copy(sheet1_id, group_id, 1, silent_mode=True)

    group_ = group(group_id)
    assert group_.sheets[0].title == 'sheet1'
    assert group_.sheets[1].title == 'sheet0'
    assert group_.sheets[2].title == 'sheet2'


def test_get_quick_look_url__with_sheet(testgroup_id):
    sht_id = calls.new_sheet(
        'test_get_quick_look_url__with_sheet', testgroup_id)

    path = calls.get_quick_look_url(sht_id)

    assert os.path.exists(path)


def test_read_sheet(testgroup_id):
    text = '## tests read sheet\nfirst line\n' + TEST_STRING
    sht_id = calls.new_sheet(text, testgroup_id)

    sheet = calls.read_sheet(sht_id, text=True)

    assert sheet.title == 'tests read sheet'
    assert sheet.titleType == 'heading2'

    assert sheet.text == text
    assert sheet.keywords == []
    assert sheet.notes == []


def test_insert(testgroup_id):
    sht_id = calls.new_sheet('tests insert\nline1')

    calls.insert(sht_id, 'line2' + TEST_STRING, newline='prepend')

    sheet = calls.read_sheet(sht_id, text=True)

    assert sheet.title == 'tests insert'
    assert sheet.text == 'tests insert\nline1\nline2' + TEST_STRING


def test_attach_keywords(testgroup_id):
    sht_id = calls.new_sheet('test_attach_keywords', testgroup_id)

    calls.attach_keywords(sht_id, ['keyword1'])
    calls.attach_keywords(sht_id, ['keyword2', 'keyword3' + TEST_STRING])

    sheet = calls.read_sheet(sht_id)
    assert sheet.keywords == ['keyword1', 'keyword2', 'keyword3' + TEST_STRING]


def test_remove_keywords(testgroup_id):
    sht_id = calls.new_sheet('test_attach_keywords', testgroup_id)
    calls.attach_keywords(sht_id, ['keyword1', 'keyword2', 'keyword3'])

    calls.remove_keywords(sht_id, ['keyword1', 'keyword3'])

    sheet = calls.read_sheet(sht_id)
    assert sheet.keywords == ['keyword2']


def test_attach_note(testgroup_id):
    sht_id = calls.new_sheet('test_attach_note', testgroup_id)

    calls.attach_note(sht_id, TEST_STRING)

    sheet = calls.read_sheet(sht_id)
    assert sheet.notes == [TEST_STRING]


def test_update_note(testgroup_id):
    sht_id = calls.new_sheet('test_update_note', testgroup_id)
    calls.attach_note(sht_id, 'note0')
    calls.attach_note(sht_id, 'note1')

    calls.update_note(sht_id, 1, 'note1' + TEST_STRING)

    sheet = calls.read_sheet(sht_id)
    assert sheet.notes == ['note0', 'note1' + TEST_STRING]


def test_remove_note(testgroup_id):
    sht_id = calls.new_sheet('test_remove_note', testgroup_id)
    calls.attach_note(sht_id, 'note0')
    calls.attach_note(sht_id, 'note1')

    calls.remove_note(sht_id, 0)

    sheet = calls.read_sheet(sht_id)
    assert sheet.notes == ['note1']


@pytest.mark.skip('visual check')
def test__open__open_all__open_recent__open_favorites(testgroup_id):

    sheet_id = calls.new_sheet('test_open\n\nand some text', testgroup_id)
    calls.open(sheet_id)
    time.sleep(5)

    calls.open_all()
    time.sleep(5)

    calls.open_recent()
    time.sleep(5)

    calls.open_favorites()
    time.sleep(5)


class TestItemConstructors():

    def test_sheet(self):
        d = {
            'changeToken': '1|1E9A917F|unfpAQAAAAADAAAA',
            'creationDate': 513446267,
            'hasLifetimeIdentifier': True,
            'identifier': 'ENYa9PBxg3Vj7ws4MO_SWA',
            'modificationDate': 513446268.980628,
            'title': 'upcsheet',
            'titleType': None,
            'type': 'sheet'}
        sheet = calls.Sheet(**d)
        assert sheet.title == 'upcsheet'
        exp = "Sheet(title='upcsheet', identifier='ENYa9PBxg3Vj7ws4MO_SWA')"
        assert str(sheet) == exp


# Test read only item classes

    def test_group_with_no_containers(self):
        d = {
            'hasLifetimeIdentifier': True,
            'identifier': '4A14NiU-iGaw06m2Y2DNwA',
            'sheets': [],
            'title': 'iCloud',
            'type': 'group',
            'sheets': [{'changeToken': '1|1E9A917F|unfpAQAAAAADAAAA',
                        'creationDate': 513446267,
                        'hasLifetimeIdentifier': True,
                        'identifier': 'ENYa9PBxg3Vj7ws4MO_SWA',
                        'modificationDate': 513446268.980628,
                        'title': 'sheet',
                        'titleType': None,
                        'type': 'sheet'}]}
        group = calls.Group(**d)
        assert group.title == 'iCloud'
        assert group.sheets == [calls.Sheet(**d['sheets'][0])]
        assert group.containers is None
        expected = ("Group(title='iCloud', n_sheets=1, n_containers=?unknown?,"
                    " identifier='4A14NiU-iGaw06m2Y2DNwA')")
        assert str(group) == expected

    def test_group_with_containers(self):
        d = {
            'containers': [{
                'containers': [],
                'hasLifetimeIdentifier': True,
                'identifier': 'wjdPFC0ayV4PGjPEMofEgQ',
                'sheets': [{
                    'changeToken': '1|1E9A91A4|mnjpAQAAAAADAAAA',
                    'creationDate': 513446305,
                    'hasLifetimeIdentifier': True,
                    'identifier': 'tv6FBiPRaSBUZ1eJCdUZIA',
                    'modificationDate': 513446307.663547,
                    'title': 'sheet1a',
                    'titleType': None,
                    'type': 'sheet',
                    }, {
                    'changeToken': '1|1E9A91A8|AXnpAQAAAAADAAAA',
                    'creationDate': 513446309,
                    'hasLifetimeIdentifier': True,
                    'identifier': '5uN0A6hqjbO4QWHMV7tkkg',
                    'modificationDate': 513446311.753698,
                    'title': 'sheet1b',
                    'titleType': None,
                    'type': 'sheet',
                    }],
                'title': 'group1',
                'type': 'group',
                }, {
                'containers': [],
                'hasLifetimeIdentifier': True,
                'identifier': 'WrDEUsU7eoFxCDpizAwtNw',
                'sheets': [],
                'title': 'group2',
                'type': 'group',
                }],
            'hasLifetimeIdentifier': True,
            'identifier': 'S_8htbpgEo0KJiXDLXVtdg',
            'sheets': [{
                'changeToken': '1|1E9A9D95|JoTpAQAAAAADAAAA',
                'creationDate': 513446267,
                'hasLifetimeIdentifier': True,
                'identifier': 'ENYa9PBxg3Vj7ws4MO_SWA',
                'modificationDate': 513449353.343165,
                'title': 'upcsheet',
                'titleType': None,
                'type': 'sheet',
                }],
            'title': 'upcgroup',
            'type': 'group',
            }
        upcgroup = calls.Group(**d)
        upcsheet = calls.Sheet(**d['sheets'][0])
        group1 = calls.Group(**d['containers'][0])
        group2 = calls.Group(**d['containers'][1])
        sheet1a = calls.Sheet(**d['containers'][0]['sheets'][0])
        sheet1b = calls.Sheet(**d['containers'][0]['sheets'][1])

        assert upcgroup.title == 'upcgroup'
        assert upcgroup.sheets == [upcsheet]
        assert upcgroup.containers == [group1, group2]
        assert str(upcgroup) == (
            "Group(title='upcgroup', n_sheets=1, n_containers=2,"
            " identifier='S_8htbpgEo0KJiXDLXVtdg')")

        assert group1.title == 'group1'
        assert group1.sheets[0] == sheet1a
        assert group1.sheets[1] == sheet1b
        assert group1.containers == []
        assert str(group1) == (
            "Group(title='group1', n_sheets=2, n_containers=0, identifier="
            "'wjdPFC0ayV4PGjPEMofEgQ')")

        assert group2.title == 'group2'
        assert group2.sheets == []
        assert group2.containers == []
        assert str(group2) == (
            "Group(title='group2', n_sheets=0, n_containers=0, "
            "identifier='WrDEUsU7eoFxCDpizAwtNw')")

        assert upcgroup.get_group_by_title('group1') == group1
        assert upcgroup.get_sheet_by_title('upcsheet') == upcsheet


# http://stackoverflow.com/questions/2030053/random-strings-in-python
def randomword(length):
    return ''.join(random.choice(string.lowercase) for _ in range(length))
