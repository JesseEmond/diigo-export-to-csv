import csv
import dataclasses
import datetime
from getpass import getpass
import requests
from typing import Any
from urllib.parse import urljoin


BASE_URL = 'https://www.diigo.com/api/v2/'
API_KEY = 'TODO_YOUR_API_KEY_HERE'  # Get one on https://www.diigo.com/api_keys
EXPORT_FILENAME = 'diigo_export.csv'
CHUNK_SIZE = 1024
# E.g. 2024/11/14 05:48:28 +0000
DIIGO_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S %z'


@dataclasses.dataclass
class Creds:
    username: str
    password: str


@dataclasses.dataclass
class Bookmark:
    url: str
    title: str
    description: str
    tags: list[str]
    created_at: datetime.datetime
    read_later: bool
    private: bool
    annotations: dict[str, list[str]]


    RAINDROP_IO_FIELDNAMES = ['url', 'folder', 'title', 'note', 'tags', 'created']

    def to_raindrop_io_csv_row(self) -> dict[str, Any]:
        folder = 'Diigo Import'
        if self.read_later:
            folder += '/Read Later'
        if self.private:
            folder += '/Private'
        tags = ''
        if len(self.tags) == 1:
            tags = self.tags[0]
        elif len(self.tags) > 1:
            joined = ', '.join(self.tags)
            tags = f'"{joined}"'
        note = self.description
        if self.annotations:
            note += '\n\nAnnotations:'
            for annotation, comments in self.annotations.items():
                quoted = '>' + annotation.replace('\n\n', '\n> \n')
                for comment in comments:
                    note += f'\n {quoted}\n\n{comment}\n'
        return {
            'url': self.url,
            'folder': folder,
            'title': self.title,
            'note': note,
            'tags': tags,
            'created': self.created_at.isoformat(),
        }


class ApiException(Exception):
    def __init__(self, status_code: int, text: str) -> None:
        super().__init__(f'HTTP {status_code}: {text}')


def api_request(method_path: str, params: dict[str, Any], creds: Creds) -> Any:
    url = urljoin(BASE_URL, method_path)
    assert 'key' not in params
    params = {'key': API_KEY, **params}
    auth = requests.auth.HTTPBasicAuth(creds.username, creds.password)
    response = requests.get(url, params=params, auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        raise ApiException(response.status_code, response.text)


def get_bookmarks(creds: Creds, start: int, count: int) -> list[Bookmark]:
    params = {
        'user': creds.username,
        'start': start,
        'count': count,
        'filter': 'all',
    }
    response = api_request('bookmarks', params, creds)
    bookmarks = []
    for bookmark_obj in response:
        assert not bookmark_obj['comments'], bookmark_obj  # TODO: Support
        assert '"' not in bookmark_obj['tags'], bookmark_obj  # TODO: Remove, looking for potential weird tags
        assert bookmark_obj['shared'] in ['yes', 'no'], bookmark_obj
        assert bookmark_obj['readlater'] in ['yes', 'no'], bookmark_obj
        created_at = datetime.datetime.strptime(bookmark_obj['created_at'], DIIGO_DATETIME_FORMAT)
        read_later = bookmark_obj['readlater'] == 'yes'
        description = bookmark_obj['desc']
        title = bookmark_obj['title']
        tags = bookmark_obj['tags'].split(',')
        url = bookmark_obj['url']
        private = bookmark_obj['shared'] == 'no'
        annotations = {}
        for annotation_obj in bookmark_obj['annotations']:
            assert annotation_obj['content'] not in annotations, annotation_obj  # TODO: Support
            comments = [comment['content'] for comment in annotation_obj['comments']]
            annotations[annotation_obj['content']] = comments
        bookmarks.append(Bookmark(
            url=url,
            tags=tags,
            title=title,
            description=description,
            read_later=read_later,
            private=private,
            created_at=created_at,
            annotations=annotations))
    return bookmarks


def main() -> None:
    creds = Creds(username=input('username? '), password=getpass('password? '))

    bookmarks = []
    start = 0
    while True:
        print(f'Bookmarks [{start}, {start + CHUNK_SIZE})...')
        chunk_bookmarks = get_bookmarks(start=start, count=CHUNK_SIZE, creds=creds)
        if not chunk_bookmarks:
            break
        bookmarks.extend(chunk_bookmarks)
        start += CHUNK_SIZE

    print(f'Saving to {EXPORT_FILENAME}...')
    with open(EXPORT_FILENAME, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=Bookmark.RAINDROP_IO_FIELDNAMES)
        writer.writeheader()
        writer.writerows([bookmark.to_raindrop_io_csv_row() for bookmark in bookmarks])
    print('Done!')
    

if __name__ == '__main__':
    main()
