import json
import dataclasses
from dataclasses import dataclass
from urllib.request import urlopen
from bs4 import BeautifulSoup


@dataclass
class Card:
    title: str
    subtitle: str
    location: str
    posted: str
    apply_link: str

    def __post_init__(self):
        self._content: str | None = None

    def __iter__(self):
        return (
            getattr(self, field.name) for field in dataclasses.fields(self)
        )

    def as_line(self, include_content: bool = True):
        line = ','.join(self._clean(val) for val in self)
        if include_content:
            return line + ',' + self._clean(self.content)
        return line

    def as_dict(self, include_content: bool = True):
        d = {
            key: str(val).strip().replace('\n', '')
            for key, val in dataclasses.asdict(self).items()
        }

        if include_content:
            d.update({'content': self.content})

        return d

    @staticmethod
    def _clean(word: str):
        word = word.strip().replace('\n', '')
        return f'"{word}"' if ',' in word else word

    @property
    def content(self):
        if self._content:
            return self._content

        res = urlopen(self.apply_link)
        html = res.read()
        soup = BeautifulSoup(html, features='html.parser')
        self._content = soup.select_one('.content p').text
        return self._content


class FakePythonPage:
    def __init__(self) -> None:
        self.url = 'https://realpython.github.io/fake-jobs/'
        self.cards_container_selector = (
            '#ResultsContainer .column .card .card-content'
        )
        self.selectors = {
            'title': '.media-content .title',
            'subtitle': '.media-content .subtitle',
            'location': '.content .location',
            'posted': '.content p time',
            'apply_link': '.card-footer-item:last-child',
        }
        self._cards: list[Card] = []

    @property
    def cards(self) -> list[Card]:
        if self._cards:
            return self._cards

        res = urlopen(self.url)
        content = res.read()
        soup = BeautifulSoup(content, features='html.parser')
        raw_cards = soup.select(self.cards_container_selector)

        for raw_card in raw_cards:
            title = raw_card.select_one(self.selectors['title']).text
            subtitle = raw_card.select_one(self.selectors['subtitle']).text
            location = raw_card.select_one(self.selectors['location']).text
            posted = raw_card.select_one(self.selectors['posted']).text
            apply_link = raw_card.select_one(self.selectors['apply_link'])[
                'href'
            ]

            card = Card(title, subtitle, location, posted, apply_link)
            self._cards.append(card)

        return self._cards

    def to_csv(self, filename: str) -> None:
        with open(filename, 'wt', encoding='utf8') as file:
            file.write(','.join(self.selectors.keys()) + ',content\n')
            for card in self.cards:
                file.write(card.as_line() + '\n')

    def to_json(self, filename: str) -> None:
        with open(filename, 'wt', encoding='utf8') as file:
            data = json.dumps([card.as_dict() for card in self.cards])
            file.write(data)


if __name__ == '__main__':
    page = FakePythonPage()
    page.to_csv('demo.csv')
    page.to_json('demo.json')
