"""
Specific functions working on the games.
"""

import re
from difflib import SequenceMatcher
from utils import utils, osg_parse
from utils.constants import *

regex_sanitize_name = re.compile(r"[^A-Za-z 0-9-+]+")
regex_sanitize_name_space_eater = re.compile(r" +")


def name_similarity(a, b):
    return SequenceMatcher(None, str.casefold(a), str.casefold(b)).ratio()


def entry_iterator():
    """

    """

    # get all entries (ignore everything starting with underscore)
    entries = os.listdir(entries_path)

    # iterate over all entries
    for entry in entries:
        entry_path = os.path.join(entries_path, entry)

        # ignore directories ("tocs" for example)
        if os.path.isdir(entry_path):
            continue

        # read entry
        content = utils.read_text(entry_path)

        # yield
        yield entry, entry_path, content


def canonical_entry_name(name):
    """
    Derives a canonical game name from an actual game name (suitable for file names, ...)
    """
    name = name.casefold()
    name = name.replace('ö', 'o').replace('ä', 'a').replace('ü', 'u')
    name = regex_sanitize_name.sub('', name)
    name = regex_sanitize_name_space_eater.sub('_', name)
    name = name.replace('_-_', '-')
    name = name.replace('--', '-').replace('--', '-')

    return name


def read_developers():
    """

    :return:
    """
    grammar_file = os.path.join(code_path, 'grammar_listing.lark')
    developers = osg_parse.read_and_parse(developer_file, grammar_file, osg_parse.ListingTransformer)

    # now developers is a list of dictionaries for every entry with some properties

    # check for duplicate names entries
    names = [dev['Name'] for dev in developers]
    duplicate_names = (name for name in names if names.count(name) > 1)
    duplicate_names = set(duplicate_names)  # to avoid duplicates in duplicate_names
    if duplicate_names:
        print('Warning: duplicate developer names: {}'.format(', '.join(duplicate_names)))

    # check for essential, valid fields
    for dev in developers:
        # check that essential fields are existing
        for field in essential_developer_fields:
            if field not in dev:
                raise RuntimeError('Essential field "{}" missing in developer {}'.format(field, dev['Name']))
        # check that all fields are valid fields
        for field in dev.keys():
            if field not in valid_developer_fields:
                raise RuntimeError('Invalid field "{}" in developer {}.'.format(field, dev['Name']))
        # url fields
        for field in url_developer_fields:
            if field in dev:
                content = dev[field]
                if any(not (x.startswith('http://') or x.startswith('https://')) for x in content):
                    raise RuntimeError('Invalid URL in field "{}" in developer {}.'.format(field, dev['Name']))

    # convert to dictionary
    developers = {x['Name']: x for x in developers}

    return developers


def write_developers(developers):
    """

    :return:
    """
    # convert dictionary to list
    developers = list(developers.values())

    # comment
    content = '{}\n'.format(generic_comment_string)

    # number of developer
    content += '# Developer [{}]\n\n'.format(len(developers))

    # sort by name
    developers.sort(key=lambda x: str.casefold(x['Name']))

    # iterate over them
    for dev in developers:
        keys = list(dev.keys())
        # developer name
        content += '## {} [{}]\n\n'.format(dev['Name'], len(dev['Games']))
        keys.remove('Name')

        # all the remaining in alphabetical order, but 'games' first
        keys.remove('Games')
        keys.sort()
        keys = ['Games'] + keys
        for field in keys:
            value = dev[field]
            # lists get special treatment
            if isinstance(value, list):
                value.sort(key=str.casefold)
                value = [x if not ',' in x else '"{}"'.format(x) for x in value]  # surround those with a comma with quotation marks
                value = ', '.join(value)
            content += '- {}: {}\n'.format(field, value)
        content += '\n'

    # write
    utils.write_text(developer_file, content)


def read_inspirations():
    """
    Reads the info list about the games originals/inspirations from inspirations.md using the Lark parser grammar
    in grammar_listing.lark
    :return:
    """
    # read inspirations

    # read and parse inspirations
    grammar_file = os.path.join(code_path, 'grammar_listing.lark')
    inspirations = osg_parse.read_and_parse(inspirations_file, grammar_file, osg_parse.ListingTransformer)

    # now inspirations is a list of dictionaries for every entry with some properties

    # check for duplicate names entries
    names = [inspiration['Name'] for inspiration in inspirations]
    duplicate_names = (name for name in names if names.count(name) > 1)
    duplicate_names = set(duplicate_names)  # to avoid duplicates in duplicate_names
    if duplicate_names:
        raise RuntimeError('Duplicate inspiration names: {}'.format(', '.join(duplicate_names)))

    # check for essential, valid fields
    for inspiration in inspirations:
        # check that essential fields are existing
        for field in essential_inspiration_fields:
            if field not in inspiration:
                raise RuntimeError('Essential field "{}" missing in inspiration {}'.format(field, inspiration['Name']))
        # check that all fields are valid fields
        for field in inspiration.keys():
            if field not in valid_inspiration_fields:
                raise RuntimeError('Invalid field "{}" in inspiration {}.'.format(field, inspiration['Name']))
        # url fields
        for field in url_inspiration_fields:
            if field in inspiration:
                content = inspiration[field]
                if any(not (x.startswith('http://') or x.startswith('https://')) for x in content):
                    raise RuntimeError('Invalid URL in field "{}" in inspiration {}.'.format(field, inspiration['Name']))

    # convert to dictionary
    inspirations = {x['Name']: x for x in inspirations}

    return inspirations


def write_inspirations(inspirations):
    """
    Given an internal dictionary of inspirations, write it into the inspirations file
    :param inspirations:
    :return:
    """
    # convert dictionary to list
    inspirations = list(inspirations.values())

    # comment
    content = '{}\n'.format(generic_comment_string)

    # updated number of inspirations
    content += '# Inspirations [{}]\n\n'.format(len(inspirations))

    # sort by name
    inspirations.sort(key=lambda x: str.casefold(x['Name']))

    # iterate over them
    for inspiration in inspirations:
        keys = list(inspiration.keys())
        # inspiration name
        content += '## {} [{}]\n\n'.format(inspiration['Name'], len(inspiration['Inspired entries']))
        keys.remove('Name')

        # all the remaining in alphabetical order, but "inspired entries" first
        keys.remove('Inspired entries')
        keys.sort()
        keys = ['Inspired entries'] + keys
        for field in keys:
            value = inspiration[field]
            # lists get special treatment
            if isinstance(value, list):
                value.sort(key=str.casefold)  # sorted alphabetically
                value = [x if not ',' in x else '"{}"'.format(x) for x in value]  # surround those with a comma with quotation marks
                value = ', '.join(value)
            content += '- {}: {}\n'.format(field, value)
        content += '\n'

    # write
    utils.write_text(inspirations_file, content)


def read_entries():
    """
    Parses all entries and assembles interesting infos about them.
    """

    # setup parser and transformer
    grammar_file = os.path.join(code_path, 'grammar_entries.lark')
    grammar = utils.read_text(grammar_file)
    parse = osg_parse.create(grammar, osg_parse.EntryTransformer)

    # a database of all important infos about the entries
    entries = []

    # iterate over all entries
    exception_happened = False
    for file, _, content in entry_iterator():

        if not content.endswith('\n'):
            content += '\n'

        # parse and transform entry content
        try:
            entry = parse(content)
            entry = [('File', file),] + entry # add file information to the beginning
            entry = check_and_process_entry(entry)
        except Exception as e:
            print('{} - {}'.format(file, e))
            exception_happened = True
            # raise RuntimeError(e)
            continue

        # add to list
        entries.append(entry)
    if exception_happened:
        raise RuntimeError('errors while reading entries')

    return entries


def check_and_process_entry(entry):
    message = ''

    # check that all fields are valid fields and are existing in that order
    index = 0
    for e in entry:
        field = e[0]
        while index < len(valid_fields) and field != valid_fields[index]:
            index += 1
        if index == len(valid_fields):  # must be valid fields and must be in the right order
            message += 'Field "{}" either misspelled or in wrong order\n'.format(field)

    # order is fine we can convert to dictionary
    d = {}
    for field, value in entry:
        if field in d:
            message += 'Field "{}" appears twice\n'.format(field)
        d[field] = value
    entry = d

    # check for essential fields
    for field in essential_fields:
        if field not in entry:
            message += 'Essential property "{}" missing\n'.format(field)

    # now the same treatment for building
    building = entry['Building']
    d = {}
    for field, value in building:
        if field in d:
            message += 'Field "{}" appears twice\n'.format(field)
        d[field] = value
    building = d

    # check valid fields in building TODO should also check order
    for field in building.keys():
        if field not in valid_building_fields:
            message += 'Building field "{}" invalid\n'.format(field)
    entry['Building'] = building

    # check canonical file name
    file = entry['File']
    canonical_file_name = canonical_entry_name(entry['Title']) + '.md'
    # we also allow -X with X =2..9 as possible extension (because of duplicate canonical file names)
    if canonical_file_name != file and canonical_file_name != file[:-5] + '.md':
        message += 'file name should be {}\n'.format(canonical_file_name)

    # state must contain either beta or mature but not both
    state = entry['State']
    for t in state:
        if t != 'beta' and t != 'mature' and not t.startswith('inactive since '):
            message += 'Unknown state "{}"'.format(t)
    if 'beta' in state == 'mature' in state:
        message += 'State must be one of <"beta", "mature">'

    # check urls
    for field in url_fields:
        values = entry.get(field, [])
        for value in values:
            if value.value.startswith('<') and value.value.endswith('>'):
                value.value = value.value[1:-1]
            if not any(value.startswith(x) for x in extended_valid_url_prefixes):
                message += 'URL "{}" in field "{}" does not start with a valid prefix'.format(value, field)

    # github/gitlab repositories should end on .git and should start with https
    for repo in entry['Code repository']:
        if any(repo.startswith(x) for x in ('@', '?')):
            continue
        repo = repo.value.split(' ')[0].strip()
        if any((x in repo for x in ('github', 'gitlab', 'git.tuxfamily', 'git.savannah'))):
                if not repo.startswith('https://'):
                    message += 'Repo "{}" should start with https://'.format(repo)
                if not repo.endswith('.git'):
                    message += 'Repo "{}" should end on .git.'.format(repo)

    # check that all platform tags are valid tags and are existing in that order
    if 'Platform' in entry:
        index = 0
        for platform in entry['Platform']:
            while index < len(valid_platforms) and platform != valid_platforms[index]:
                index += 1
            if index == len(valid_platforms):  # must be valid platforms and must be in that order
                message += 'Platform tag "{}" either misspelled or in wrong order'.format(platform)

    # there must be at least one keyword
    if not entry['Keywords']:
        message += 'Need at least one keyword'

    # check for existence of at least one recommended keywords
    keywords = entry['Keywords']
    if not any(keyword in keywords for keyword in recommended_keywords):
        message += 'Entry contains no recommended keywords'

    # languages should be known
    languages = entry['Code language']
    for language in languages:
        if language not in known_languages:
            message += 'Language "{}" is not a known code language. Misspelled or new?'.format(language)

    # licenses should be known
    licenses = entry['Code license']
    for license in licenses:
        if license not in known_licenses:
            message += 'License "{}" is not a known license. Misspelled or new?'.format(license)

    if message:
        raise RuntimeError(message)

    return entry

def is_inactive(entry):
    state = entry['State']
    phrase = 'inactive since '
    return any(x.startswith(phrase) for x in state)


def extract_inactive_year(entry):
    state = entry['State']
    phrase = 'inactive since '
    inactive_year = [x.value[len(phrase):] for x in state if x.startswith(phrase)]
    assert len(inactive_year) <= 1
    if inactive_year:
        return inactive_year[0]
    else:
        return None

def write_entries(entries):
    """

    :return:
    """

    # iterate over all entries
    for entry in entries:
        write_entry(entry)


def write_entry(entry):
    """

    :param entry:
    :return:
    """
    # TODO check entry

    # get path
    entry_path = os.path.join(entries_path, entry['File'])

    # create output content
    content = create_entry_content(entry)

    # write entry
    utils.write_text(entry_path, content)


def create_entry_content(entry):
    """

    :param entry:
    :return:
    """

    # title
    content = '# {}\n\n'.format(entry['Title'])

    # we automatically sort some fields
    sort_fun = lambda x: str.casefold(x.value)
    for field in ('Media', 'Inspirations', 'Code Language'):
        if field in entry:
            values = entry[field]
            entry[field] = sorted(values, key=sort_fun)
    # we also sort keywords, but first the recommend ones and then other ones
    keywords = entry['Keywords']
    a = [x for x in keywords if x in recommended_keywords]
    b = [x for x in keywords if x not in recommended_keywords]
    entry['Keywords'] = sorted(a, key=sort_fun) + sorted(b, key=sort_fun)

    # now properties in the recommended order
    for field in valid_properties:
        if field in entry:
            c = entry[field]
            c = ['"{}"'.format(x) if ',' in x else x for x in c]
            c = [str(x) for x in c]
            content += '- {}: {}\n'.format(field, ', '.join(c))
    content += '\n'

    # if there is a note, insert it
    if 'Note' in entry:
        content += entry['Note']

    # building header
    content += '## Building\n'

    # building properties if present
    has_properties = False
    for field in valid_building_properties:
        if field in entry['Building']:
            if not has_properties:
                has_properties = True
                content += '\n'
            c = entry['Building'][field]
            c = ['"{}"'.format(x) if ',' in x else x for x in c]
            c = [str(x) for x in c]
            content += '- {}: {}\n'.format(field, ', '.join(c))

    # if there is a note, insert it
    if 'Note' in entry['Building']:
        content += '\n'
        content += entry['Building']['Note']

    return content


def is_url(str):
    """
    Could be too generous. See https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not for other possibilities.
    :param str:
    :return:
    """
    if any(str.startswith(x) for x in valid_url_prefixes) and not ' ' in str:
        return True
    return False


def all_urls(entries):
    """
    Gets all urls of all entries in a dictionary (key=url value=list of entries (file name) with this url
    :param entries: 
    :return: 
    """
    urls = {}
    # iterate over entries
    for entry in entries:
        file = entry['File']
        for field in url_fields:  # TODO there are other fields, maybe just regex on the whole content
            for value in entry.get(field, []):
                if value.comment:
                    value = value.value + ' ' + value.comment
                else:
                    value = value.value
                for subvalue in value.split(' '):
                    subvalue = subvalue.strip()
                    if is_url(subvalue):
                        urls[subvalue] = urls.get(subvalue, []) + [file]
    return urls